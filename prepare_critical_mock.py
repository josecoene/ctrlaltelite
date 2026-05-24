# prepare_critical_mock.py

import json
import copy

with open("data/mock-motor.json") as f:
    motor = json.load(f)

total = len(motor["points"])
split = total // 2

for i in range(split, total):
    p = motor["points"][i]
    p["corrente_fase_a"] = 200
    p["corrente_fase_b"] = 200
    p["corrente_fase_c"] = 200
    p["fator_potencia_a"] = -0.99
    p["fator_potencia_b"] = -0.99
    p["fator_potencia_c"] = -0.99

with open("data/mock-motor-critical.json", "w") as f:
    json.dump(motor, f, indent=2)

print(f"mock crítico gerado: {split} pontos normais + {total - split} pontos anômalos")