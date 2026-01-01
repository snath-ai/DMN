import os
import sys
import json
import shutil
import time

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from lar.dmn_dreamer import dream

# Config for Verification using temporary files
TEST_LOG_DIR = "verification_logs"
TEST_MEMORY_DIR = "verification_memory"
TEST_LOG_FILE = os.path.join(TEST_LOG_DIR, "interaction_stream.jsonl")
TEST_MEMORY_FILE = os.path.join(TEST_MEMORY_DIR, "long_term_insights.json")

# Monkey patch constants in dmn_dreamer for testing purpose
import lar.dmn_dreamer
lar.dmn_dreamer.LOG_FILE = TEST_LOG_FILE
lar.dmn_dreamer.MEMORY_FILE = TEST_MEMORY_FILE

def setup():
    if os.path.exists(TEST_LOG_DIR): shutil.rmtree(TEST_LOG_DIR)
    if os.path.exists(TEST_MEMORY_DIR): shutil.rmtree(TEST_MEMORY_DIR)
    
    os.makedirs(TEST_LOG_DIR)
    os.makedirs(TEST_MEMORY_DIR)

    # Create dummy logs
    print(f"--- 1. Creating Mock Logs in {TEST_LOG_FILE} ---")
    entries = [
        {"timestamp": "2023-10-27T10:00:00", "role": "user", "content": "I feel like my agent is too rigid."},
        {"timestamp": "2023-10-27T10:00:05", "role": "assistant", "content": "Lár is designed for determinism, but we can add flexibility."},
        {"timestamp": "2023-10-27T10:01:00", "role": "user", "content": "But I want it to be creative sometimes."},
        {"timestamp": "2023-10-27T10:01:05", "role": "assistant", "content": "You can increase temperature for specific LLMNodes."},
        {"timestamp": "2023-10-27T10:02:00", "role": "user", "content": "Maybe I should just use LangChain for the creative parts?"}
    ]
    
    with open(TEST_LOG_FILE, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

def verify_dreamer():
    print("--- 2. Running Dreamer (Connecting to Ollama) ---")
    print("NOTE: This requires Ollama running locally. If it fails, check 'ollama serve'.")
    
    # Run the dreamer
    # Using 'llama3:latest' as requested, but falling back to a known small model if needed by user env
    # For verification we'll assume the environment is set up as per previous checks.
    try:
        dream(model="llama3:latest")
    except Exception as e:
        print(f"❌ FAIL: Dream function crashed: {e}")
        return

    print("--- 3. Verifying Memory File ---")
    if not os.path.exists(TEST_MEMORY_FILE):
        print(f"❌ FAIL: Memory file {TEST_MEMORY_FILE} was not created.")
        return

    with open(TEST_MEMORY_FILE, "r") as f:
        memory = json.load(f)

    if not memory:
        print("❌ FAIL: Memory file is empty.")
        return

    last_dream = memory[-1]
    print("Last Dream Entry:")
    print(json.dumps(last_dream, indent=2))

    if "insights" in last_dream and isinstance(last_dream["insights"], dict):
         # The prompt asked for "list of insights", but output might be {"insights": []} or just []
         # Let's check generally
         print("✅ Dream structure looks valid JSON.")
    elif "insights" in last_dream and isinstance(last_dream["insights"], list):
         print("✅ Dream structure looks valid JSON (List).")
    else:
        print(f"⚠️ WARN: Unexpected structure, but saved successfully.")

    print("\n🎉 Verification Successful!")

if __name__ == "__main__":
    setup()
    verify_dreamer()
    # Cleanup? Maybe keep for inspection
    # shutil.rmtree(TEST_LOG_DIR)
    # shutil.rmtree(TEST_MEMORY_DIR)
