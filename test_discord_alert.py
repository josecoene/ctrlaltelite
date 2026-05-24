# test_discord_alert.py

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from discord_notifier import send_discord_alert


if __name__ == "__main__":

    # resultado falso que simula um cenário crítico real
    result = {
        "status": "CRITICO",
        "score": 427,
        "diagnostic": "Anomalias consistentes no sistema.",
        "temperatura_media": -1.8,
        "energia_media_total": 83652,
        "porta_aberta_count": 19,
        "anomalias_detectadas": 51,
        "anomalia_ratio": 0.51,
        "total_amostras": 100,
        "autoencoder_backend": "moving_average",
    }

    print("enviando alerta de teste no Discord...")

    try:
        send_discord_alert(result)
        print("✅ alerta enviado com sucesso.")
    except Exception as e:
        print(f"❌ erro ao enviar alerta: {e}")
        sys.exit(1)