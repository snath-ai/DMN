<p align="center">
  <img src="https://raw.githubusercontent.com/snath-ai/.github/main/assets/lar-logo.png" width="80" alt="Lár Logo" />
</p>
<p align="center"><em>Lár DMN — The Memory Layer for the Snath AI Cognitive Architecture</em></p>
<p align="center">
  <a href="https://github.com/snath-ai/lar">
    <img alt="Based on" src="https://img.shields.io/badge/Spine-Lár%20Engine%20v2.1.0-blue?style=for-the-badge">
  </a>
  <a href="https://github.com/snath-ai/DMN">
    <img alt="Architecture" src="https://img.shields.io/badge/Architecture-Bicameral%20Mind-blueviolet?style=for-the-badge">
  </a>
  <a href="https://doi.org/10.5281/zenodo.18175178">
    <img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18175178-blue?style=for-the-badge" alt="DOI">
  </a>
</p>

# Lár DMN — Solving Catastrophic Forgetting Without Retraining

Every AI agent forgets everything the moment it stops running. Context windows fill up, old messages get silently truncated, and the agent permanently loses knowledge of past interactions. Talk to any chatbot for two hours — it forgets the first hour.

**DMN solves this architecturally.** No weight updates. No continual learning. No retraining. The base LLM stays frozen. Memory is treated as an infrastructure problem, not a model problem — the same way a database solves persistence without touching application code.

While the agent is active, it runs normally on Lár. When the user goes idle, a background daemon activates — reads the recent interaction logs, synthesizes them into compressed semantic narratives, and writes them to a tiered vector store. When the user returns, those memories are retrieved and injected as context. The agent picks up where it left off, across sessions, indefinitely.

---

## Part of a Larger System

DMN is the memory layer of a three-part cognitive architecture. Each part is independent but designed to compose:

