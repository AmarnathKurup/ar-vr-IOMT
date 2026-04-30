import subprocess
import json
import requests
import sys
from pathlib import Path
import time

# =========================
# PATH SETUP
# =========================
BASE_DIR = Path(__file__).resolve().parent
SIMULATOR_PATH = BASE_DIR.parent / "simulator" / "simulate_sensors.py"

# =========================
# START SIMULATOR PROCESS
# =========================
process = subprocess.Popen(
    [sys.executable, "-u", str(SIMULATOR_PATH)],  # unbuffered
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
SENSOR_API = "http://127.0.0.1:5000/api/v1/max30100"
TEMP_API = "http://127.0.0.1:5000/api/v1/temp"
COMBINED_API = "http://127.0.0.1:5000/api/v1/combined"

print("🚀 Starting Simulator Bridge...\n")

# =========================
# WAIT FOR MENU
# =========================
while True:
    line = process.stdout.readline()

    if not line:
        continue

    print("RAW:", line.strip())

    if "Run both" in line:
        break  # menu is ready

# =========================
# MANUAL INPUT (FIXED)
# =========================
choice = input("Enter choice (1/2/3): ")

process.stdin.write(choice + "\n")
process.stdin.flush()

print(f"✅ Choice '{choice}' sent to simulator\n")

# =========================
# READ + FORWARD DATA
# =========================
latest_sensor = {}
latest_temp = {}

last_sent_time = 0
SEND_INTERVAL = 1  # seconds

while True:
    try:
        line = process.stdout.readline()

        if not line:
            continue

        line = line.strip()
        print("RAW:", line)

        # Extract JSON part
        if "{" not in line:
            continue

        json_part = line[line.find("{"):]

        data = json.loads(json_part)
        telemetry = data.get("telemetry", {})

        current_time = time.time()

        # ======================
        # SENSOR DATA
        # ======================
        if "spo2" in telemetry and "heart_rate" in telemetry:
            latest_sensor = {
                "heart_rate": telemetry["heart_rate"]["value"],
                "spo2": telemetry["spo2"]["value"]
            }

            if current_time - last_sent_time > SEND_INTERVAL:
                res = requests.post(SENSOR_API, json=latest_sensor, timeout=2)
                print("📡 Sensor → API:", res.status_code)

        # ======================
        # TEMP DATA
        # ======================
        if "temperature" in telemetry:
            latest_temp = {
                "temperature": telemetry["temperature"]["value"]
            }

            if current_time - last_sent_time > SEND_INTERVAL:
                res = requests.post(TEMP_API, json=latest_temp, timeout=2)
                print("🌡️ Temp → API:", res.status_code)

        # ======================
        # COMBINED DATA
        # ======================
        if latest_sensor and latest_temp:
            if current_time - last_sent_time > SEND_INTERVAL:
                combined = {
                    "heart_rate": latest_sensor["heart_rate"],
                    "spo2": latest_sensor["spo2"],
                    "temperature": latest_temp["temperature"]
                }

                res = requests.post(COMBINED_API, json=combined, timeout=2)
                print("🧠 Combined → API:", res.status_code)

                last_sent_time = current_time

    except Exception as e:
        print("❌ Error:", e)
        continue