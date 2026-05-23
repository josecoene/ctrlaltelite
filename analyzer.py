import numpy as np

from detector import detect_door_state


def analyze_system(
    porta_data,
    temperatura_data,
    energia_data
):

    # =========================
    # PORTA
    # =========================

    door_states = detect_door_state(
        porta_data["points"]
    )

    # =========================
    # TEMPERATURA
    # =========================

    temperaturas = [
        p["temperatura"]
        for p in temperatura_data["points"]
    ]

    # =========================
    # ENERGIA
    # =========================

    energias = [
        p["energia"]
        for p in energia_data["points"]
    ]

    # =========================
    # BASELINE
    # =========================

    temp_media = np.mean(temperaturas)

    energia_media = np.mean(energias)

    # =========================
    # SCORE
    # =========================

    score = 0

    problemas = []

    porta_aberta_count = 0

    anomalia_porta_aberta = False

    anomalia_porta_fechada = False

    # =========================
    # ANÁLISE TEMPORAL
    # =========================

    for i in range(len(door_states)):

        estado_porta = door_states[i][
            "door_state"
        ]

        temperatura = temperaturas[i]

        energia = energias[i]

        # =====================
        # PORTA ABERTA
        # =====================

        if estado_porta == "ABERTA":

            porta_aberta_count += 1

            # Temperatura anormal
            if temperatura > temp_media + 1:

                score += 10

                anomalia_porta_aberta = True

            # Energia anormal
            if energia > energia_media * 1.2:

                score += 10

                anomalia_porta_aberta = True

        # =====================
        # PORTA FECHADA
        # =====================

        else:

            # Temperatura alta
            if temperatura > temp_media + 1:

                score += 25

                anomalia_porta_fechada = True

            # Energia alta
            if energia > energia_media * 1.3:

                score += 25

                anomalia_porta_fechada = True

    # =========================
    # REGRAS GERAIS
    # =========================

    if porta_aberta_count > 5:

        score += 20

        problemas.append(
            "Alta frequência de abertura"
        )

    if anomalia_porta_aberta:

        problemas.append(
            "Consumo elevado durante abertura"
        )

    if anomalia_porta_fechada:

        problemas.append(
            "Anomalia com porta fechada"
        )

    # =========================
    # STATUS
    # =========================

    if score <= 30:

        status = "NORMAL"

    elif score <= 70:

        status = "ATENCAO"

    else:

        status = "CRITICO"

    # =========================
    # DIAGNÓSTICO
    # =========================

    diagnostic = (
        "Sistema operando normalmente."
    )

    if status == "ATENCAO":

        diagnostic = (
            "Pequenas anomalias operacionais "
            "detectadas."
        )

    if status == "CRITICO":

        diagnostic = (
            "Possível perda de eficiência "
            "térmica detectada."
        )

    return {

        "score": score,

        "status": status,

        "temperatura_media": round(
            temp_media,
            2
        ),

        "energia_media": round(
            energia_media,
            2
        ),

        "porta_aberta_count":
            porta_aberta_count,

        "problemas": problemas,

        "diagnostic": diagnostic,

        "door_states": door_states
    }