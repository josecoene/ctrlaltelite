def detect_door_state(
    points,
    open_threshold=150,   # dados reais: fechada ~119, aberta ~222 → margem segura
    standby_threshold=10,
):
    """
    Três patamares observados nos dados reais:
      - 0             → STANDBY  (sensor desligado / estabelecimento fechado)
      - 118–121       → FECHADA  (voltagem média, sensor ativo, porta fechada)
      - 221–224       → ABERTA   (voltagem alta, porta fisicamente aberta)

    open_threshold=150 fica no meio-termo entre os dois patamares ativos,
    eliminando risco de falso positivo por oscilação de ±2 V.
    standby_threshold=10 cobre o zero com margem para ruído de hardware.
    """

    result = []

    for p in points:

        voltage = p["abertura_porta"]

        if voltage >= open_threshold:
            state = "ABERTA"
        elif voltage > standby_threshold:
            state = "FECHADA"
        else:
            state = "STANDBY"

        result.append({
            "time": p["time"],
            "voltage": voltage,
            "door_state": state,
        })

    return result