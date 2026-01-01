import sys
import os
import time
import signal
import datetime

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from brain.default_mode_network import DefaultModeNetwork

# Configuration
DATA_DIR = "/data"
LOGS_FILE = os.path.join(DATA_DIR, "short_term_memory.jsonl")
MEMORY_DIR = DATA_DIR

# Thresholds
IDLE_THRESHOLD_SECONDS = 30 # Demo mode (Prod: 1800)
CHECK_INTERVAL = 10

def signal_handler(sig, frame):
    print("💤 [Dreamer] Shutting down...")
    sys.exit(0)

def main():
    print(f"🌙 [Dreamer] Daemon started. Watching {LOGS_FILE}...")
    print(f"🌙 [Dreamer] Model: {os.environ.get('OLLAMA_MODEL', 'standard')}")
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize Brain Region
    # Note: DMN will need to be instantiated with custom paths
    # We might need to patch DMN init or subclass it if it hardcodes paths
    # For now, let's assume we pass arguments (I'll need to check DMN code next to confirm)
    dmn = DefaultModeNetwork(logs_path=LOGS_FILE, memory_dir=MEMORY_DIR)
    
    last_dream_time = datetime.datetime.min

    while True:
        try:
            if not os.path.exists(LOGS_FILE):
                print(f"Waiting for logs at {LOGS_FILE}...")
                time.sleep(CHECK_INTERVAL)
                continue

            last_modified = os.path.getmtime(LOGS_FILE)
            now = time.time()
            idle_duration = now - last_modified
            
            last_interaction = datetime.datetime.fromtimestamp(last_modified)

            if idle_duration > IDLE_THRESHOLD_SECONDS:
                # Logic: Only dream if we haven't dreamed since the last interaction
                if last_dream_time < last_interaction:
                    print(f"💤 [Dreamer] Brain is idle ({int(idle_duration)}s). Spindles active...")
                    
                    # ACTIVATE DREAMING
                    dmn.activate()
                    
                    last_dream_time = datetime.datetime.now()
                    print(f"🧠 [Dreamer] Cycle Complete. Resting.")
                else:
                    # Already dreamed for this session
                    pass
            
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"❌ [Dreamer] Error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
