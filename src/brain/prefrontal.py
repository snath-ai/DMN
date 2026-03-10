import os
import requests
from typing import Dict, Any

from lar.node import BaseNode, GraphState
from .hippocampus import Hippocampus

# Configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL_GENERATE = f"{OLLAMA_HOST}/api/generate"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
if "/" not in DEFAULT_MODEL and not DEFAULT_MODEL.startswith("gpt"):
    DEFAULT_MODEL = f"ollama/{DEFAULT_MODEL}"

class PrefrontalNode(BaseNode):
    """
    The Prefrontal Cortex (PFC) Layer.
    Acts as a gating and compression mechanism between Hippocampal retrieval and the Working Memory (Context Window).
    Solves KV Cache bloat by compressing 2000+ tokens of raw chunks into a dense ~100 token synthesis.
    """
    
    def __init__(self, hippocampus: Hippocampus, name: str = "PrefrontalNode"):
        self.hippocampus = hippocampus
        self.model_name = DEFAULT_MODEL
        
    def execute(self, state: GraphState) -> GraphState:
        query = state.get("user_input", "")
        if not query:
            return state
            
        print(f"🧠 [Prefrontal Cortex] Filtering memories for '{query}'...")
        
        # 1. Retrieve Cold Memory (Raw Chunks) - Top 10
        cold_chunks = self.hippocampus.recall(query=query, max_memories=10)
        
        # 2. Retrieve Warm Memory (Semantic Summaries) - Top 3
        warm_summaries = self.hippocampus.recall_warm(query=query, max_memories=3)
        
        if not cold_chunks and not warm_summaries:
            state.set("compressed_memory", "")
            return state
            
        # 3. Run Compression Prompt
        prompt = f"""
Current agent query: {query}

Retrieved memory chunks (Cold):
{cold_chunks}

Existing semantic summaries (Warm):
{warm_summaries}

Your task:
Synthesize ONLY what is directly relevant to the current query into a single coherent paragraph of maximum 100 words.
Discard anything not immediately relevant. Be ruthless with compression.
Preserve meaning over detail.
Output ONLY the synthesis. No preamble.
"""
        
        try:
            # Strip LiteLLM prefixes for direct Ollama API calls
            api_model = self.model_name.replace("ollama/", "").replace("gemini/", "")
            
            response = requests.post(
                OLLAMA_URL_GENERATE,
                json={
                    "model": api_model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            synthesis = result.get("response", "").strip()
            
            print(f"🧬 [Prefrontal Cortex] Compressed memory footprint to ~{len(synthesis.split())} words.")
            state.set("compressed_memory", synthesis)
            
        except Exception as e:
            print(f"⚠️ [Prefrontal Cortex] Compression failed, bypassing: {e}")
            # Fallback to empty context if compression fails so we don't crash or bloat the context window
            state.set("compressed_memory", "")
            
        return state
