import os
import json
import uuid
import chromadb
from chromadb.config import Settings
from typing import List, Optional

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

DREAMS_FILE = os.path.join(PROJECT_ROOT, "memory", "dreams.json")
# Vectors file is legacy, but we keep the path calc for backward compat if needed
VECTORS_FILE = os.path.join(PROJECT_ROOT, "memory", "dream_vectors.json") 
CHROMA_DB_DIR = os.path.join(PROJECT_ROOT, "data", "chroma_db")

# Ollama Config
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

class Hippocampus:
    """
    The Hippocampus: Responsible for long-term memory formation and retrieval.
    It consolidates recent experiences into long-term storage (ChromaDB + JSON Journal)
    and retrieves relevant memories based on context (Semantic Search).
    """

    def __init__(self, dreams_path=None, chroma_path=None):
        # Support environment mapping (Docker)
        env_memory = os.environ.get("MEMORY_FILE")
        if env_memory:
            self.dreams_path = dreams_path or env_memory
            base_dir = os.path.dirname(self.dreams_path)
            self.chroma_path = chroma_path or os.path.join(base_dir, "chroma_db")
        else:
             self.dreams_path = dreams_path or DREAMS_FILE
             self.chroma_path = chroma_path or CHROMA_DB_DIR
        
        # Ensure fallback for simple script execution
        if not os.path.exists(os.path.dirname(self.dreams_path)):
             os.makedirs(os.path.dirname(self.dreams_path), exist_ok=True)

        # Initialize ChromaDB
        print(f"🧠 [Hippocampus] Connecting to ChromaDB at {self.chroma_path}...")
        try:
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(name="long_term_memory")
        except Exception as e:
            print(f"❌ [Hippocampus] ChromaDB Init Error: {e}")
            self.collection = None

    def save_memory(self, text: str, embedding: List[float], metadata: dict = None):
        """
        Saves a memory to both the Vector DB (for search) and the JSON Journal (for narrative history).
        """
        if not text: return

        memory_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata["timestamp"] = metadata.get("timestamp", "")
        
        # 1. Save to ChromaDB (Associative)
        if self.collection:
            try:
                self.collection.add(
                    documents=[text],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[memory_id]
                )
            except Exception as e:
                print(f"❌ [Hippocampus] Vector Save Error: {e}")

        # 2. Save to JSON Journal (Narrative/Chronological)
        # We append to the existing list
        journal_entry = {
            "id": memory_id,
            "timestamp": metadata.get("timestamp"),
            "content": text,
            "metadata": metadata
        }
        
        journal_data = []
        if os.path.exists(self.dreams_path):
            try:
                with open(self.dreams_path, "r") as f:
                    journal_data = json.load(f)
            except: pass
        
        journal_data.append(journal_entry)
        
        with open(self.dreams_path, "w") as f:
            json.dump(journal_data, f, indent=2)
            
        print(f"💾 [Hippocampus] Memory consolidated (ID: {memory_id})")

    def get_latest_dream(self) -> str:
        """Retrieves the most recent dream from the JSON Journal."""
        if not os.path.exists(self.dreams_path):
            return ""
        try:
            with open(self.dreams_path, "r") as f:
                dreams_data = json.load(f)
            if not dreams_data:
                return ""
            
            # The journal structure has changed slightly in this refactor (content vs insights)
            # We handle backward compatibility or new format
            latest = dreams_data[-1]
            if "content" in latest:
                return latest["content"]
            elif "insights" in latest:
                # Legacy format support
                 return self._format_insights([latest])
            return str(latest)
        except:
            return ""

    def recall(self, query: str = None, max_memories: int = 3) -> str:
        """
        Retrieves context from long-term memory via ChromaDB.
        """
        if not query:
            # Fallback to recency if no query (get last N from JSON)
            return self.get_latest_dream()

        if not self.collection:
            return ""

        try:
            # query_embeddings expects a list of embeddings. 
            # We need to generate embedding for the query first provided by caller? 
            # OR typically we generate it here?
            # Wait, Hippocampus previously relied on self._get_embedding.
            # DMN provides embeddings on save. But Recall needs to generate them too.
            # I removed _get_embedding helper. I should put it back or move it to a Util.
            # Ideally Hippocampus should own embedding generation.
            pass 
            # REVISION: I will re-add _get_embedding method below to support recall.
        except:
             pass
        return "" # Placeholder, logic continues below...

    # Helper re-added for Recall
    def _generate_embedding(self, text):
        import requests
        url = f"{OLLAMA_HOST}/api/embeddings"
        try:
            res = requests.post(url, json={"model": DEFAULT_MODEL, "prompt": text})
            if res.status_code == 200:
                return res.json().get("embedding")
        except: pass
        return None

    def recall(self, query: str = None, max_memories: int = 3) -> str:
        if not query:
             return self.get_latest_dream()

        # Chroma Query
        if self.collection:
            try:
                query_vec = self._generate_embedding(query)
                if not query_vec: return ""
                
                results = self.collection.query(
                    query_embeddings=[query_vec],
                    n_results=max_memories
                )
                
                # Format results
                # Chroma returns {'documents': [[doc1, doc2]], 'ids': ...}
                docs = results.get('documents', [[]])[0]
                if docs:
                    return "\\n".join([f"- {d}" for d in docs])
            except Exception as e:
                print(f"⚠️ [Hippocampus] Recall Error: {e}")
        
        return ""

    # Legacy helper for reading old JSONs if needed
    def _format_insights(self, dreams: list) -> str:
        # ... (Keep existing logic or simplify)
        text = []
        for d in dreams:
            if "insights" in d and "narrative" in d["insights"]:
                 text.append(d["insights"]["narrative"])
        return "\\n".join(text)

# Minimal test
if __name__ == "__main__":
    h = Hippocampus()
    # Simple mock check
    print("Hippocampus initialized.")
