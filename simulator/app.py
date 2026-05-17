"""
Flask interface for AR/VR-Enabled Smart Healthcare Monitoring
and Emergency Response System sensor simulator.
"""

import json
import queue
import threading
from flask import Flask, Response, request, jsonify
import requests
import time

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Import the individual runner functions and helpers directly.
# We deliberately do NOT call generate_max30100_data() because it registers
# signal handlers, which Python forbids on any thread other than the main
# thread — causing "ValueError: signal only works in main thread".
from HRgen import (
    generate_temperature_once,
    generate_sensor_once,
    parse_selection,
    SENSOR_OPTIONS,
)

app = Flask(__name__)

# ── Global simulation state ──────────────────────────────────────────────────
_stop_event: threading.Event | None = None
_sim_thread: threading.Thread | None = None
_log_queue: queue.Queue = queue.Queue(maxsize=500)
_running = False


# ==========================================
# API URLS
# ==========================================

BASE_API = "http://localhost:5000"  # Change this to your actual API URL

TEMP_API = f"{BASE_API}/api/v1/temp"

SENSOR_API = f"{BASE_API}/api/v1/max30100"

COMBINED_API = f"{BASE_API}/api/v1/combined"

# ── Intercept print() so we can stream logs to the browser ──────────────────

class _QueueWriter:
    """Tee stdout into _log_queue while keeping normal console output."""
    def __init__(self, original):
        self._orig = original

    def write(self, text):
        self._orig.write(text)
        if text.strip():
            try:
                _log_queue.put_nowait(text.rstrip())
            except queue.Full:
                try:
                    _log_queue.get_nowait()
                except queue.Empty:
                    pass
                _log_queue.put_nowait(text.rstrip())

    def flush(self):
        self._orig.flush()


import sys as _sys
_sys.stdout = _QueueWriter(_sys.stdout)


# ── Routes ───────────────────────────────────────────────────────────────────

# ==========================================
# API SENDER
# ==========================================

def send_to_api(selection):

    while not _stop_event.is_set():

        try:

            # ==========================
            # TEMPERATURE
            # ==========================

            if selection in ["1", "3"]:

                temp_data = generate_temperature_once()

                temp_payload = {

                    "temperature":
                        temp_data["telemetry"]["temperature"]["value"],

                    "temp_condition":
                        temp_data["condition"]["temperature"]
                }

                requests.post(
                    TEMP_API,
                    json=temp_payload
                )

                print(
                    "[TEMP]",
                    json.dumps(temp_payload)
                )

            # ==========================
            # SENSOR
            # ==========================

            if selection in ["2", "3"]:

                sensor_data = generate_sensor_once()

                sensor_payload = {

                    "heart_rate":
                        sensor_data["telemetry"]["heart_rate"]["value"],

                    "spo2":
                        sensor_data["telemetry"]["spo2"]["value"],

                    "heart_condition":
                        sensor_data["condition"]["heart_rate"],

                    "spo2_condition":
                        sensor_data["condition"]["spo2"]
                }

                requests.post(
                    SENSOR_API,
                    json=sensor_payload
                )

                print(
                    "[SENSOR]",
                    json.dumps(sensor_payload)
                )

            # ==========================
            # COMBINED
            # ==========================

            if selection == "3":

                combined_payload = {
                    **temp_payload,
                    **sensor_payload
                }

                requests.post(
                    COMBINED_API,
                    json=combined_payload
                )

                print(
                    "[COMBINED]",
                    json.dumps(combined_payload)
                )

            time.sleep(1)

        except Exception as e:

            print("API ERROR:", e)

@app.route("/")
def index():
    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "templates", "index.html")
    with open(tpl, "r", encoding="utf-8") as f:
        return f.read()


@app.route("/start", methods=["POST"])
def start():
    global _stop_event, _sim_thread, _running

    if _running:
        return jsonify({"status": "already_running"}), 200

    data = request.get_json(silent=True) or {}
    selection = str(data.get("selection", "3"))

    selected = parse_selection(selection)
    if not selected:
        return jsonify({"status": "error", "message": "Invalid selection"}), 400

    _stop_event = threading.Event()
    _running = True

    def _run():
        global _running
        try:
            print("[INFO] Simulator started.")

            api_thread = threading.Thread(
                target=send_to_api,
                args=(selection,),
                daemon=True
            )

            api_thread.start()

            

            while not _stop_event.is_set():

                _stop_event.wait(timeout=0.2)

        finally:
            _running = False
            print("[INFO] All simulators stopped.")

    _sim_thread = threading.Thread(target=_run, daemon=True)
    _sim_thread.start()

    label = {
        "1": "Body Temperature",
        "2": "MAX30100 (SpO2 + Heart Rate)",
        "3": "All Sensors",
    }.get(selection, "Selected Sensors")

    return jsonify({"status": "started", "sensor": label})


@app.route("/stop", methods=["POST"])
def stop():
    global _stop_event, _running

    if not _running:
        return jsonify({"status": "not_running"}), 200

    if _stop_event:
        _stop_event.set()
    _running = False

    return jsonify({"status": "stopped"})


@app.route("/status")
def status():
    return jsonify({"running": _running})


@app.route("/stream")
def stream():
    """Server-Sent Events — pushes log lines to the browser in real time."""
    def event_gen():
        while True:
            try:
                line = _log_queue.get(timeout=1.0)
                yield f"data: {json.dumps({'line': line})}\n\n"
            except queue.Empty:
                yield ": ping\n\n"   # keep-alive

    return Response(
        event_gen(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print(" AR/VR Smart Healthcare Monitor - Flask Interface")
    print(" Open  http://127.0.0.1:5050  in your browser")
    print("=" * 60)
    app.run(debug=False, threaded=True, host="0.0.0.0", port=5050)