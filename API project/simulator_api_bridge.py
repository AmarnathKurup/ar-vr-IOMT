import sys
from pathlib import Path
import requests
import time

# Add simulator path
sys.path.append(str(Path(__file__).resolve().parent.parent / "simulator"))

from HRgen import generate_max30100_data

# APIs
SENSOR_API = "http://127.0.0.1:5000/api/v1/max30100"

TEMP_API = "http://127.0.0.1:5000/api/v1/temp"

COMBINED_API = "http://127.0.0.1:5000/api/v1/combined"

print("Starting realtime simulator...\n")

while True:

    try:

        # Combined payload
        combined = generate_max30100_data("3")

        # ======================
        # TEMP
        # ======================
        temp_payload = {
            "temperature":
                combined["temperature"]["telemetry"]["temperature"]["value"],

            "temp_condition":
                combined["temperature"]["condition"]["temperature"]
        }

        temp_res = requests.post(
            TEMP_API,
            json=temp_payload
        )

        print("Temp → API:", temp_res.status_code)

        # ======================
        # SENSOR
        # ======================
        sensor_payload = {

            "heart_rate":
                combined["sensor"]["telemetry"]["heart_rate"]["value"],

            "spo2":
                combined["sensor"]["telemetry"]["spo2"]["value"],

            "heart_condition":
                combined["sensor"]["condition"]["heart_rate"],

            "spo2_condition":
                combined["sensor"]["condition"]["spo2"]
        }

        sensor_res = requests.post(
            SENSOR_API,
            json=sensor_payload
        )

        print("Sensor → API:", sensor_res.status_code)

        # ======================
        # COMBINED
        # ======================
        combined_payload = {
            **temp_payload,
            **sensor_payload
        }

        combined_res = requests.post(
            COMBINED_API,
            json=combined_payload
        )

        print("Combined → API:", combined_res.status_code)

        time.sleep(1)

    except Exception as e:

        print("Error:", e)
