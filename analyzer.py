import numpy as np
from detector import detect_door_state


def calculate_power(point):
    return (
        point["tensao_fase_a"] * point["corrente_fase_a"] * point["fator_potencia_a"]
        + point["tensao_fase_b"] * point["corrente_fase_b"] * point["fator_potencia_b"]
        + point["tensao_fase_c"] * point["corrente_fase_c"] * point["fator_potencia_c"]
    )


def simple_autoencoder_error(data, window=5):
    """
    Autoencoder ultra leve (proxy):
    usa média móvel como reconstrução
    """
    errors = []

    for i in range(len(data)):
        start = max(0, i - window)
        window_data = data[start:i+1]

        recon = np.mean(window_data)
        error = abs(data[i] - recon)

        errors.append(error)

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

    # 🤖 autoencoder simples
    recon_errors = simple_autoencoder_error(energia_total)
    threshold = np.mean(recon_errors) + 2 * np.std(recon_errors)

    score = 0
    problemas = []
    porta_aberta_count = 0
    anomaly_count = 0

    for i in range(min_size):

        if door_states[i]["door_state"] == "ABERTA":
            porta_aberta_count += 1

        if recon_errors[i] > threshold:
            anomaly_count += 1

        if temperaturas[i] > temp_media + 1:
            score += 5

        if energia_total[i] > energia_media * 1.2:
            score += 5

        if recon_errors[i] > threshold:
            score += 10
            problemas.append("Anomalia energética detectada")

    anomaly_ratio = anomaly_count / max(1, min_size)

    if anomaly_ratio < 0.2:
        status = "NORMAL"
        diagnostic = "Sistema estável."
    elif anomaly_ratio < 0.5:
        status = "ATENCAO"
        diagnostic = "Variações moderadas detectadas."
    else:
        status = "CRITICO"
        diagnostic = "Anomalias consistentes no sistema."

    return {
        "score": score,
        "status": status,
        "anomalias_detectadas": anomaly_count,
        "anomalia_ratio": anomaly_ratio,

        "temperatura_media": round(temp_media, 2),
        "energia_media_total": round(energia_media, 2),
        "porta_aberta_count": porta_aberta_count,
        "total_amostras": min_size,

        "diagnostic": diagnostic,

        # 👇 necessário pro gráfico
        "debug": {
            "temperaturas": temperaturas,
            "energia": energia_total,
            "recon_errors": recon_errors,
            "threshold": threshold
        }
    }