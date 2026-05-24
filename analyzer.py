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