| Repository | Role |
| :--- | :--- |
| **[Lár](https://github.com/snath-ai/lar)** | The execution spine — deterministic graph engine, audit logging, EU AI Act compliance |
| **[Lár DMN](https://github.com/snath-ai/DMN)** ← you are here | The memory layer — solves catastrophic forgetting with sleep/dream consolidation |
| **[Lár-JEPA](https://github.com/snath-ai/Lar-JEPA)** | The world model — routes LLMs, JEPAs, and any future architecture as first-class nodes |

The industry is building the Brain (LLMs, JEPAs). We are building the Nervous System.

---

## The Human Analogy

Human brains don't rewrite neural weights every night. The **Hippocampus** consolidates the day's experiences into long-term cortical storage during sleep. You don't remember every pixel of your morning commute — you remember it rained and traffic was bad. Raw sensory data is gone; the meaning persists.

DMN implements this exact strategy as software:

| Human Brain | Lár DMN |
|---|---|
| Sensory Input | User Messages (Raw Logs) |
| Hippocampal Consolidation (Sleep) | Dreamer Daemon (Idle Trigger) |
| Long-Term Cortical Storage | ChromaDB (Warm + Cold Tiers) |
| Prefrontal Filtering (Attention) | PrefrontalNode (Compression Gateway) |
| Working Memory | Hot Memory (Last 5 Turns) |

---

## Architecture

The system runs as two separate processes — a Conscious mind (active chat) and a Subconscious mind (background consolidation).

```mermaid
graph TD
    User -->|Chat| Thalamus
    Thalamus -->|Feeling| Amygdala
    
    subgraph Working Memory [Hot Memory]
        Thalamus -->|Context| Cortex(LLMNode)
    end
    
    subgraph Deep Memory [Warm & Cold Memory]
        Thalamus -->|Query| PFC[Prefrontal Cortex]
        Hippo[(Hippocampus<br>ChromaDB)] -.->|Cold: Raw Chunks| PFC
        Hippo -.->|Warm: Semantic Summaries| PFC
        PFC -->|Compressed Synthesis| Cortex
    end
    
    Cortex -->|Response| User
    
    subgraph DMN [Default Mode Network]
        Cortex -.->|Logs| STM[Short Term Memory]
        STM -->|Idle Trigger 30s| Dreamer(lar-dreamer)
        Dreamer -->|Pass 1: Cold Consolidation| Hippo
        Dreamer -->|Pass 2: Warm Compression| Hippo
    end
```

### The Thalamus
Input router and prompt engineer. Constructs a dynamic system prompt each turn from three sources: the user's message, an emotional state from the Amygdala, and relevant memories from the Hippocampus. Implements a "Wake Up Protocol" — if the agent has been sleeping, it injects the last dream into context so the agent resumes with continuity.

### The Amygdala
A lightweight state machine simulating emotional valence and arousal. Analyzes user sentiment and injects a mood modifier into the system prompt. Prevents the flat affect typical of AI assistants.

### The Dreamer (DMN Daemon)
A background process monitoring the short-term memory logs. Activates after 30 seconds of idle time. Runs two consolidation passes: raw vector storage (Cold) and semantic narrative synthesis (Warm). Uses a high-reasoning model for dreaming where latency doesn't matter — insight quality does.

### The Hippocampus
Hybrid vector store using ChromaDB with two collections: `long_term_memory` (raw Cold chunks) and `warm_memory` (compressed Warm summaries, capped at 500 entries).

### The Prefrontal Cortex
Solves KV cache bloat. Rather than injecting raw retrieved chunks directly into the prompt, the PFC synthesises retrieved memories into a single ≤100 word summary. Only meaning enters the context window — not raw tokens.

---

## 3-Tier Memory

| Tier | Contents | Injection |
|:---|:---|:---|
| **Hot** | Last 5 interactions | Verbatim — immediate conversational flow |
| **Warm** | Compressed semantic summaries from sleep | Via PFC — synthesised before injection |
| **Cold** | Raw chronological logs and narrative dreams | Via PFC only — never injected directly |

---

## JEPA Integration — World Model Memories

DMN is not limited to LLM conversations. **Lár-JEPA writes JEPA trajectory heuristics directly into the Hippocampus** via `JEPA_DMN_Consolidation_Node`.
*(Note: Thanks to the newly integrated `TensorSafeEncoder` in the Lár core engine, raw PyTorch and NumPy tensors from JEPAs are now safely serialized and consolidated into the DMN without crashing the graph state.)*

The pattern: after a JEPA world model predicts a trajectory and the `EntropicRouter` returns `COMMIT_TRAJECTORY`, the successful execution trace is written to the DMN episodic store. On the next planning cycle, `recall_heuristics()` retrieves it as warm context — the JEPA doesn't re-explore known-good regions of latent space.

```python
from dmn_integration.consolidation_node import JEPA_DMN_Consolidation_Node

bridge = JEPA_DMN_Consolidation_Node(chroma_path="data/chroma_db")

# After COMMIT_TRAJECTORY
bridge.write_trajectory_heuristic({
    "domain": "spatial_kinematics",
    "action": action_vector,
    "entropic_loss": 0.049,
    "outcome": "committed",
})

# At the start of the next planning cycle
prior_heuristics = bridge.recall_heuristics("orbital insertion n-body")
# → "[JEPA Heuristic] Domain: spatial_kinematics | Outcome: committed | ..."
```

Gracefully degrades if ChromaDB or Ollama are unavailable — JEPA execution is never blocked by DMN availability. See [`Lár-JEPA → examples/jepa_dmn_showcase.py`](https://github.com/snath-ai/Lar-JEPA/blob/main/examples/jepa_dmn_showcase.py) for the full running demo.

---

## Quick Start

```bash
git clone https://github.com/snath-ai/DMN
cd DMN/lar
docker-compose up --build -d
# Open http://localhost:8501
```

**Prerequisites:** Docker Desktop, Ollama running locally (or cloud API keys).

### What to expect

1. **Wake Phase** — Chat normally. The Amygdala scores sentiment live. Hot memory keeps the last 5 turns in context.
2. **Sleep Phase** — Go idle for 30 seconds. The UI shows `💤 Brain Sleeping / Dreaming`. The `lar-dreamer` container activates.
3. **Dream Phase** — The Dreamer runs two consolidation passes. Watch it live: `docker logs -f lar-dreamer`
4. **Recall Phase** — Return and ask about a past topic. The PFC retrieves and compresses relevant memories before they hit the prompt.
5. **Model Switching** — Swap the Conscious (fast) and Subconscious (reasoning) models on the fly from the Neural Configuration sidebar. Embeddings stay pinned to `llama3.2` to prevent memory corruption.
6. **Wipe Brain** — `🧹 Wipe Brain` clears all logs and ChromaDB collections for a clean slate.

---

## License

Apache 2.0. Built on the [Lár Engine](https://github.com/snath-ai/lar).
