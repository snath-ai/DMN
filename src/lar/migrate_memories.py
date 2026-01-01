import os
import json
import sys
import uuid

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.hippocampus import Hippocampus

def migrate():
    print("🚀 [Migration] Starting Backfill to ChromaDB...")
    
    # Initialize Hippocampus (which inits Chroma)
    hippocampus = Hippocampus()
    
    if not hippocampus.collection:
        print("❌ [Migration] Failed to connect to ChromaDB. Aborting.")
        return

    # Read existing dreams
    dreams_path = hippocampus.dreams_path
    if not os.path.exists(dreams_path):
        print(f"⚠️ [Migration] No dreams.json found at {dreams_path}. Nothing to migrate.")
        return

    try:
        with open(dreams_path, "r") as f:
            dreams = json.load(f)
    except Exception as e:
        print(f"❌ [Migration] JSON Read Error: {e}")
        return

    print(f"📦 [Migration] Found {len(dreams)} memories to migrate.")
    
    count = 0
    for dream in dreams:
        try:
            dream_id = dream.get("id", str(uuid.uuid4()))
            timestamp = dream.get("timestamp", "")
            
            # Extract content
            content = ""
            if "content" in dream:
                content = dream["content"]
            elif "insights" in dream:
                # Legacy format
                # We need to format it to text for embedding
                content = hippocampus._format_insights([dream])
            
            if not content:
                print(f"⚠️ Skipping empty dream {dream_id}")
                continue

            # Generate Embedding (we need to generate it if we don't have it)
            # Do we have vectors.json? 
            # Ideally we re-embed to be safe and consistent with current model.
            print(f"   - Embedding memory {dream_id[:8]}...")
            embedding = hippocampus._generate_embedding(content)
            
            if not embedding:
                print(f"   ⚠️ Failed to embed {dream_id[:8]}")
                continue

            # Add to Chroma
            hippocampus.collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[{
                    "timestamp": timestamp,
                    "source": "migration",
                    "original_id": dream_id
                }],
                ids=[dream_id]
            )
            count += 1
            
        except Exception as e:
            print(f"❌ Error migrating {dream_id}: {e}")

    print(f"✅ [Migration] Complete. {count}/{len(dreams)} memories migrated to ChromaDB.")

if __name__ == "__main__":
    migrate()
