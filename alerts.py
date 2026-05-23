import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def send_discord_alert(status, risks, metrics=None, chamber_temp=None):
    """
    Sends a rich discord embed alert to the configured webhook URL.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url or "SUA_URL_AQUI" in webhook_url or "sua_url_aqui" in webhook_url:
        print("[Alerts] Discord webhook not configured. Alert logged to console:")
        for r in risks:
            print(f"  - [{status}] {r}")
        return False

    # Choose color based on status (decimal color values)
    # Red: 15158332, Yellow: 15176256, Green: 3066993
    color = 3066993
    if status == "CRITICAL":
        color = 15158332
    elif status == "WARNING":
        color = 15176256

    # Create fields from metrics
    fields = []
    if metrics:
        if "current_imbalance" in metrics:
            fields.append({
                "name": "⚡ Desequilíbrio de Corrente",
                "value": f"{metrics['current_imbalance']}%",
                "inline": True
            })
        if "avg_pf" in metrics:
            fields.append({
                "name": "🔌 Fator de Potência Médio",
                "value": f"{metrics['avg_pf']:.3f}",
                "inline": True
            })
        if "compressor_temp" in metrics and metrics["compressor_temp"] is not None:
            fields.append({
                "name": "🌡️ Temp. Compressor",
                "value": f"{metrics['compressor_temp']}°C",
                "inline": True
            })

    if chamber_temp is not None:
        fields.append({
            "name": "❄️ Temp. Câmara Fria",
            "value": f"{chamber_temp}°C (Alvo: <-18°C)",
            "inline": True
        })

    # Join risk descriptions into a single string
    description = "\n".join([f"⚠️ {r}" for r in risks]) if risks else "Todos os parâmetros operando dentro da normalidade."

    payload = {
        "username": "FrostGuard AI",
        "avatar_url": "https://img.icons8.com/color/344/snowflake.png",
        "embeds": [
            {
                "title": f"🚨 FrostGuard AI - Estado: {status}",
                "description": description,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": "Dale Sorvetes - Manutenção Preditiva",
                    "icon_url": "https://img.icons8.com/color/344/ice-cream-cone.png"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 240 or response.status_code in [200, 204]:
            print(f"[Alerts] Discord webhook notification sent successfully (Status: {status}).")
            return True
        else:
            print(f"[Alerts] Failed to send webhook, HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[Alerts] Exception when sending webhook: {e}")
        return False

# Quick test if run directly
if __name__ == "__main__":
    print("Testing alerts...")
    test_metrics = {
        "current_imbalance": 13.5,
        "avg_pf": 0.88,
        "compressor_temp": 82.0
    }
    test_risks = [
        "ALERTA: Alto desequilíbrio de corrente (13.5%). Risco de queima do motor!",
        "AVISO: Fator de potência baixo (0.880). Risco de multa por energia reativa."
    ]
    send_discord_alert("CRITICAL", test_risks, test_metrics, chamber_temp=-9.2)
