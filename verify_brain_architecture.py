import sys
import os
import time

# Ensure src is in path
sys.path.insert(0, os.path.abspath("src"))

from src.brain.thalamus import Thalamus

def verify_brain():
    print("🧠 Initializing Human Brain Model...")
    t = Thalamus()
    
    print("\n--- Test 1: Amygdala Response (Emotion) ---")
    response = t.process_input("I am extremely angry and frustrated!")
    print(f"Response: {response[:50]}...")
    # We check logs to see if emotion was captured (simulated here by checking print output in real run)
    
    print("\n--- Test 2: Hippocampus Recall (Memory) ---")
    response_mem = t.process_input("What is my favorite programming language (from previous memories)?")
    print(f"Response: {response_mem[:50]}...")
    
    print("\n--- Test 3: Default Mode Network (Dreaming) ---")
    print("Forcing activation...")
    try:
        t.dmn.activate()
        print("✅ DMN Activation Successful.")
    except Exception as e:
        print(f"❌ DMN Failed: {e}")

if __name__ == "__main__":
    verify_brain()
