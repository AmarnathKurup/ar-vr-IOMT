import sys
from pathlib import Path
import requests
import time

# Add simulator folder path
sys.path.append(str(Path(__file__).resolve().parent.parent / "simulator"))

from HRgen import generate_max30100_data

POST_URL = "http://127.0.0.1:5000/api/v1/temp"
GET_URL = "http://127.0.0.1:5000/api/v1/temp/latest"

while True:

    temp_data = generate_max30100_data("1")

    payload = {
        "temperature":
            temp_data["telemetry"]["temperature"]["value"],

        "temp_condition":
            temp_data["condition"]["temp_status"]["label"]
    }

    # POST
    post_res = requests.post(POST_URL, json=payload)

    print("POST:", post_res.text)

    # GET
    get_res = requests.get(GET_URL)

    print("GET:", get_res.text)

    time.sleep(1)