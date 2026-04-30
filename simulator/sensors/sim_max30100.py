import json
import os
import random
import signal
import time
from pathlib import Path
from typing import Optional




SPO2_CONFIG_PATH = Path(__file__).parent / "configs" / "spo2.json"
HEART_RATE_CONFIG_PATH = Path(__file__).parent / "configs" / "heart_rate.json"

MIN_CONDITION_SECONDS = 180
MAX_CONDITION_SECONDS = 300

TOPIC_PREFIX = os.getenv("TOPIC_PREFIX", "iomt")
GENERIC_TOPIC = os.getenv("GENERIC_TOPIC", "localhost")
THIS_DEVICE_ID = "device001"

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


def load_config(config_path: Path) -> dict:
	with config_path.open("r", encoding="utf-8") as f:
		return json.load(f)


def load_sensor_configs() -> tuple[dict, dict]:
	return load_config(SPO2_CONFIG_PATH), load_config(HEART_RATE_CONFIG_PATH)


def pick_next_condition_key(all_keys: list[str], current_key: Optional[str]) -> str:
	if current_key is None:
		return random.choice(all_keys)

	other_keys = [k for k in all_keys if k != current_key]
	if not other_keys:
		return current_key
	return random.choice(other_keys)


def generate_value(condition: dict, precision_digits: int) -> float:
	low, high = condition["range"]
	value = random.uniform(low, high)
	return round(value, precision_digits)


def build_payload(spo2_sensor: dict, heart_sensor: dict, spo2_value: float, heart_value: float) -> dict:
	return {
		"telemetry": {
			"spo2": {
				"value": spo2_value,
				"unit": spo2_sensor["unit"].get("primary", "%"),
			},
			"heart_rate": {
				"value": heart_value,
				"unit": heart_sensor["unit"].get("primary", "bpm"),
			},
		}
	}


def publish_payload(payload: dict) -> None:
	print(json.dumps(payload))


def run() -> None:
	spo2_config, heart_config = load_sensor_configs()
	spo2_sensor = spo2_config["sensor"]
	heart_sensor = heart_config["sensor"]
	spo2_conditions = spo2_config["conditions"]
	heart_conditions = heart_config["conditions"]

	condition_keys = list(SHARED_CONDITIONS.keys())
	spo2_sampling_rate_hz = float(spo2_sensor.get("sampling_rate_hz", 1.0))
	heart_sampling_rate_hz = float(heart_sensor.get("sampling_rate_hz", 1.0))
	sampling_rate_hz = max(spo2_sampling_rate_hz, heart_sampling_rate_hz)
	if sampling_rate_hz <= 0:
		raise ValueError(f"Invalid sampling_rate_hz: {sampling_rate_hz}")

	
	spo2_precision_digits = int(spo2_sensor.get("precision_digits", 1))
	heart_precision_digits = int(heart_sensor.get("precision_digits", 1))
	sleep_seconds = 1.0 / sampling_rate_hz

	
	stop_requested = False

	def _handle_stop(signum, frame):
		nonlocal stop_requested
		stop_requested = True

	signal.signal(signal.SIGINT, _handle_stop)
	signal.signal(signal.SIGTERM, _handle_stop)

	current_condition_key: Optional[str] = None
	condition_end_monotonic = time.monotonic()

	print("[INFO] Combined SpO2 + Heart Rate simulation started. Press Ctrl+C to stop.")

	while not stop_requested:
		now = time.monotonic()
		if now >= condition_end_monotonic:
			current_condition_key = pick_next_condition_key(condition_keys, current_condition_key)
			hold_seconds = random.randint(MIN_CONDITION_SECONDS, MAX_CONDITION_SECONDS)
			condition_end_monotonic = now + hold_seconds

			shared_state = SHARED_CONDITIONS[current_condition_key]
			spo2_condition = spo2_conditions[shared_state["spo2"]]
			heart_condition = heart_conditions[shared_state["heart_rate"]]
			print(
				"[INFO] Condition switched to "
				f"{current_condition_key} for {hold_seconds}s "
				f"| SpO2={spo2_condition['label']} {spo2_condition['range']} "
				f"| HR={heart_condition['label']} {heart_condition['range']}"
			)

		shared_state = SHARED_CONDITIONS[current_condition_key]
		spo2_condition = spo2_conditions[shared_state["spo2"]]
		heart_condition = heart_conditions[shared_state["heart_rate"]]
		spo2_value = generate_value(spo2_condition, spo2_precision_digits)
		heart_value = generate_value(heart_condition, heart_precision_digits)
		payload = build_payload(spo2_sensor, heart_sensor, spo2_value, heart_value)
		publish_payload(payload)

		time.sleep(sleep_seconds)

	print("[INFO] Simulation stopped.")


if __name__ == "__main__":
	run()
