import json
import os
import random
import signal
import time
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent / "configs" / "body_temperature.json"

MIN_CONDITION_SECONDS = 180
MAX_CONDITION_SECONDS = 300




def load_config(config_path: Path) -> dict:
	with config_path.open("r", encoding="utf-8") as f:
		return json.load(f)


def pick_next_condition_key(all_keys: list[str], current_key: Optional[str]) -> str:
	if current_key is None:
		return random.choice(all_keys)

	other_keys = [k for k in all_keys if k != current_key]
	if not other_keys:
		return current_key
	return random.choice(other_keys)


def generate_temperature(condition: dict, precision_digits: int) -> float:
	low, high = condition["range"]
	value = random.uniform(low, high)
	return round(value, precision_digits)


def build_payload(sensor: dict, value: float) -> dict:
	return {
		"telemetry": {
			"temperature": {
				"value": value,
				"unit": sensor["unit"].get("primary", "C"),
			}
		}
	}


def publish_payload(payload: dict) -> None:
	print(json.dumps(payload))


def run() -> None:
	config = load_config(CONFIG_PATH)
	sensor = config["sensor"]
	conditions = config["conditions"]

	condition_keys = list(conditions.keys())
	sampling_rate_hz = float(sensor.get("sampling_rate_hz", 1.0))
	if sampling_rate_hz <= 0:
		raise ValueError(f"Invalid sampling_rate_hz: {sampling_rate_hz}")

	
	precision_digits = int(sensor.get("precision_digits", 1))
	sleep_seconds = 1.0 / sampling_rate_hz

	
	

	stop_requested = False

	def _handle_stop(signum, frame):
		nonlocal stop_requested
		stop_requested = True

	signal.signal(signal.SIGINT, _handle_stop)
	signal.signal(signal.SIGTERM, _handle_stop)

	
	current_condition_key: Optional[str] = None
	condition_end_monotonic = time.monotonic()

	print("[INFO] Body temperature simulation started. Press Ctrl+C to stop.")
	

	while not stop_requested:
		now = time.monotonic()
		if now >= condition_end_monotonic:
			current_condition_key = pick_next_condition_key(condition_keys, current_condition_key)
			hold_seconds = random.randint(MIN_CONDITION_SECONDS, MAX_CONDITION_SECONDS)
			condition_end_monotonic = now + hold_seconds

			cond = conditions[current_condition_key]
			print(
				"[INFO] Condition switched to "
				f"{cond['label']} ({current_condition_key}) for {hold_seconds}s "
				f"with range {cond['range']}"
			)

		selected_condition = conditions[current_condition_key]
		temp_value = generate_temperature(selected_condition, precision_digits)
		payload = build_payload(sensor, temp_value)
		publish_payload(payload)

		
		time.sleep(sleep_seconds)

	
	print("[INFO] Simulation stopped.")


if __name__ == "__main__":
	run()
