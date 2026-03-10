import os
import json
from collections import deque

class MemoryTiers:
    """
    Manages the translation of interactions across the Three-Tier Memory System.
    TIER 1 (Hot): Rolling buffer of immediate context.
    TIER 2 (Warm): Handled by ChromaDB / PrefrontalNode.
    TIER 3 (Cold): Handled by ChromaDB / PrefrontalNode.
    """
    
    def __init__(self, hot_memory_size=5):
        self.hot_memory_size = hot_memory_size
    
    def get_hot_memory(self, stream_log_path: str) -> str:
        """
        Retrieves the last N interactions from the Consciousness Stream logic.
        Limits to roughly 200 tokens (we enforce this via character limit approx).
        """
        if not os.path.exists(stream_log_path):
            return ""
            
        try:
            with open(stream_log_path, "r") as f:
                lines = f.readlines()
            
            recent = []
            # We take the last `hot_memory_size` lines
            for line in lines[-self.hot_memory_size:]:
                try:
                    data = json.loads(line)
                    role = data.get("role", "unknown")
                    content = data.get("content", "")
                    recent.append(f"{role}: {content}")
                except:
                    pass
            
            # Simple text truncation to approximate 200 tokens (~800 chars)
            # if we wanted strict tokenization, we'd use tiktoken, but char limit is fast and deterministic.
            raw_text = "\\n".join(recent)
            if len(raw_text) > 800:
                return "...[truncated context]..." + raw_text[-750:]
            return raw_text
            
        except Exception as e:
            print(f"⚠️ [MemoryTiers] Failed to fetch Hot Memory: {e}")
            return ""
