from fastapi import FastAPI, Response
from api_client import get_sensor_data
from analyzer import analyze_system
from visualizer import generate_system_plot
from discord_notifier import send_discord_alert
from config import PORTA_URL, TEMPERATURA_URL, MOTOR2_URL

app = FastAPI()


@app.get("/")
def home():
    return {
        "project": "ColdGuardian AI",
        "status": "running"
    }


@app.get("/analyze")
def analyze():

    porta = get_sensor_data(PORTA_URL)
    temperatura = get_sensor_data(TEMPERATURA_URL)
    motor2 = get_sensor_data(MOTOR2_URL)

    result = analyze_system(porta, temperatura, motor2)

    if result.get("status") in ("CRITICO", "ATENCAO"):
        try:
            send_discord_alert(result)
        except Exception as e:
            result["discord_alert_error"] = str(e)

    return result


@app.get("/chart")
def chart():

    porta = get_sensor_data(PORTA_URL)
    temperatura = get_sensor_data(TEMPERATURA_URL)
    motor2 = get_sensor_data(MOTOR2_URL)

    result = analyze_system(porta, temperatura, motor2)

    debug = result["debug"]

    image = generate_system_plot(
        debug["temperaturas"],
        debug["energia"],
        debug["recon_errors"],
        debug["threshold"]
    )

    return Response(content=image.getvalue(), media_type="image/png")