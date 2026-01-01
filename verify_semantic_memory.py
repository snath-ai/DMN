import sys
import os
import json
import time

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from lar.dmn_dreamer import get_embedding, save_insight
from lar.memory_retrieval import get_subconscious_context

def verify_semantic_memory():
    print("🧠 Starting Hippocampus verification...")
    
    # 1. Create two distinct memories
    # Memory A: About Coding (Python)
    print("  ...Injecting Memory A (Python Coding)...")
    content_a = "User loves Python and prefers snake_case naming conventions."
    emb_a = get_embedding(content_a)
    if not emb_a:
        print("FAIL: Could not generate embedding. Is Ollama running?")
        return
        
    save_insight({
        "dream_timestamp": "2020-01-01T00:00:00", # OLD timestamp
        "insights": [{"hidden_pattern": content_a}],
        "embedding": emb_a,
        "test_tag": "A"
    })
    
    # Memory B: About Cooking (Pizza)
    print("  ...Injecting Memory B (Pizza Cooking)...")
    content_b = "User loves Pizza and prefers extra cheese."
    emb_b = get_embedding(content_b)
    save_insight({
        "dream_timestamp": "2025-01-01T00:00:00", # NEW timestamp
        "insights": [{"hidden_pattern": content_b}],
        "embedding": emb_b,
        "test_tag": "B"
    })
    
    # 2. Query for Coding (Should retrieve Memory A despite it being older, if semantic works)
    # Note: If semantic search behaves poorly, it might return both or the recent one.
    # But cosine similarity for "Write code" should be much higher for A.
    query = "How should I name my variables in this script?"
    print(f"  ...Querying: '{query}'")
    
    result = get_subconscious_context(max_insights=1, query=query)
    print(f"  ...Result: {result[:100]}...")
    
    if "snake_case" in result:
        print("✅ SUCCESS: Semantic Recall worked! Retrieved older Python memory.")
    else:
        print("❌ FAILURE: Did not retrieve Python memory.")
        if "Pizza" in result:
            print("   (It retrieved the Pizza memory instead - Recency Bias dominant or Embedding fail)")
        else:
             print("   (It retrieved nothing or unrelated)")

    # 3. Query for Food
    query_food = "I am hungry, what should I eat?"
    print(f"  ...Querying: '{query_food}'")
    result_food = get_subconscious_context(max_insights=1, query=query_food)
    
    if "Pizza" in result_food:
         print("✅ SUCCESS: Retrieved Pizza memory.")
    else:
         print("❌ FAILURE: Did not retrieve Pizza memory.")

if __name__ == "__main__":
    verify_semantic_memory()
