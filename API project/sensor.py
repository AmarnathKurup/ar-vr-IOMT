import requests, time
from HRgen import *

POST_URL = "http://127.0.0.1:5000/api/v1/max30100"
GET_URL = "http://127.0.0.1:5000/api/v1/max30100/latest"

try:
    while True:
        # 🔹 Generate sensor data
        # sensor = {
        #     "heart_rate": random.randint(60, 130),
        #     "spo2": random.randint(85, 100)
        # }
        max30100 = generate_max30100_data()


        # 🔹 POST request
        post_res = requests.post(POST_URL, json=max30100)
        print("📡 max30100 POST:", post_res.json())

        # 🔹 GET request (latest data)
        get_res = requests.get(GET_URL)
        latest = get_res.json()

        print("📥 Latest max30100 Data:", latest)

        time.sleep(2)

except KeyboardInterrupt:
    print("Stopped generating max30100 data")



    #need to create the get api here  for sensor as well as for the temperature
    #this file contains  both the heartbeat and the spO2 

    #the next step will  be the api will be given to the ai model to predict it
