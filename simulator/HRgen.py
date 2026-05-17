import json
import random
import signal
import threading
import time
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Paths  (HRgen.py lives at project root; configs are in simulator/sensors/configs/)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
BODY_TEMP_CONFIG_PATH = BASE_DIR  / "sensors" / "configs" / "body_temperature.json"
SPO2_CONFIG_PATH      = BASE_DIR  / "sensors" / "configs" / "spo2.json"
HEART_RATE_CONFIG_PATH = BASE_DIR  / "sensors" / "configs" / "heart_rate.json"

# ---------------------------------------------------------------------------
# Shared condition map for MAX30100 (SpO2 + Heart Rate)
# ---------------------------------------------------------------------------

MIN_CONDITION_SECONDS = 180
MAX_CONDITION_SECONDS = 300

SHARED_CONDITIONS = {
    "normal": {
        "spo2": "normal",
        "heart_rate": "normal",
    },
    "low": {
        "spo2": "acceptable_low",
        "heart_rate": "bradycardia_mild",
    },
    "medium": {
        "spo2": "hypoxemia_mild",
        "heart_rate": "tachycardia_mild",
    },
    "high": {
        "spo2": "hypoxemia_moderate",
        "heart_rate": "tachycardia_severe",
    },
    "critical": {
        "spo2": "hypoxemia_severe",
        "heart_rate": "vfib_zone",
    },
}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def pick_next_condition_key(all_keys: list[str], current_key: Optional[str]) -> str:
    if current_key is None:
        return random.choice(all_keys)
    other_keys = [k for k in all_keys if k != current_key]
    return random.choice(other_keys) if other_keys else current_key


def generate_value(condition: dict, precision_digits: int) -> float:
    low, high = condition["range"]
    return round(random.uniform(low, high), precision_digits)


# ---------------------------------------------------------------------------
# Body Temperature simulator
# ---------------------------------------------------------------------------

def run_body_temperature(stop_event: threading.Event) -> None:
    config = load_config(BODY_TEMP_CONFIG_PATH)
    sensor = config["sensor"]
    conditions = config["conditions"]

    condition_keys = list(conditions.keys())
    sampling_rate_hz = float(sensor.get("sampling_rate_hz", 1.0))
    if sampling_rate_hz <= 0:
        raise ValueError(f"Invalid sampling_rate_hz: {sampling_rate_hz}")

    precision_digits = int(sensor.get("precision_digits", 1))
    sleep_seconds = 1.0 / sampling_rate_hz

    current_condition_key: Optional[str] = None
    condition_end_monotonic = time.monotonic()

    print("[Body Temperature] Simulation started.")

    while not stop_event.is_set():
        now = time.monotonic()
        if now >= condition_end_monotonic:
            current_condition_key = pick_next_condition_key(condition_keys, current_condition_key)
            hold_seconds = random.randint(MIN_CONDITION_SECONDS, MAX_CONDITION_SECONDS)
            condition_end_monotonic = now + hold_seconds

            cond = conditions[current_condition_key]
            print(
                f"[Body Temperature] Condition switched to "
                f"{cond['label']} ({current_condition_key}) for {hold_seconds}s "
                f"with range {cond['range']}"
            )

        selected_condition = conditions[current_condition_key]
        temp_value = generate_value(selected_condition, precision_digits)
        temp_label = selected_condition["label"]

        payload = {
            "telemetry": {
                "temperature": {
                    "value": temp_value,
                    "unit": sensor["unit"].get("primary", "C"),
                }
            },
            "condition": {
                "temperature": temp_label
                
            }
        }
        print(f"[Body Temperature] {json.dumps(payload)}")
        time.sleep(sleep_seconds)

    print("[Body Temperature] Simulation stopped.")


# ---------------------------------------------------------------------------
# MAX30100 (SpO2 + Heart Rate) simulator
# ---------------------------------------------------------------------------

