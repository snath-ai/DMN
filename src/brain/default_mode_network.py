import os
import json
import requests
import datetime
import time
import uuid
# Add Hippocampus import
try:
    from brain.hippocampus import Hippocampus
except ImportError:
    Hippocampus = None

# Configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL_GENERATE = f"{OLLAMA_HOST}/api/generate"
OLLAMA_URL_EMBED = f"{OLLAMA_HOST}/api/embeddings"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

class DefaultModeNetwork:
    """
    The Default Mode Network (DMN):
    Active during 'resting states'. It processes recent experiences (logs),
    reflects on them using the LLM, and consolidates them into long-term memory
    (Dreams and Vectors).
    """

    def __init__(self, logs_path=None, memory_dir=None):
        # Allow override or use env vars, fallback to defaults
        self.logs_path = logs_path or os.environ.get("LOG_FILE", "logs/interaction_stream.jsonl")
        
        # Determine memory files relative to MEMORY_FILE or default
        env_memory = os.environ.get("MEMORY_FILE")
        if env_memory:
            self.dreams_path = env_memory
            base_dir = os.path.dirname(env_memory)
            self.vectors_path = os.path.join(base_dir, "dream_vectors.json")
        else:
             base_dir = memory_dir or "memory"
             self.dreams_path = os.path.join(base_dir, "dreams.json")
             self.vectors_path = os.path.join(base_dir, "dream_vectors.json")

        self.max_log_entries = 50
        
        # Initialize Unified Brain
        if Hippocampus:
            self.hippocampus = Hippocampus(dreams_path=self.dreams_path)
        else:
            self.hippocampus = None

    def _read_recent_logs(self, n=50):
        if not os.path.exists(self.logs_path):
            print(f"⚠️ [DMN] No logs found at {self.logs_path}.")
            return []
        try:
            with open(self.logs_path, "r") as f:
                lines = f.readlines()
                return [json.loads(line) for line in lines[-n:]]
        except Exception as e:
            print(f"❌ [DMN] Error reading logs: {e}")
            return []

    def _get_embedding(self, text: str) -> list:
        try:
            # Always use a consistent embedding model across all services to prevent dimension mismatch
            embed_model = "llama3.2"
            response = requests.post(
                OLLAMA_URL_EMBED,
                json={"model": embed_model, "prompt": text}
            )
            if response.status_code == 200:
                return response.json().get("embedding", [])
            else:
                print(f"⚠️ [DMN] Embed failed: {response.text}")
                return []
        except Exception as e:
            print(f"⚠️ [DMN] Embed Error: {e}")
            return []

    def _save_dream(self, dream_data, embedding_data):
        # 1. Save Text Dream
        dreams = []
        if os.path.exists(self.dreams_path):
            try:
                with open(self.dreams_path, "r") as f:
                    content = f.read()
                    if content.strip():
                        dreams = json.loads(content)
            except Exception as e:
                print(f"Error parsing existing dream content: {e}")
        
        dreams.append(dream_data)
        os.makedirs(os.path.dirname(self.dreams_path), exist_ok=True)
        with open(self.dreams_path, "w") as f:
            json.dump(dreams, f, indent=2)
            
        # 2. Save Vector
        if embedding_data:
            vectors = []
            if os.path.exists(self.vectors_path):
                 try:
                    with open(self.vectors_path, "r") as f:
                        content = f.read()
                        if content.strip():
                            vectors = json.loads(content)
                 except Exception as e:
                     print(f"Error parsing existing vector content: {e}")
            
            vectors.append(embedding_data)
            with open(self.vectors_path, "w") as f:
                 json.dump(vectors, f, indent=2)

        print(f"💾 [DMN] Insight consolidated into Long-Term Memory (ID: {dream_data['id']})")

    def activate(self):
        """
        Triggers the dreaming process.
        """
        print(f"🌙 [DMN] Calculating Resting State Connectivity...")
        recent_logs = self._read_recent_logs(self.max_log_entries)
        
        if not recent_logs:
            print("💤 [DMN] No recent partial memories to consolidate. Sleeping.")
            return

        print(f"🧠 [DMN] Consolidating {len(recent_logs)} recent episodes...")
        
        # --- MODEL SWITCHER SUPPORT ---
        current_model = DEFAULT_MODEL
        try:
             config_path = "/data/model_config.json"
             if os.path.exists(config_path):
                 with open(config_path, "r") as f:
                     cfg = json.load(f)
                     current_model = cfg.get("subconscious_model", DEFAULT_MODEL)
                     print(f"🧠 [DMN] Using user-selected model: {current_model}")
        except Exception as e:
             print(f"⚠️ [DMN] Config Load Error: {e}")

        # Prepare the prompt
        # SANITIZATION: Convert JSON logs to a plain text transcript to prevent LLM from mimicking JSON structure.
        conversation_text = ""
        for log in recent_logs:
            timestamp = log.get("timestamp", "")
            role = log.get("role", "unknown")
            content = log.get("content", "")
            conversation_text += f"[{timestamp}] {role}: {content}\n"

        system_prompt = (
        "TASK: EXTRACT SEMANTIC INSIGHT.\n"
        "INSTRUCTION: Read the chat transcript below and extract the core topics, facts, and emotional shifts into a single, dense paragraph.\n"
        "RULES:\n"
        "1. Write strictly in the third person (e.g., 'The user discussed...', 'The agent noted...').\n"
        "2. Output ONLY the summary paragraph. No headings. No intro. No 'FINAL OUTPUT'. No 'CONCLUSION'.\n"
        "3. Do not act as a conversational bot. You are a silent synthesis engine.\n"
        "4. Keep it concise, omitting trivial pleasantries.\n"
    )    
        # Use clear separators to prevent chat completion
        full_prompt = f"{system_prompt}\n\n[TRANSCRIPT START]\n{conversation_text}\n[TRANSCRIPT END]\n\nSYNTHESIS:"

        # Debug Logging
        try:
            with open("logs/dmn_prompts.log", "a") as f:
                f.write(f"\n\n--- [TIMESTAMP] ---\nPrompt:\n{full_prompt}\n")
        except Exception as e:
             print(f"Error logging prompt: {e}")

        try:
            response = requests.post(
                OLLAMA_URL_GENERATE,
                json={
                    "model": current_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "" # Disable JSON mode
                }
            )
            response.raise_for_status()
            result = response.json()
            raw_output = result.get("response", "").strip()

            # Debug Response
            try:
                with open("logs/dmn_prompts.log", "a") as f:
                    f.write(f"Response:\n{raw_output}\n-------------------\n")
            except Exception as e:
                 print(f"Error logging response: {e}")
            
            # Manually wrap in JSON structure for consistency with storage
            # Fallback if empty
            if not raw_output:
                raw_output = "The mind is silent. (Analysis failed generated empty response)"

            insights_json = {
                "narrative": raw_output
            }

            # Flatten for embedding
            insight_text_block = raw_output

            print(f"🧬 [DMN] Generating synaptic weights (Embeddings)...")
            embedding = self._get_embedding(insight_text_block)

            # Generate ID
            dream_id = str(uuid.uuid4())
            ts = datetime.datetime.now().isoformat()
            
            # --- SAVE MEMORY (Hybrid: Chroma + JSON) ---
            if self.hippocampus:
                print(f"💾 [DMN] Saving to Vector Brain (Hippocampus Cold Storage)...")
                metadata = {
                    "source": "dreamer", 
                    "timestamp": ts,
                    "log_count": len(recent_logs),
                    "type": "dream_insight" 
                }
                self.hippocampus.save_memory(
                    text=insight_text_block,
                    embedding=embedding,
                    metadata=metadata
                )
                
                # --- SECONDARY COMPRESSION PASS (Warm Memory) ---
                print(f"🧠 [DMN] Performing secondary compression for PFC integration...")
                warm_prompt = f"Synthesize this dream into a single dense summary sentence focusing on meaning and strategy: {insight_text_block}"
                
                try:
                    warm_res = requests.post(
                        OLLAMA_URL_GENERATE,
                        json={
                            "model": current_model,
                            "prompt": warm_prompt,
                            "stream": False,
                            "format": ""
                        }
                    )
                    warm_res.raise_for_status()
                    warm_output = warm_res.json().get("response", "").strip()
                    
                    if warm_output:
                        warm_emb = self._get_embedding(warm_output)
                        self.hippocampus.save_warm_memory(
                            text=warm_output,
                            embedding=warm_emb,
                            metadata={"timestamp": ts, "type": "warm_summary", "source": "dreamer_compression"}
                        )
                except Exception as we:
                    print(f"⚠️ [DMN] Warm Memory Compression Warning: {we}")
                    
            else:
                # Legacy Fallback
                print(f"💾 [DMN] Saving to Legacy JSON (No Hippocampus)...")
                dream_entry = {
                    "id": dream_id,
                    "timestamp": ts,
                    "log_count": len(recent_logs),
                    "insights": insights_json
                }
                vector_entry = {"dream_id": dream_id, "embedding": embedding}
                self._save_dream(dream_entry, vector_entry)

        except Exception as e:
            print(f"❌ [DMN] Consolidation Error: {e}")

# Test
if __name__ == "__main__":
    dmn = DefaultModeNetwork()
