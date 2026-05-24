from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")

PORTA_URL = os.getenv(
    "PORTA_URL"
)

TEMPERATURA_URL = os.getenv(
    "TEMPERATURA_URL"
)

MOTOR2_URL = os.getenv(
    "MOTOR2_URL"
)

print("API_KEY:", API_KEY)