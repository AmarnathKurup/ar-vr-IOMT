import subprocess
import sys
import threading
import time
from pathlib import Path


BASE_DIR = Path(__file__).parent

SENSOR_OPTIONS = {
	"1": {
		"name": "Body Temperature",
		"script": BASE_DIR / "sensors" / "sim_temp.py",
	},
	"2": {
		"name": "MAX30100 (SpO2 + Heart Rate)",
		"script": BASE_DIR / "sensors" / "sim_max30100.py",
	},
}


def print_menu() -> None:
	print("\nSelect sensor simulator(s) to run:")
	print("  1. Body Temperature")
	print("  2. MAX30100 (SpO2 + Heart Rate)")
	print("  3. Run both")


def parse_selection(raw: str) -> list[str]:
	selection = raw.strip().lower()
	if selection == "3" or selection == "all":
		return ["1", "2"]

	parts = [p.strip() for p in selection.split(",") if p.strip()]
	valid = [p for p in parts if p in SENSOR_OPTIONS]
	if not valid:
		return []

	# Remove duplicates while preserving order.
	ordered_unique: list[str] = []
	for item in valid:
		if item not in ordered_unique:
			ordered_unique.append(item)
	return ordered_unique


def stream_process_output(name: str, process: subprocess.Popen[str]) -> None:
	if process.stdout is None:
		return
	for line in process.stdout:
		print(f"[{name}] {line.rstrip()}")


def launch_process(script_path: Path, label: str) -> tuple[subprocess.Popen[str], threading.Thread]:
	if not script_path.exists():
		raise FileNotFoundError(f"Simulator script not found: {script_path}")

	proc = subprocess.Popen(
		[sys.executable, "-u", str(script_path)],
		cwd=str(BASE_DIR),
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
		bufsize=1,
	)

	thread = threading.Thread(target=stream_process_output, args=(label, proc), daemon=True)
	thread.start()
	return proc, thread


def shutdown_processes(processes: list[tuple[str, subprocess.Popen[str]]]) -> None:
	for _, proc in processes:
		if proc.poll() is None:
			proc.terminate()

	deadline = time.time() + 5
	for _, proc in processes:
		if proc.poll() is None:
			remaining = max(0.0, deadline - time.time())
			try:
				proc.wait(timeout=remaining)
			except subprocess.TimeoutExpired:
				proc.kill()


def run_selected_sensors(selected_keys: list[str]) -> None:
	processes: list[tuple[str, subprocess.Popen[str]]] = []
	threads: list[threading.Thread] = []
	reported_exit: set[str] = set()

	try:
		for key in selected_keys:
			item = SENSOR_OPTIONS[key]
			label = item["name"]
			script = item["script"]
			proc, thread = launch_process(script, label)
			processes.append((label, proc))
			threads.append(thread)
			print(f"[INFO] Started {label}")

		print("[INFO] Simulators are running. Press Ctrl+C to stop all.")

		while True:
			all_exited = True
			for label, proc in processes:
				if proc.poll() is None:
					all_exited = False
				else:
					if label not in reported_exit:
						print(f"[WARN] {label} exited with code {proc.returncode}")
						reported_exit.add(label)
			if all_exited:
				break
			time.sleep(1)

	except KeyboardInterrupt:
		print("\n[INFO] Stop requested. Shutting down simulators...")
	finally:
		shutdown_processes(processes)
		for thread in threads:
			thread.join(timeout=1)
		print("[INFO] All selected simulators stopped.")


def main() -> None:
	print_menu()
	raw = input("Enter choice (1/2/3 or comma-separated like 1,2): ")
	selected = parse_selection(raw)
	if not selected:
		print("[ERROR] Invalid selection. Please run again and choose 1, 2, 3, or 1,2.")
		return

	run_selected_sensors(selected)


if __name__ == "__main__":
	main()
