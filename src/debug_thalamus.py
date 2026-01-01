import os
import sys
import traceback

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("STEP 1: Importing Thalamus...")
    from brain.thalamus import Thalamus
    print(" Import Success.")

    print("STEP 2: Initializing Thalamus...")
    t = Thalamus(log_dir="/data/logs") # Use container path if needed, or default
    print(" Initialization Success.")
    
    print("STEP 3: Processing Input...")
    response = t.process_input("Hello, are you awake?", session_id="debug-session")
    print(f"RESPONSE: {response}")

except Exception:
    print("\nCRASH DETECTED! Full Traceback:")
    traceback.print_exc()
