import requests
from config import DISCORD_WEBHOOK_URL


def send_discord_alert(analysis: dict):
    """
    Envia alerta no Discord via webhook quando o sistema está em estado crítico.
    Monta uma embed com as informações mais relevantes da análise.
    """

    status = analysis.get("status", "DESCONHECIDO")
    diagnostic = analysis.get("diagnostic", "")
    score = analysis.get("score", 0)
    temp_media = analysis.get("temperatura_media", 0)
    energia_media = analysis.get("energia_media_total", 0)
    anomalias = analysis.get("anomalias_detectadas", 0)
    anomalia_ratio = analysis.get("anomalia_ratio", 0)
    porta_aberta = analysis.get("porta_aberta_count", 0)
    total_amostras = analysis.get("total_amostras", 0)
    backend = analysis.get("autoencoder_backend", "desconhecido")

    if status == "CRITICO":
        color = 0xFF0000   # vermelho
        titulo = "🚨 ALERTA CRÍTICO — ColdGuardian AI"
    elif status == "ATENCAO":
        color = 0xFFA500   # laranja
        titulo = "⚠️ Atenção — ColdGuardian AI"
    else:
        return   # NORMAL não envia alerta

    campos = [
        {
            "name": "📊 Diagnóstico",
            "value": diagnostic,
            "inline": False,
        },
        {
            "name": "🌡️ Temperatura média",
            "value": f"{temp_media} °C",
            "inline": True,
        },
        {
            "name": "⚡ Energia média",
            "value": f"{energia_media:.0f} W",
            "inline": True,
        },
        {
            "name": "🚪 Abertura de porta",
            "value": f"{porta_aberta} ocorrência(s)",
            "inline": True,
        },
        {
            "name": "🤖 Anomalias detectadas",
            "value": f"{anomalias} de {total_amostras} amostras ({anomalia_ratio:.1%})",
            "inline": True,
        },
        {
            "name": "🔬 Score de risco",
            "value": str(score),
            "inline": True,
        },
        {
            "name": "🧠 Modelo",
            "value": backend,
            "inline": True,
        },
    ]

    payload = {
        "embeds": [
            {
                "title": titulo,
                "color": color,
                "fields": campos,
                "footer": {
                    "text": "ColdGuardian AI · Sistema de monitoramento de câmara fria"
                },
            }
        ]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()