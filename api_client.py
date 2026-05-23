import requests
from config import API_KEY


def get_sensor_data(url):

    headers = {
        "X-API-Key": API_KEY
    }

    response = requests.get(
        url,
        headers=headers
    )

    response.raise_for_status()

    return response.json()