def run_max30100(stop_event: threading.Event) -> None:
    spo2_config  = load_config(SPO2_CONFIG_PATH)
    heart_config = load_config(HEART_RATE_CONFIG_PATH)

    spo2_sensor  = spo2_config["sensor"]
    heart_sensor = heart_config["sensor"]
    spo2_conditions  = spo2_config["conditions"]
    heart_conditions = heart_config["conditions"]

    condition_keys = list(SHARED_CONDITIONS.keys())
    spo2_sampling_rate_hz  = float(spo2_sensor.get("sampling_rate_hz", 1.0))
    heart_sampling_rate_hz = float(heart_sensor.get("sampling_rate_hz", 1.0))
    sampling_rate_hz = max(spo2_sampling_rate_hz, heart_sampling_rate_hz)
    if sampling_rate_hz <= 0:
        raise ValueError(f"Invalid sampling_rate_hz: {sampling_rate_hz}")

    spo2_precision  = int(spo2_sensor.get("precision_digits", 1))
    heart_precision = int(heart_sensor.get("precision_digits", 1))
    sleep_seconds   = 1.0 / sampling_rate_hz

    current_condition_key: Optional[str] = None
    condition_end_monotonic = time.monotonic()

    print("[MAX30100] Combined SpO2 + Heart Rate simulation started.")

    while not stop_event.is_set():
        now = time.monotonic()
        if now >= condition_end_monotonic:
            current_condition_key = pick_next_condition_key(condition_keys, current_condition_key)
            hold_seconds = random.randint(MIN_CONDITION_SECONDS, MAX_CONDITION_SECONDS)
            condition_end_monotonic = now + hold_seconds

            shared_state = SHARED_CONDITIONS[current_condition_key]
            spo2_cond  = spo2_conditions[shared_state["spo2"]]
            heart_cond = heart_conditions[shared_state["heart_rate"]]
            print(
                f"[MAX30100] Condition switched to {current_condition_key} for {hold_seconds}s "
                f"| SpO2={spo2_cond['label']} {spo2_cond['range']} "
                f"| HR={heart_cond['label']} {heart_cond['range']}"
            )

        shared_state = SHARED_CONDITIONS[current_condition_key]
        spo2_cond  = spo2_conditions[shared_state["spo2"]]
        heart_cond = heart_conditions[shared_state["heart_rate"]]

        spo2_value  = generate_value(spo2_cond,  spo2_precision)
        heart_value = generate_value(heart_cond, heart_precision)

        payload = {
            "telemetry": {
                "spo2": {
                    "value": spo2_value,
                    "unit": spo2_sensor["unit"].get("primary", "%"),
                },
                "heart_rate": {
                    "value": heart_value,
                    "unit": heart_sensor["unit"].get("primary", "bpm"),
                },
            },
            "condition": {
                "spo2":   spo2_cond["label"],
                "heart_rate": heart_cond["label"]
            },
        }
        print(f"[MAX30100] {json.dumps(payload)}")

        time.sleep(sleep_seconds)

    print("[MAX30100] Simulation stopped.")


# ---------------------------------------------------------------------------
# Combined  (temperature + SpO2 + Heart Rate) simulator
# ---------------------------------------------------------------------------
   
def run_combined(stop_event: threading.Event):

    temp_data = run_body_temperature(stop_event)

    sensor_data = run_max30100(stop_event)

    return {
        "temperature": temp_data,
        "sensor": sensor_data
    }


# ---------------------------------------------------------------------------
# Menu + selection logic
# ---------------------------------------------------------------------------

SENSOR_OPTIONS = {
    "1": "Body Temperature",
    "2": "MAX30100 (SpO2 + Heart Rate)",
}

SENSOR_RUNNERS = {
    "1": run_body_temperature,
    "2": run_max30100,
}


def print_menu() -> None:
    print("\nSelect sensor simulator(s) to run:")
    print("  1. Body Temperature")
    print("  2. MAX30100 (SpO2 + Heart Rate)")
    print("  3. Run both")


