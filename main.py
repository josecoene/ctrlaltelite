from fastapi import FastAPI

from data_loader import load_json
from analyzer import analyze_system
from diagnostics import generate_diagnostic

app = FastAPI()

@app.get("/")
def home():
    return {
        "project": "ColdGuardian AI",
        "status": "running"
    }

@app.get("/analyze")
def analyze():

    porta = load_json("data/porta.json")
    motor1 = load_json("data/motor1.json")
    motor2 = load_json("data/motor2.json")
    temperatura = load_json("data/temperatura.json")

    result = analyze_system(
        porta,
        motor1,
        motor2,
        temperatura
    )

    diagnostic = generate_diagnostic(result)

    return {
        "analysis": result,
        "diagnostic": diagnostic
    }