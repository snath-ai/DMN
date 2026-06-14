"""
MemoryTiers — Tier 1 hot buffer for the DefaultModeNetwork conversation memory system.

IMPORTANT: there are two distinct tier systems in Lár DMN.

  Conversation memory tiers  (this file + Hippocampus + PrefrontalNode)
  ─────────────────────────────────────────────────────────────────────
  Tier 1 — Episodic / Hot   : rolling buffer of last N turns (this class)
  Tier 2 — Semantic / Warm  : ChromaDB compressed summaries (Hippocampus.warm_collection)
  Tier 3 — Episodic / Cold  : ChromaDB raw dream episodes   (Hippocampus.collection)

  Domain continual-learning tiers  (AbstractDMN / AbstractAdapterRouter)
  ────────────────────────────────────────────────────────────────────────
  Tier 1 — Episodic   : D-hard JSONL queue  (fast, perishable)
  Tier 2 — Semantic   : signed JSON centroids / ChromaDB  (durable, geometry-stable)
  Tier 3 — Procedural : signed LoRA .pt adapters  (perishable, time-gated by W)

This class only implements the conversation Tier 1 hot buffer.
Tiers 2 and 3 of conversation memory are handled by Hippocampus and PrefrontalNode.
"""

import os
import json


class MemoryTiers:
    """
    Tier 1 hot buffer for DefaultModeNetwork conversation memory.

    Provides a rolling window of the last N interaction turns for
    immediate context injection into the LLM prompt — the fast,
    perishable layer that requires no embedding or retrieval.

    Tier 2 (warm ChromaDB summaries) and Tier 3 (cold ChromaDB episodes)
    are handled by Hippocampus and retrieved via PrefrontalNode.
    """

    def __init__(self, hot_memory_size: int = 5):
        self.hot_memory_size = hot_memory_size

    def get_hot_memory(self, stream_log_path: str) -> str:
        """
        Return the last N turns from the consciousness stream log as plain text.

        Limits output to ~800 characters (~200 tokens) to avoid bloating
        the prompt before Hippocampus warm/cold retrieval is injected.
        """
        if not os.path.exists(stream_log_path):
            return ""

        try:
            with open(stream_log_path, "r") as f:
                lines = f.readlines()

            recent = []
            for line in lines[-self.hot_memory_size:]:
                try:
                    data = json.loads(line)
                    role    = data.get("role", "unknown")
                    content = data.get("content", "")
                    recent.append(f"{role}: {content}")
                except Exception:
                    pass

            raw_text = "\n".join(recent)
            if len(raw_text) > 800:
                return "...[truncated]..." + raw_text[-750:]
            return raw_text

        except Exception as e:
            print(f"[MemoryTiers] Tier 1 read failed: {e}")
            return ""
