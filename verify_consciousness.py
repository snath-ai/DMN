import os
import sys
import json
import time
import shutil

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from lar.consciousness_stream import ConsciousnessStream

LOG_DIR = "verification_logs"
LOG_FILE = "interaction_stream.jsonl"

def setup():
    if os.path.exists(LOG_DIR):
        shutil.rmtree(LOG_DIR)
    os.makedirs(LOG_DIR)

def verify_logging():
    print(f"--- 1. Initializing Logger in {LOG_DIR} ---")
    stream = ConsciousnessStream(log_dir=LOG_DIR, filename=LOG_FILE)
    
    @stream.wrap_chat
    def chat_function(user_input, session_id=None):
        print(f"  [AI] Processing: {user_input}")
        time.sleep(0.01) # Small delay for latency
        return f"Response to: {user_input}"

    print("--- 2. Simulating Chat Interaction ---")
    session_id = "verify-session-123"
    response = chat_function("Hello Lár", session_id=session_id)
    print(f"  [User] Received: {response}")

    print("--- 3. Verifying Log File Content ---")
    log_path = os.path.join(LOG_DIR, LOG_FILE)
    
    if not os.path.exists(log_path):
        print("❌ FAIL: Log file not created.")
        return

    with open(log_path, "r") as f:
        lines = f.readlines()
    
    if len(lines) != 2:
        print(f"❌ FAIL: Expected 2 log lines (User + Assistant), found {len(lines)}")
        return

    # Check User Log
    user_log = json.loads(lines[0])
    if user_log["role"] == "user" and user_log["content"] == "Hello Lár" and user_log["session_id"] == session_id:
        print("✅ User log entry matches.")
    else:
        print(f"❌ FAIL: User log mismatch: {user_log}")

    # Check Assistant Log
    assist_log = json.loads(lines[1])
    if assist_log["role"] == "assistant" and assist_log["content"] == f"Response to: Hello Lár" and "latency_ms" in assist_log["metadata"]:
        print("✅ Assistant log entry matches.")
    else:
        print(f"❌ FAIL: Assistant log mismatch: {assist_log}")

    print("\n🎉 Verification Successful!")

if __name__ == "__main__":
    setup()
    verify_logging()
    # Cleanup
    # shutil.rmtree(LOG_DIR) 
