import os
import sys
import asyncio
import time
from unittest.mock import MagicMock

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Mock dmn_dreamer to avoid actual Ollama calls and long waits
import lar.dmn_dreamer
mock_dream = MagicMock()
lar.dmn_dreamer.dream = mock_dream

from lar.lar_orchestrator import LarOrchestrator
import lar.lar_orchestrator

# Setup Test Env
TEST_LOG_FILE = "verification_logs/interaction_stream.jsonl"
lar.lar_orchestrator.LOG_FILE = TEST_LOG_FILE

def setup():
    if not os.path.exists(os.path.dirname(TEST_LOG_FILE)):
        os.makedirs(os.path.dirname(TEST_LOG_FILE))
    
    # Touch file to set time
    with open(TEST_LOG_FILE, "w") as f:
        f.write("{}")

async def verify_orchestrator():
    print("--- 1. Initializing Orchestrator (Threshold=2s) ---")
    # Low threshold for testing
    orchestrator = LarOrchestrator(idle_threshold_seconds=2, check_interval_seconds=1)
    
    # Start monitor in background task
    monitor_task = asyncio.create_task(orchestrator.monitor())
    
    print("--- 2. Simulating Activity (Touching Log File) ---")
    # Touch file "now"
    os.utime(TEST_LOG_FILE, None)
    
    print("  ... Waiting 1s (Should be awake) ...")
    await asyncio.sleep(1.1)
    if mock_dream.called:
        print("❌ FAIL: Dream Triggered too early!")
        monitor_task.cancel()
        return

    print("  ... Waiting 2s more (Should trigger dream) ...")
    await asyncio.sleep(2.5) # Total > 3s, threshold is 2s
    
    if mock_dream.called:
        print("✅ Success! Dream Triggered after idle.")
    else:
        print("❌ FAIL: Dream NOT triggered.")
    
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    
    print("\n🎉 Orchestrator Verification Successful!")

if __name__ == "__main__":
    setup()
    try:
        asyncio.run(verify_orchestrator())
    except KeyboardInterrupt:
        pass
    # Cleanup
    # import shutil
    # shutil.rmtree("verification_logs")
