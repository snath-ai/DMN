import os
import json
import requests
import datetime
import time
import uuid

# Configuration
OLLAMA_URL_GENERATE = "http://localhost:11434/api/generate"
OLLAMA_URL_EMBED = "http://localhost:11434/api/embeddings"
DEFAULT_MODEL = "llama3" # Can be overriden or auto-detected
LOG_FILE = os.path.join("logs", "interaction_stream.jsonl")
DEFAULT_MODEL = "llama3" # Can be overriden or auto-detected
LOG_FILE = os.path.join("logs", "interaction_stream.jsonl")
OLD_MEMORY_FILE = os.path.join("memory", "long_term_insights.json")
DREAMS_FILE = os.path.join("memory", "dreams.json")
VECTORS_FILE = os.path.join("memory", "dream_vectors.json")
MAX_LOG_ENTRIES = 50
MAX_LOG_ENTRIES = 50

def read_recent_logs(n=50):
    """
    Reads the last n entries from the log file.
    """
    if not os.path.exists(LOG_FILE):
        print(f"⚠️ [DMN] No logs found at {LOG_FILE}.")
        return []

    try:
        with open(LOG_FILE, "r") as f:
            # Simple approach: read all lines and take last n
            # For massive logs, we'd use seek() from the end.
            lines = f.readlines()
            return [json.loads(line) for line in lines[-n:]]
    except Exception as e:
        print(f"❌ [DMN] Error reading logs: {e}")
        return []

def get_embedding(text: str, model: str = DEFAULT_MODEL) -> list:
    """
    Generates a vector embedding for the given text using Ollama.
    """
    try:
        response = requests.post(
            OLLAMA_URL_EMBED,
            json={
                "model": model,
                "prompt": text
            }
        )
        if response.status_code == 200:
            return response.json().get("embedding", [])
        else:
            print(f"⚠️ [DMN] Embed failed: {response.text}")
            return []
    except Exception as e:
        print(f"⚠️ [DMN] Embed Error: {e}")
        return []

def save_insight_split(dream_data, embedding_data):
    """
    Saves dream text to dreams.json and vector to dream_vectors.json
    """
    memory_dir = os.path.dirname(DREAMS_FILE)
    if not os.path.exists(memory_dir):
        os.makedirs(memory_dir)

    # 1. Save Text Dream
    dreams = []
    if os.path.exists(DREAMS_FILE):
        try:
            with open(DREAMS_FILE, "r") as f:
                content = f.read()
                if content.strip():
                    dreams = json.loads(content)
        except: pass
    
    dreams.append(dream_data)
    with open(DREAMS_FILE, "w") as f:
        json.dump(dreams, f, indent=2)
        
    # 2. Save Vector
    if embedding_data:
        vectors = []
        if os.path.exists(VECTORS_FILE):
             try:
                with open(VECTORS_FILE, "r") as f:
                    content = f.read()
                    if content.strip():
                        vectors = json.loads(content)
             except: pass
        
        vectors.append(embedding_data)
        with open(VECTORS_FILE, "w") as f:
             json.dump(vectors, f, indent=2)

    print(f"💾 [DMN] Split Dream saved (ID: {dream_data['id']})")

def save_insight(insight_data):
    # Backward compatibility wrapper or simple deprecation
    # We now expect insight_data to be the FULL packet which we will split here
    # But to minimize refactor risk in 'verify' scripts, we can just adapt:
    
    # Generate ID if missing
    dream_id = str(uuid.uuid4())
    
    dream_entry = {
         "id": dream_id,
         "timestamp": insight_data.get("dream_timestamp"),
         "analyzed_entries_count": insight_data.get("analyzed_entries_count"),
         "insights": insight_data.get("insights")
    }
    
    vector_entry = None
    if "embedding" in insight_data:
         vector_entry = {
             "dream_id": dream_id,
             "embedding": insight_data["embedding"]
         }
         
    save_insight_split(dream_entry, vector_entry)

def dream(model="llama3:latest"):
    """
    The core dreaming process.
    1. Read recent logs.
    2. Reflect using Ollama.
    3. Save insights.
    """
    print(f"🌙 [DMN] Entering sleep mode... Reading logs...")
    recent_logs = read_recent_logs(MAX_LOG_ENTRIES)
    
    if not recent_logs:
        print("💤 [DMN] No recent experiences to process. Sleeping.")
        return

    print(f"🧠 [DMN] Reflecting on {len(recent_logs)} interactions...")
    
    # Prepare the prompt
    logs_str = json.dumps(recent_logs, indent=2)
    system_prompt = (
        "You are the subconscious processing unit. Analyze these recent user interactions. "
        "Do not summarize them. Instead, identify 3 hidden patterns, contradictions, or unasked questions "
        "that the user might be exploring. Output ONLY a JSON object with a list of 'insights'."
    )
    
    full_prompt = f"{system_prompt}\n\nLogs:\n{logs_str}\n\nOutput JSON:"

    try:
        response = requests.post(
            OLLAMA_URL_GENERATE,
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "format": "json" # Force JSON mode if supported by model/ollama version
            }
        )
        response.raise_for_status()
        result = response.json()
        raw_output = result.get("response", "")
        
        # Parse the output
        try:
            insights_json = json.loads(raw_output)
        except json.JSONDecodeError:
             print("⚠️ [DMN] LLM output was not valid JSON. Attempting cleanup...")
             # Basic cleanup attempt (strip markdown fences)
             cleaned = raw_output.replace("```json", "").replace("```", "").strip()
             try:
                 insights_json = json.loads(cleaned)
             except:
                 print(f"❌ [DMN] Failed to parse insights: {raw_output}")
                 return

        # Structure the final memory entry
        
        # 1. Flatten insights to a string for embedding
        # We want to search by meeting, so we embed the combined text of patterns
        insight_text_block = ""
        if isinstance(insights_json, list):
            for item in insights_json:
                if isinstance(item, dict):
                    # Join all values
                    vals = [str(v) for k,v in item.items() if v]
                    insight_text_block += " ".join(vals) + ". "
                else:
                    insight_text_block += str(item) + ". "
        elif isinstance(insights_json, dict) and "insights" in insights_json:
             # Handle nested structure common with some models
             for item in insights_json["insights"]:
                 if isinstance(item, dict):
                    vals = [str(v) for k,v in item.items() if v]
                    insight_text_block += " ".join(vals) + ". "
        else:
            insight_text_block = str(insights_json)

        # 2. Generate Embedding
        print(f"🧬 [DMN] Generating embedding for insights...")
        embedding = get_embedding(insight_text_block, model)

        memory_entry = {
            "dream_timestamp": datetime.datetime.now().isoformat(),
            "analyzed_entries_count": len(recent_logs),
            "insights": insights_json,
            "embedding": embedding # NEW: Vector Storage
        }
        
        save_insight(memory_entry)

    except requests.exceptions.ConnectionError:
        print(f"❌ [DMN] Could not connect to Ollama at {OLLAMA_URL_GENERATE}. Is it running?")
    except Exception as e:
        print(f"❌ [DMN] Error during dreaming: {e}")

if __name__ == "__main__":
    # Allow model override via env var
    target_model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
    dream(model=target_model)
