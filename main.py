from fastapi import FastAPI

from analyzer import analyze_system

from api_client import get_sensor_data

from config import (
    PORTA_URL,
    TEMPERATURA_URL,
    ENERGIA_URL
)

app = FastAPI()


@app.get("/")
def home():

    return {
        "project": "ColdGuardian AI",
        "status": "running"
    }


@app.get("/analyze")
def analyze():

    try:

        porta = get_sensor_data(
            PORTA_URL
        )

        temperatura = get_sensor_data(
            TEMPERATURA_URL
        )

        energia = get_sensor_data(
            ENERGIA_URL
        )

        result = analyze_system(
            porta,
            temperatura,
            energia
        )

        return result

    except Exception as e:

        return {
            "error": str(e)
        }