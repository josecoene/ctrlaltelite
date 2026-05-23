import requests


def get_sensor_data(url):

    response = requests.get(url)

    response.raise_for_status()

    return response.json()