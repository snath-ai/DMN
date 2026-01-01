import json
import os
import uuid

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_MEMORY_FILE = os.path.join(BASE_DIR, "memory", "long_term_insights.json")
NEW_DREAMS_FILE = os.path.join(BASE_DIR, "memory", "dreams.json")
NEW_VECTORS_FILE = os.path.join(BASE_DIR, "memory", "dream_vectors.json")

def migrate():
    print("🧠 Starting Memory Migration...")
    
    if not os.path.exists(OLD_MEMORY_FILE):
        print(f"⚠️ No existing memory file found at {OLD_MEMORY_FILE}. Nothing to migrate.")
        return

    try:
        with open(OLD_MEMORY_FILE, "r") as f:
            old_data = json.load(f)
            
        print(f"  Found {len(old_data)} entries to migrate.")
        
        dreams = []
        vectors = []
        
        for entry in old_data:
            dream_id = str(uuid.uuid4())
            
            # 1. Create Dream Entry (Clean Text)
            dream_entry = {
                "id": dream_id,
                "timestamp": entry.get("dream_timestamp"),
                "log_count": entry.get("analyzed_entries_count"),
                "insights": entry.get("insights")
                # Removed "embedding"
            }
            dreams.append(dream_entry)
            
            # 2. Create Vector Entry (Machine Data)
            # Only if embedding exists
            if "embedding" in entry and entry["embedding"]:
                vector_entry = {
                    "dream_id": dream_id,
                    "embedding": entry["embedding"]
                }
                vectors.append(vector_entry)
        
        # Save New Files
        print(f"  Saving {len(dreams)} text dreams to {NEW_DREAMS_FILE}...")
        with open(NEW_DREAMS_FILE, "w") as f:
            json.dump(dreams, f, indent=2)
            
        print(f"  Saving {len(vectors)} vectors to {NEW_VECTORS_FILE}...")
        with open(NEW_VECTORS_FILE, "w") as f:
            json.dump(vectors, f, indent=2)
            
        print("✅ Migration Complete!")
        print("  (Note: Original file has been kept as backup)")

    except Exception as e:
        print(f"❌ Migration Failed: {e}")

if __name__ == "__main__":
    migrate()
