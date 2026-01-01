import os
import json
import math
import requests
from typing import List, Optional

# Path to the memory files
# We assume it is running from the root of the repo mostly, but let's make it robust.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Relative to src/lar/ we want ../../memory
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

# Fallbacks for different running contexts
DREAMS_FILE = os.path.join(PROJECT_ROOT, "memory", "dreams.json")
VECTORS_FILE = os.path.join(PROJECT_ROOT, "memory", "dream_vectors.json")

# Fallback to local if project root logic fails (simple script run)
if not os.path.exists(os.path.dirname(DREAMS_FILE)):
    DREAMS_FILE = os.path.join("memory", "dreams.json") 
    VECTORS_FILE = os.path.join("memory", "dream_vectors.json")
OLLAMA_URL_EMBED = "http://localhost:11434/api/embeddings"
DEFAULT_MODEL = "llama3"

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude_v1 = math.sqrt(sum(a * a for a in v1))
    magnitude_v2 = math.sqrt(sum(b * b for b in v2))
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 0.0
    return dot_product / (magnitude_v1 * magnitude_v2)

def get_embedding(text: str, model: str = DEFAULT_MODEL) -> List[float]:
    """Generates embedding for query text."""
    try:
        response = requests.post(
            OLLAMA_URL_EMBED,
            json={"model": model, "prompt": text}
        )
        if response.status_code == 200:
            return response.json().get("embedding", [])
        return []
    except:
        return []

def get_subconscious_context(max_insights: int = 3, memory_path: str = None, query: str = None) -> str:
    """
    Retrieves insights from DMN memory.
    If 'query' is provided, performs Semantic Search.
    Otherwise, returns most recent insights.
    
    Args:
        max_insights (int): Number of insights to retrieve.
        memory_path (str, optional): Override path to memory file.
        query (str, optional): Text to match against memories.
    
    Returns:
        str: A formatted string of insights.
    """
    memory_path = memory_path or DREAMS_FILE # Default to text file
    vector_path = VECTORS_FILE

    if not os.path.exists(memory_path):
        return ""

    try:
        # Load Dreams (Text)
        with open(memory_path, "r") as f:
            dreams_data = json.load(f)
            
        if not dreams_data or not isinstance(dreams_data, list):
            return ""

        selected_dreams = []
        
        # --- Semantic Search ---
        if query and os.path.exists(vector_path):
            query_embedding = get_embedding(query)
            if query_embedding:
                try:
                    with open(vector_path, "r") as f:
                        vectors_data = json.load(f)
                    
                    if vectors_data and isinstance(vectors_data, list):
                        scored_memories = []
                        for vec_entry in vectors_data:
                            if "embedding" in vec_entry and vec_entry["embedding"]:
                                score = cosine_similarity(query_embedding, vec_entry["embedding"])
                                scored_memories.append((score, vec_entry["dream_id"]))
                        
                        # Sort by score descending
                        scored_memories.sort(key=lambda x: x[0], reverse=True)
                        
                        # Take top K IDs
                        top_ids = [m[1] for m in scored_memories[:max_insights]]
                        
                        # Fetch the actual dreams
                        # Optimization: Create a lookup map if list is long. For now, simple scan.
                        for dream_id in top_ids:
                             matches = [d for d in dreams_data if d.get("id") == dream_id]
                             selected_dreams.extend(matches)
                             
                        if selected_dreams:
                            print(f"🧠 [Hippocampus] Semantic Recall: Found {len(selected_dreams)} relevant memories (Split store).")
                except Exception as e:
                    print(f"⚠️ [Hippocampus] Vector search failed: {e}")

        # --- Fallback to Recent ---
        if not selected_dreams:
            # Get last N entries from DREAMS file if no query or no semantic matches found
            selected_dreams = dreams_data[-max_insights:]
        
        insight_texts = []
        for mem in selected_dreams:
            # Check structure (it might be nested {"insights": [...]})
            if "insights" in mem:
                payload = mem["insights"]
                if isinstance(payload, dict) and "insights" in payload:
                     # Handle {"insights": {"insights": [...]}} double nesting or just {"insights": [...]}
                     items = payload["insights"]
                elif isinstance(payload, list):
                     items = payload
                else:
                    items = []

                for item in items:
                    if isinstance(item, dict):
                        # Enhanced Parsing (Robust to LLM variations)
                        label = None
                        text = None
                        
                        # Check for common keys
                        for key in ["pattern", "hidden_pattern", "contradiction", "unasked_question", "insight"]:
                            if key in item and item[key]:
                                label = key.replace("_", " ").title()
                                text = item[key]
                                break
                        
                        if text:
                            insight_texts.append(f"- {label}: {text}")
                        else:
                            # Fallback: dump values
                            vals = [str(v) for k,v in item.items() if v and k != "type"]
                            if vals:
                                insight_texts.append(f"- {'; '.join(vals)}")

                    elif isinstance(item, str):
                        insight_texts.append(f"- {item}")

        if not insight_texts:
            return ""

        # Format solely the list
        return "\n".join(insight_texts)

    except Exception as e:
        # Fail silently to avoid crashing the conscious mind
        # print(f"Error reading memory: {e}") 
        return ""
