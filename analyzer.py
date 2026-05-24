import numpy as np

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from detector import detect_door_state


def calculate_power(point):
    return (
        point["tensao_fase_a"] * point["corrente_fase_a"] * abs(point["fator_potencia_a"])
        + point["tensao_fase_b"] * point["corrente_fase_b"] * abs(point["fator_potencia_b"])
        + point["tensao_fase_c"] * point["corrente_fase_c"] * abs(point["fator_potencia_c"])
    )


class _TinyAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(1, 4),
            nn.Tanh(),
            nn.Linear(4, 2),
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, 4),
            nn.Tanh(),
            nn.Linear(4, 1),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


def _train_autoencoder(data: list[float], epochs: int = 80, lr: float = 1e-2):
    arr = np.array(data, dtype=np.float32)
    mean, std = arr.mean(), arr.std() + 1e-8
    norm = (arr - mean) / std

    x = torch.tensor(norm).unsqueeze(1)

    model = _TinyAutoencoder()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        out = model(x)
        loss = loss_fn(out, x)
        loss.backward()
        optimizer.step()

    return model, mean, std


def autoencoder_reconstruction_errors(data: list[float]) -> list[float]:
    if TORCH_AVAILABLE and len(data) >= 10:
        model, mean, std = _train_autoencoder(data)
        arr = np.array(data, dtype=np.float32)
        norm = (arr - mean) / std
        x = torch.tensor(norm).unsqueeze(1)
        model.eval()
        with torch.no_grad():
            recon = model(x).squeeze(1).numpy()
        recon_original = recon * std + mean
        return [abs(data[i] - float(recon_original[i])) for i in range(len(data))]
    else:
        return _moving_average_errors(data)


def _moving_average_errors(data: list[float], window: int = 5) -> list[float]:
    errors = []
    for i in range(len(data)):
        start = max(0, i - window)
        recon = np.mean(data[start:i + 1])
        errors.append(abs(data[i] - recon))
    return errors


def analyze_system(porta_data, temperatura_data, motor2_data):

    if not porta_data["points"]:
        return {"error": "Sem dados da porta"}
    if not temperatura_data["points"]:
        return {"error": "Sem dados de temperatura"}
    if not motor2_data["points"]:
        return {"error": "Sem dados do motor 2"}

    door_states = detect_door_state(porta_data["points"])

    temperaturas = [p["temperatura"] for p in temperatura_data["points"]]
    energia = [calculate_power(p) for p in motor2_data["points"]]

    min_size = min(len(door_states), len(temperaturas), len(energia))

    energia_total = energia[:min_size]
    temperaturas = temperaturas[:min_size]
    door_states = door_states[:min_size]

    temp_media = np.mean(temperaturas)
    energia_media = np.mean(energia_total)

    recon_errors = autoencoder_reconstruction_errors(energia_total)
    threshold = np.mean(recon_errors) + 2 * np.std(recon_errors)

    # --- Autoencoder ---
    recon_errors = autoencoder_reconstruction_errors(energia_total)
    threshold = np.mean(recon_errors) + 2 * np.std(recon_errors)

    # --- Confiabilidade ---
    confianca = calculate_confidence(energia_total, recon_errors, threshold)

    # --- Pontuação e detecção de problemas ---
    score = 0
    problemas = []
    porta_aberta_count = 0
    anomaly_count = 0

    for i in range(min_size):

        state = door_states[i]["door_state"]

        if state == "ABERTA":
            porta_aberta_count += 1
            score += 3
            problemas.append(f"Porta aberta em {door_states[i]['time']}")

        if recon_errors[i] > threshold:
            anomaly_count += 1
            score += 10
            problemas.append("Anomalia energética detectada")

        if temperaturas[i] > temp_media + 1:
            score += 5

        if energia_total[i] > energia_media * 1.2:
            score += 5

    anomaly_ratio = anomaly_count / max(1, min_size)

    def calculate_confidence(
        data: list[float],
        recon_errors: list[float],
        threshold: float,
        min_points: int = 10,
    ) -> dict:
        """
        Calcula a confiabilidade do processo de detecção em quatro dimensões:

        1. volume      — pontos suficientes para o autoencoder generalizar
        2. estabilidade — quão estável é a série (coef. de variação)
        3. separabilidade — o threshold consegue separar normal de anômalo com clareza
        4. cobertura   — proporção de pontos bem reconstruídos (abaixo do threshold)

        Retorna um score de 0 a 100 e um label: ALTA, MEDIA ou BAIXA.
        """

        n = len(data)
        arr = np.array(data, dtype=np.float32)
        errors = np.array(recon_errors, dtype=np.float32)

        # 1. volume: menos de 10 pontos é insuficiente, 50+ é ideal
        if n < min_points:
            volume_score = 0.0
        else:
            volume_score = min(1.0, (n - min_points) / (50 - min_points))

        # 2. estabilidade: coeficiente de variação da série original
        # série muito volátil = autoencoder menos confiável
        mean = arr.mean()
        std = arr.std()
        cv = std / (abs(mean) + 1e-8)
        estabilidade_score = max(0.0, 1.0 - cv)

        # 3. separabilidade: distância entre a média dos erros normais
        # e a média dos erros anômalos, normalizada pelo threshold
        # quanto maior a separação, mais claro é o sinal
        normal_errors = errors[errors <= threshold]
        anomaly_errors = errors[errors > threshold]

        if len(normal_errors) == 0 or len(anomaly_errors) == 0:
            separabilidade_score = 0.5  # não dá para medir separação sem os dois grupos
        else:
            gap = anomaly_errors.mean() - normal_errors.mean()
            separabilidade_score = min(1.0, gap / (threshold + 1e-8))

        # 4. cobertura: proporção de pontos bem reconstruídos
        cobertura_score = (errors <= threshold).sum() / n

        # score final ponderado
        confidence = (
            volume_score        * 0.20 +
            estabilidade_score  * 0.30 +
            separabilidade_score * 0.30 +
            cobertura_score     * 0.20
        ) * 100

        confidence = round(float(confidence), 1)

        if confidence >= 70:
            label = "ALTA"
        elif confidence >= 40:
            label = "MEDIA"
        else:
            label = "BAIXA"

        return {
            "score": confidence,
            "label": label,
            "detalhes": {
                "volume":          round(volume_score * 100, 1),
                "estabilidade":    round(estabilidade_score * 100, 1),
                "separabilidade":  round(separabilidade_score * 100, 1),
                "cobertura":       round(cobertura_score * 100, 1),
            }
        }

    # status unificado com o score — anomaly_ratio vira métrica auxiliar
    if score < 100:
        status = "NORMAL"
        diagnostic = "Sistema estável."
    elif score < 300:
        status = "ATENCAO"
        diagnostic = "Variações moderadas detectadas."
    else:
        status = "CRITICO"
        diagnostic = "Anomalias consistentes no sistema."

    return {
        "score": score,
        "status": status,
        "confianca": confianca,
        "anomalias_detectadas": anomaly_count,
        "anomalia_ratio": round(anomaly_ratio, 4),

        "temperatura_media": round(temp_media, 2),
        "energia_media_total": round(energia_media, 2),
        "porta_aberta_count": porta_aberta_count,
        "total_amostras": min_size,

        "diagnostic": diagnostic,
        "autoencoder_backend": "pytorch" if TORCH_AVAILABLE else "moving_average",

        "debug": {
            "temperaturas": temperaturas,
            "energia": energia_total,
            "recon_errors": recon_errors,
            "threshold": threshold,
        },
    }