import sys
from pathlib import Path
import requests
import time

# Add simulator folder path
sys.path.append(str(Path(__file__).resolve().parent.parent / "simulator"))

from HRgen import generate_max30100_data

POST_URL = "http://127.0.0.1:5000/api/v1/max30100"
GET_URL = "http://127.0.0.1:5000/api/v1/max30100/latest"

while True:

    max30100 = generate_max30100_data("2")

    sensor_data = {
    "heart_rate": max30100["telemetry"]["heart_rate"]["value"],

    "spo2": max30100["telemetry"]["spo2"]["value"],

    "heart_condition":
        max30100["condition"]["Heart_status"]["label"],

    "spo2_condition":
        max30100["condition"]["spo2_status"]["label"]
}

    # POST
    post_res = requests.post(POST_URL, json=sensor_data)

    print("POST:", post_res.text)

    # GET
    get_res = requests.get(GET_URL)

    print("GET:", get_res.text)

    time.sleep(1)