import numpy as np

def analyze_system(
    porta_data,
    motor1_data,
    motor2_data,
    temperatura_data
):

    score = 0
    problemas = []

    # =========================
    # TEMPERATURA
    # =========================

    temperaturas = [
        p["temperatura"]
        for p in temperatura_data["points"]
    ]

    temp_media = np.mean(temperaturas)
    temp_max = np.max(temperaturas)

    # =========================
    # PORTA
    # =========================

    aberturas = [
        p["abertura_porta"]
        for p in porta_data["points"]
    ]

    variacao_porta = max(aberturas) - min(aberturas)

    # =========================
    # MOTORES
    # =========================

    motor1 = [
        p["temperatura"]
        for p in motor1_data["points"]
    ]

    motor2 = [
        p["temperatura"]
        for p in motor2_data["points"]
    ]

    motor1_media = np.mean(motor1)
    motor2_media = np.mean(motor2)

    # =========================
    # REGRAS DE ANOMALIA
    # =========================

    # Temperatura muito alta
    if temp_media > -4:
        score += 30
        problemas.append(
            "Temperatura acima do ideal"
        )

    # Oscilação térmica
    if temp_max > -5:
        score += 20
        problemas.append(
            "Oscilação térmica detectada"
        )

    # Muitas aberturas
    if variacao_porta > 3:
        score += 15
        problemas.append(
            "Alta frequência de abertura da porta"
        )

    # Temperatura subindo sem abertura
    if temp_max > -5 and variacao_porta <= 1:
        score += 35
        problemas.append(
            "Aumento térmico sem abertura relevante"
        )

    # Motores trabalhando demais
    if motor1_media > -5.5 and motor2_media > -5.5:
        score += 25
        problemas.append(
            "Compressores operando acima do padrão"
        )

    # =========================
    # CLASSIFICAÇÃO
    # =========================

    if score <= 30:
        status = "NORMAL"

    elif score <= 70:
        status = "ATENCAO"

    else:
        status = "CRITICO"

    return {
        "score": score,
        "status": status,
        "temperatura_media": round(temp_media, 2),
        "temperatura_max": round(temp_max, 2),
        "variacao_porta": variacao_porta,
        "problemas": problemas
    }