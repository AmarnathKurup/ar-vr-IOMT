from flask import Flask, request, jsonify, send_file
import datetime, json, csv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# ===============================
# EXPORT COMBINED DATA (IMPORTANT)
# ===============================

@app.route('/api/v1/export/combined/json', methods=['GET'])
def export_combined_json():
    if not combined_store:
        return jsonify({"error": "No data"}), 400

    with open("combined_data.json", "w") as f:
        json.dump(combined_store, f, indent=4)

    return send_file("combined_data.json", as_attachment=True)




@app.route('/api/v1/export/combined/csv', methods=['GET'])
def export_combined_csv():
    if not combined_store:
        return jsonify({"error": "No data"}), 400

    keys = combined_store[0].keys()

    with open("combined_data.csv", "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(combined_store)

    return send_file("combined_data.csv", as_attachment=True)


@app.route('/api/v1/export/temp/csv', methods=['GET'])
def export_temp_csv():
    if not temp_store:
        return jsonify({"error": "No data"}), 400

    keys = temp_store[0].keys()

    with open("temp_data.csv", "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys) 
        writer.writeheader()
        writer.writerows(temp_store)

    return send_file("temp_data.csv", as_attachment=True)

@app.route('/api/v1/export/sensor/csv', methods=['GET'])
def export_sensor_csv():
    if not sensor_store:
        return jsonify({"error": "No data"}), 400

    keys = sensor_store[0].keys()

    with open("sensor_data.csv", "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys) 
        writer.writeheader()
        writer.writerows(sensor_store)

    return send_file("sensor_data.csv", as_attachment=True)

# ===============================
# 3. TEMPERATURE API
# ===============================
temp_store = []

@app.route('/api/v1/temp', methods=['POST'])
def publish_temp():
    data = request.json
    data["timestamp"] = datetime.datetime.now().isoformat()
    temp_store.append(data)

    return jsonify({
        "message": "Temperature stored",
        "count": len(temp_store)
    })

@app.route('/api/v1/temp/latest', methods=['GET'])
def get_latest_temp():
    return jsonify(temp_store[-1] if temp_store else {})

@app.route('/api/v1/temp/all', methods=['GET'])
def get_all_temp():
    return jsonify(temp_store)

# ===============================
# 4. SENSOR API (HR + SpO2)
# ===============================
sensor_store = []

@app.route('/api/v1/sensor', methods=['POST'])
def publish_sensor():
    data = request.json
    data["timestamp"] = datetime.datetime.now().isoformat()
    sensor_store.append(data)

    return jsonify({
        "message": "Sensor data stored",
        "count": len(sensor_store)
    })

@app.route('/api/v1/sensor/latest', methods=['GET'])
def get_latest_sensor():
    return jsonify(sensor_store[-1] if sensor_store else {})

@app.route('/api/v1/sensor/all', methods=['GET'])
def get_all_sensor():
    return jsonify(sensor_store)

# ===============================
# 5. COMBINED API (🔥 IMPORTANT)
# ===============================
combined_store = []

@app.route('/api/v1/combined', methods=['POST'])
def receive_combined():
    data = request.json
    combined_store.append(data)

    return jsonify({
        "message": "Combined data stored",
        "count": len(combined_store)
    })

@app.route('/api/v1/combined/latest', methods=['GET'])
def get_latest_combined():
    return jsonify(combined_store[-1] if combined_store else {})

@app.route('/api/v1/combined/all', methods=['GET'])
def get_all_combined():
    return jsonify(combined_store)

# ===============================
# 6. OPTIONAL: HEALTH CHECK
# ===============================
@app.route('/')
def home():
    return jsonify({
        "status": "API Running",
        "endpoints Post requests": [
            "/api/v1/sensor",
            "/api/v1/temp",
            "/api/v1/combined"
        ],
        "endpoints Get requests": [
            "/api/v1/sensor/latest",
            "/api/v1/temp/latest",
            "/api/v1/combined/latest",
            "/api/v1/sensor/all",
            "/api/v1/temp/all",
            "/api/v1/combined/all"
        ],
    })

# ===============================
# RUN SERVER
# ===============================
if __name__ == "__main__":
    app.run(debug=True)