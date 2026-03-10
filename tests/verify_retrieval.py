import sys

# Ensure lar modules can be loaded
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from brain.hippocampus import Hippocampus

def verify_retrieval():
    print("🧠 Starting Retrieval Verification...")
    # Initialize connecting to the current ChromaDB data directory
    hippocampus = Hippocampus()
    
    # 1. Check if vector DB has records
    cold_count = hippocampus.collection.count() if hippocampus.collection else 0
    warm_count = hippocampus.warm_collection.count() if hippocampus.warm_collection else 0
    print(f"\n📊 Database State:")
    print(f"Cold Memories (Raw episodes): {cold_count}")
    print(f"Warm Memories (Dense summaries): {warm_count}")
    
    if cold_count == 0 and warm_count == 0:
        print("\n❌ VERIFICATION FAILED: Database is completely empty. Please chat with the agent and wait 30s to trigger a sleep cycle first.")
        return

    # 2. Test Semantic Retrieval directly
    test_query = "danger"
    print(f"\n🔍 Testing Semantic Retrieval for query: '{test_query}'")
    
    print("\n❄️ COLD MEMORY RECALL (Top 2 chunks):")
    cold_results = hippocampus.recall(query=test_query, max_memories=2)
    print(cold_results if cold_results else "No relevant cold memories found.")

    print("\n🔥 WARM MEMORY RECALL (Top 1 summary):")
    warm_results = hippocampus.recall_warm(query=test_query, max_memories=1)
    print(warm_results if warm_results else "No relevant warm memories found.")
    
    if cold_results or warm_results:
        print("\n✅ VERIFICATION SUCCESS: ChromaDB semantic retrieval is fetching specific memories!")
    else:
        print("\n⚠️ SYSTEM WARNING: Database has records, but retrieval returned nothing. Check embedding models.")

if __name__ == "__main__":
    verify_retrieval()
