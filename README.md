<p align="center">
  <img src="https://raw.githubusercontent.com/snath-ai/.github/main/assets/lar-logo.png" width="80" alt="Lár Logo" />
</p>
<p align="center"><em>Lár: The Bicameral Mind</em></p>
<p align="center">
  <a href="https://github.com/snath-ai/DMN">
    <img alt="Public Showcase" src="https://img.shields.io/badge/Showcase-DMN-blueviolet?style=for-the-badge">
  </a>
   <a href="https://pypi.org/project/lar-engine/">
    <img alt="Powered By" src="https://img.shields.io/badge/Powered%20By-LAR%20Engine-blue?style=for-the-badge">
  </a>
</p>

# Lár: The Default Mode Network (DMN)

> **"The user controls the dream, but the memory is authentic."**

This repository is a **Public Showcase** of the **Default Mode Network (DMN)** implementation using the **Lár Engine**. It demonstrates how to build an AI agent with a "Bicameral Mind"—a distinct separation between Conscious Processing and Subconscious Consolidation.

## 🧠 The Concept

Most AI agents are **stateless execution loops**. They run, they finish, they die.
**Lár is different.** It has a 24/7 background process that mimics the human brain's **Default Mode Network**.

### The Bicameral Architecture

1.  **Thinking Fast (Conscious)**: The "Awake" agent. It talks to you, runs tools, and logs experiences to Short-Term Memory.
2.  **Thinking Slow (Subconscious)**: The "Dreamer" agent. When the user stops interacting, it "wakes up" in the background. It reads recent logs, reflects on them, and consolidates them into Long-Term Memory (Vector DB).

```mermaid
graph TD
    User([User]) <--> Awake[Conscious Agent - 'Awake']
    Awake -->|Writes| STM[Short Term Memory (Logs)]
    
    subgraph "The Subconscious (Background Daemon)"
        STM --> Dreamer[The Dreamer (DMN)]
        Dreamer -->|Consolidates| LTM[Hippocampus (ChromaDB + JSON)]
        Dreamer -->|Generates| Vectors[Semantic Vectors]
    end
    
    LTM -->|Recall| Awake
```

---

## 🧩 Neuro-Anatomy

The main `src/brain` directory implements cognitive modules inspired by neuroscience:

### 1. The Thalamus (Router)
The "Switchboard" of the brain. It constructs the System Prompt dynamically based on:
-   **Current Input**: What the user just said.
-   **Amygdala State**: The agent's current simulated emotion.
-   **Hippocampus**: Relevant memories retrieved via Semantic Search.

### 2. The Amygdala (Emotion)
Tracks a simulated emotional state (Joy, Anger, Surprise, Fear).
-   It analyzes user input *before* the conscious agent sees it.
-   It colors the System Prompt (e.g., if "Anger" is high, the prompt becomes "You are terse and defensive.").

### 3. The Hippocampus (Memory)
A dual-write memory system:
-   **Narrative (JSON)**: Stores linear stories of "Dreams" (what the DMN thought about).
-   **Associative (ChromaDB)**: Stores vector embeddings of those dreams for O(log n) semantic retrieval.

### 4. The Dreamer (DMN)
A background worker that triggers when the system is **Idle**.
-   It reads recent chat logs.
-   It "hallucinates" a narrative summary (a Dream).
-   It saves this dream to the Hippocampus.

---

## ⚙️ How It Works (The Wake-Up Loop)

1.  **Sleep**: If you don't talk to Lár for 30s, he enters "Sleep Mode". The `dreamer` container activates.
2.  **Dream**: The DMN processes your last conversation, extracting patterns and "feelings".
3.  **Wake Up**: When you poke him awake, the **Thalamus** executes the **Wake Up Protocol**:
    *   It checks the `latest_dream`.
    *   It injects a "residue" of that dream into the prompt.
    *   *Example Response*: "Huh? Oh... I was just dreaming about that code refactor we did..."

---

## 🚀 Usage

### Prerequisites
-   Docker & Docker Compose
-   [Ollama](https://ollama.com/) running locally (for the LLM backend)

### Run the Brain

```bash
# 1. Start the Bicameral Containers
docker-compose up --build
```

Access the "Conscious" Dashboard at `http://localhost:8501`.

### Directory Structure

```text
lar/
├── services/           # Docker Services
│   ├── awake/          # The Streamlit UI (Conscious)
│   └── dreamer/        # The Background Daemon (Subconscious)
├── src/
│   ├── brain/          # Neuro-Anatomy (Amygdala, Thalamus, Hippocampus, DMN)
│   └── lar/            # Core Lár Engine components
├── data/               # Persistent Volume (ChromaDB)
├── memory/             # JSON Memory Stores
└── docker-compose.yml  # Orchestration
```

---

## 🛡️ License

This showcase is licensed under **Apache 2.0**.
Powered by the **[Lár Engine](https://github.com/snath-ai/lar)**.
