import os
import sys
import json
import shutil
from unittest.mock import MagicMock

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Mock litellm BEFORE importing lar.node to avoid actual API calls
import lar.node
mock_completion = MagicMock()
mock_completion.return_value.choices = [MagicMock(message=MagicMock(content="Mock Response"))]
mock_completion.return_value.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
lar.node.completion = mock_completion

from lar.node import LLMNode
from lar.state import GraphState
import lar.memory_retrieval

# Setup Test Environment
TEST_MEMORY_DIR = "verification_memory"
TEST_MEMORY_FILE = os.path.join(TEST_MEMORY_DIR, "long_term_insights.json")

# Monkey patch the memory file path
lar.memory_retrieval.MEMORY_FILE = TEST_MEMORY_FILE

def setup():
    if os.path.exists(TEST_MEMORY_DIR): shutil.rmtree(TEST_MEMORY_DIR)
    os.makedirs(TEST_MEMORY_DIR)

    # 1. Create Mock Insights
    print(f"--- 1. Creating Mock Memory in {TEST_MEMORY_FILE} ---")
    insights = [
        {
            "dream_timestamp": "2023-10-27T10:00:00",
            "insights": [
                {"pattern": "Test Pattern 1", "description": "User loves apples."},
                {"pattern": "Test Pattern 2", "description": "User hates pears."}
            ]
        }
    ]
    with open(TEST_MEMORY_FILE, "w") as f:
        json.dump(insights, f)

def verify_feedback_loop():
    print("--- 2. Initializing LLMNode with Subconscious Enabled ---")
    node = LLMNode(
        model_name="mock-model",
        prompt_template="Tell me about fruit.",
        output_key="response",
        system_instruction="You are a fruit expert.",
        enable_subconscious=True
    )
    
    state = GraphState({})
    
    print("--- 3. Executing Node ---")
    node.execute(state)
    
    print("--- 4. Verifying System Prompt Injection ---")
    
    # Inspect the call args to mock_completion to see what messages were passed
    call_args = mock_completion.call_args
    if not call_args:
        print("❌ FAIL: completion was not called.")
        return

    # completion(model=..., messages=[...], ...)
    # kwargs are usually in call_args.kwargs
    messages = call_args.kwargs.get("messages")
    if not messages:
        print("❌ FAIL: messages argument missing in call.")
        return

    # Check System Message
    system_msg = next((m for m in messages if m["role"] == "system"), None)
    if not system_msg:
         print("❌ FAIL: System message missing.")
         return
         
    content = system_msg["content"]
    print("\n[Captured System Prompt]:")
    print(content)
    print("-" * 20)

    if "[SUBCONSCIOUS_CONTEXT]" in content:
        print("✅ Success! 'SUBCONSCIOUS_CONTEXT' tag found.")
    else:
        print("❌ FAIL: 'SUBCONSCIOUS_CONTEXT' tag NOT found.")
        return

    if "User loves apples" in content:
        print("✅ Success! Memory content 'User loves apples' found.")
    else:
        print("❌ FAIL: Memory content not found.")
        return

    print("\n🎉 Feedback Loop Verification Successful!")

if __name__ == "__main__":
    setup()
    verify_feedback_loop()
    # Cleanup
    # shutil.rmtree(TEST_MEMORY_DIR)