def parse_selection(raw: str) -> list[str]:
    selection = raw.strip().lower()
    if selection in ("3", "all"):
        return ["1", "2"]

    parts = [p.strip() for p in selection.split(",") if p.strip()]
    valid = [p for p in parts if p in SENSOR_OPTIONS]
    if not valid:
        return []

    ordered_unique: list[str] = []
    for item in valid:
        if item not in ordered_unique:
            ordered_unique.append(item)
    return ordered_unique


def generate_max30100_data(sensor_selection: str):
    """
    Run the selected sensor simulator(s) in a continuous loop.

    Parameters
    ----------
    sensor_selection : str
        "1"   -> Body Temperature only
        "2"   -> MAX30100 (SpO2 + Heart Rate) only
        "3"   -> Both simultaneously
        "1,2" -> Same as "3"
    """
    selected = parse_selection(sensor_selection)
    if not selected:
        print("[ERROR] Invalid selection. Use '1', '2', '3', or '1,2'.")
        return
    
    if sensor_selection == "1":
        return run_body_temperature(threading.Event())
    
    if sensor_selection == "2":
        return run_max30100(threading.Event())
    
    if sensor_selection == "3":
        return run_combined(threading.Event())
    

    stop_event = threading.Event()
    threads: list[threading.Thread] = []

    def _handle_stop(signum, frame):
        print("\n[INFO] Stop requested. Shutting down simulators...")
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    for key in selected:
        name   = SENSOR_OPTIONS[key]
        runner = SENSOR_RUNNERS[key]
        t = threading.Thread(target=runner, args=(stop_event,), name=name, daemon=True)
        t.start()
        threads.append(t)
        print(f"[INFO] Started {name}")

    print("[INFO] Simulators are running. Press Ctrl+C to stop all.")

    while not stop_event.is_set():
        # Join with a small timeout allows the main thread to 
        # periodically check for signals
        for t in threads:
            t.join(timeout=0.1)
        
        # If all threads have finished naturally, break the loop
        if not any(t.is_alive() for t in threads):
            break

    print("[INFO] All selected simulators stopped.")


def main() -> None:
    print_menu()
    raw = input("Enter choice (1/2/3 or comma-separated like 1,2): ")
    generate_max30100_data(raw)


# =========================================================
# SINGLE DATA GENERATORS
# =========================================================

def generate_temperature_once():

    config = load_config(
        BODY_TEMP_CONFIG_PATH
    )

    sensor = config["sensor"]

    conditions = config["conditions"]

    condition = random.choice(
        list(conditions.values())
    )

    value = generate_value(
        condition,
        int(sensor.get(
            "precision_digits",
            1
        ))
    )

    return {

        "telemetry": {

            "temperature": {

                "value": value
            }
        },

        "condition": {

            "temperature":
                condition["label"]
        }
    }


def generate_sensor_once():

    spo2_config = load_config(
        SPO2_CONFIG_PATH
    )

    heart_config = load_config(
        HEART_RATE_CONFIG_PATH
    )

    spo2_conditions = spo2_config[
        "conditions"
    ]

    heart_conditions = heart_config[
        "conditions"
    ]

    spo2_cond = random.choice(
        list(spo2_conditions.values())
    )

    heart_cond = random.choice(
        list(heart_conditions.values())
    )

    return {

        "telemetry": {

            "spo2": {

                "value":
                    generate_value(
                        spo2_cond,
                        1
                    )
            },

            "heart_rate": {

                "value":
                    generate_value(
                        heart_cond,
                        1
                    )
            }
        },

        "condition": {

            "spo2":
                spo2_cond["label"],

            "heart_rate":
                heart_cond["label"]
        }
    }

if __name__ == "__main__":
    main()
















# import random

# def generate_max30100_data():
#     return {
#         "heart_rate": random.randint(60, 130),
#         "spo2": random.randint(85, 100),
#         "condition": random.choice(["normal", "low_spo2", "high_heart_rate"])
#     }
