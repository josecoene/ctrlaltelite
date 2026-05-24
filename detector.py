def detect_door_state(
    points,
    threshold=119
):

    result = []

    for p in points:

        voltage = p["abertura_porta"]

        state = "FECHADA"

        if voltage < threshold:

            state = "ABERTA"

        result.append({

            "time": p["time"],

            "voltage": voltage,

            "door_state": state
        })

    return result