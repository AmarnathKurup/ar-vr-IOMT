import requests, random, time

POST_URL = "http://127.0.0.1:5000/api/v1/temp"
GET_URL = "http://127.0.0.1:5000/api/v1/temp/latest"

try:
    while True:
        # 🔹 Generate temperature
        temp = {
            "temperature": round(random.uniform(36, 39), 1)
        }

        # 🔹 POST request
        post_res = requests.post(POST_URL, json=temp)
        print("🌡️ Temp POST:", post_res.json())

        # 🔹 GET request
        get_res = requests.get(GET_URL)
        latest = get_res.json()

        print("📥 Latest Temp Data:", latest)

        time.sleep(2)

except KeyboardInterrupt:
    print("Stopped generating temperature data")