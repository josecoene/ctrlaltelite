from dotenv import load_dotenv
import os

load_dotenv()

PORTA_URL = os.getenv("PORTA_URL")

TEMPERATURA_URL = os.getenv(
    "TEMPERATURA_URL"
)

ENERGIA_URL = os.getenv(
    "ENERGIA_URL"
)

API_KEY = os.getenv("API_KEY")