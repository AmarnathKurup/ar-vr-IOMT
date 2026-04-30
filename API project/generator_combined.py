import requests
import random
import time

# 🔹 POST endpoints
SENSOR_POST_URL = "http://127.0.0.1:5000/api/v1/sensor"
TEMP_POST_URL = "http://127.0.0.1:5000/api/v1/temp"
COMBINED_POST_URL = "http://127.0.0.1:5000/api/v1/combined"

# 🔹 GET endpoints
SENSOR_GET_URL = "http://127.0.0.1:5000/api/v1/sensor/latest"
TEMP_GET_URL = "http://127.0.0.1:5000/api/v1/temp/latest"

try:
    while True:

        # =========================
        # 1️⃣ GENERATE SENSOR DATA
        # =========================
        sensor_data = {
            "heart_rate": random.randint(60, 130),
            "spo2": random.randint(85, 100)
        }

        sensor_res = requests.post(SENSOR_POST_URL, json=sensor_data)
        print("📡 Sensor POST:", sensor_res.json())


        # =========================
        # 2️⃣ GENERATE TEMP DATA
        # =========================
        temp_data = {
            "temperature": round(random.uniform(36.0, 39.5), 1)
        }

        temp_res = requests.post(TEMP_POST_URL, json=temp_data)
        print("🌡️ Temp POST:", temp_res.json())


        # =========================
        # 3️⃣ GET LATEST DATA
        # =========================
        sensor_latest = requests.get(SENSOR_GET_URL).json()
        temp_latest = requests.get(TEMP_GET_URL).json()


        # =========================
        # 4️⃣ COMBINE DATA
        # =========================
        combined_data = {
            "heart_rate": sensor_latest.get("heart_rate"),
            "spo2": sensor_latest.get("spo2"),
            "temperature": temp_latest.get("temperature"),
            "timestamp": sensor_latest.get("timestamp")
        }

        print("\n🧠 COMBINED DATA:")
        print(combined_data)


        # =========================
        # 5️⃣ POST COMBINED DATA
        # =========================
        combined_res = requests.post(COMBINED_POST_URL, json=combined_data)
        print("📤 Combined POST:", combined_res.json())


        # 6️⃣ TERMINAL DISPLAY
        status = "NORMAL"
        if combined_data["heart_rate"] > 120 or combined_data["spo2"] < 90:
            status = "CRITICAL"

        print("\n🏥 LIVE MONITOR")
        print(f"Heart Rate : {combined_data['heart_rate']}")
        print(f"SpO₂       : {combined_data['spo2']}")
        print(f"Temp       : {combined_data['temperature']}")
        print(f"Status     : {status}")
        print("-" * 40)

        time.sleep(2)

except KeyboardInterrupt:
    print("\nStopped generator.")


    #Required:
    #1. Combine the sensor and temp data into one file (done)
    #2. Post the combined data to a new endpoint (done)
    #3. Display the combined data in the terminal (done)
    #4. Ensure the combined data is stored in the database (need to check backend code)
    #5. Create a GET endpoint to retrieve the combined data (need to check backend code
    #6. Test the entire flow to ensure data is generated, combined, stored, and displayed correctly (to be done)
    #7. Handle any exceptions or edge cases (to be done)
    
    #need to write the code for combining all the apis
    #need the get link and post link for all the apis and 
    #then combine them in one file and run that file to generate 
    # the data for all the apis at once so that we can see the data 
    # in the terminal and also in the database at the same time.