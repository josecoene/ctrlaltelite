# debug_threshold.py

import json
import os
import numpy as np

import analyzer
analyzer.TORCH_AVAILABLE = False

from analyzer import _moving_average_errors, calculate_power

with open("data/mock-motor-critical.json") as f:
    motor = json.load(f)

energia = [calculate_power(p) for p in motor["points"]]
errors = _moving_average_errors(energia)
threshold = np.mean(errors) + 2 * np.std(errors)

acima = sum(1 for e in errors if e > threshold)

print(f"total pontos:     {len(energia)}")
print(f"energia min:      {min(energia):.0f} W")
print(f"energia max:      {max(energia):.0f} W")
print(f"erro min:         {min(errors):.2f}")
print(f"erro max:         {max(errors):.2f}")
print(f"threshold:        {threshold:.2f}")
print(f"pontos acima:     {acima} / {len(errors)}")
print(f"anomaly_ratio:    {acima / len(errors):.1%}")