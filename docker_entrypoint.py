import time
import subprocess
import os

print("Argus Risk Analysis System: Scheduler Started")

while True:
    print(f"\n--- Starting Analysis Scan: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")

    # This runs your existing main.py logic
    subprocess.run(["uv", "run", "main.py"])

    print("Scan complete. Sleeping for 120 seconds...")
    time.sleep(120)