import subprocess
import json
import requests
import sys
from pathlib import Path
# =========================
# PATH SETUP
# =========================
BASE_DIR = Path(__file__).resolve().parent
SIMULATOR_PATH = BASE_DIR.parent / "simulator" / "simulate_sensors.py"

process = subprocess.Popen(
    [sys.executable, str(SIMULATOR_PATH)],
    cwd=str(SIMULATOR_PATH.parent),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)
# =========================
# API ENDPOINTS
# =========================
SENSOR_API = "http://127.0.0.1:5000/api/v1/sensor"
TEMP_API = "http://127.0.0.1:5000/api/v1/temp"
COMBINED_API = "http://127.0.0.1:5000/api/v1/combined"



# 🔹 Automatically select "3" (run both sensors)
choice = input("Enter choice (1/2/3): ")
process.stdin.write(choice + "\n")
process.stdin.flush()

print("🚀 Simulator Bridge Running...\n")

# =========================
# READ + FORWARD DATA
# =========================


latest_sensor = {}
latest_temp = {}

while True:
    line = process.stdout.readline()

    if not line:
        continue

    line = line.strip()
    print("RAW:", line)

    # 🔥 FIX: extract JSON part
    if "{" not in line:
        continue

    json_part = line[line.find("{"):]

    try:
        data = json.loads(json_part)
        telemetry = data.get("telemetry", {})

        # ======================
        # SENSOR
        # ======================
        if "spo2" in telemetry and "heart_rate" in telemetry:
            latest_sensor = {
                "heart_rate": telemetry["heart_rate"]["value"],
                "spo2": telemetry["spo2"]["value"]
            }

            res = requests.post(
                "http://127.0.0.1:5000/api/v1/sensor",
                json=latest_sensor
            )
            print("📡 Sensor → API:", res.status_code)

        # ======================
        # TEMP
        # ======================
        if "temperature" in telemetry:
            latest_temp = {
                "temperature": telemetry["temperature"]["value"]
            }

            res = requests.post(
                "http://127.0.0.1:5000/api/v1/temp",
                json=latest_temp
            )
            print("🌡️ Temp → API:", res.status_code)

        # ======================
        # COMBINED
        # ======================
        if latest_sensor and latest_temp:
            combined = {
                "heart_rate": latest_sensor["heart_rate"],
                "spo2": latest_sensor["spo2"],
                "temperature": latest_temp["temperature"]
            }

            res = requests.post(
                "http://127.0.0.1:5000/api/v1/combined",
                json=combined
            )
            print("🧠 Combined → API:", res.status_code)

    except Exception as e:
        print("❌ Error parsing:", e)