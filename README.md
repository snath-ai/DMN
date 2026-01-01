<p align="center">
  <img src="https://raw.githubusercontent.com/snath-ai/.github/main/assets/lar-logo.png" width="80" alt="Lár Logo" />
</p>
<p align="center"><em>Lár: The DMN Project</em></p>
<p align="center">
  <a href="https://github.com/snath-ai/lar">
    <img alt="Based on" src="https://img.shields.io/badge/Variant%20of-Lár%20Engine-blue?style=for-the-badge">
  </a>
   <a href="https://github.com/snath-ai/DMN">
    <img alt="Architecture" src="https://img.shields.io/badge/Architecture-Bicameral%20Mind-blueviolet?style=for-the-badge">
  </a>
</p>

# Lár DMN: Bicameral Memory Architecture

This repository is a specialized **technical showcase** of the [Lár Engine](https://github.com/snath-ai/lar), demonstrating how to build an AI agent with a **Default Mode Network (DMN)**.

It explores the concept of **Biomimetic AI**: moving beyond stateless request/response loops to a system that maintains a continuous, background cognitive life cycle.

## Architecture: The "Bicameral" Loop

Unlike standard agents that are purely reactive (Input -> Output -> Die), the Lár DMN implements a separation between **Conscious Processing** and **Subconscious Consolidation**.

| Component | Standard Architecture | Lár DMN Architecture |
| :--- | :--- | :--- |
| **Lifecycle** | **Reactive**. Idle until prompted. | **Continuous**. Active background processes ("Dreaming") during idle time. |
| **Memory** | **Stateless / Conversation History**. | **Consolidated**. A "Hippocampus" converts logs into vector embeddings during sleep. |
| **Context** | **Static**. "You are a helpful assistant." | **Dynamic**. System prompts evolve based on simulated emotion and recent dreams. |

---

## Core Neuro-Modules

This project implements specific architectural components inspired by biological cognition:

### 1. The Default Mode Network (Background Daemon)
Implemented as a separate Docker service (`lar-dreamer`).
-   **Trigger**: Activates when the main agent is idle (simulated "Sleep").
-   **Process**: Analyzes the recent interaction logs ("Short Term Memory").
-   **Output**: Synthesizes a narrative summary ("Dream") and saves it to Long-Term Memory.

### 2. The Hippocampus (Dual-Write Memory)
A hybrid memory system that bridges the gap between massive context windows and efficient retrieval.
-   **Narrative Store (JSON)**: Preserves the chronological story of the agent's experiences.
-   **Vector Store (ChromaDB)**: Embeds these experiences for semantic retrieval (RAG).
-   *Why?* This allows the agent to recall "concepts" similar to the current conversation, not just recent keywords.

### 3. The Thalamus (Dynamic Router)
The input processing layer. Instead of sending user text directly to the model, the Thalamus:
1.  **Injects Emotion**: Checks the simulated `Amygdala` state (e.g., Fear, Joy).
2.  **Retrieves Context**: Queries the `Hippocampus` for relevant past "dreams".
3.  **Constructs Prompt**: Builds a unique system prompt for *that specific turn*.

---

## Usage Guide

### 1. Requirements
-   Docker & Docker Compose
-   [Ollama](https://ollama.com/) (running `llama3.2` or similar)

### 2. Start the Architecture
This spins up the two hemispheres of the brain: `awake` (UI) and `dreamer` (Background).

```bash
docker-compose up --build
```

### 3. Observe the Cycle
1.  **Conscious Phase**: Interact with the agent at `http://localhost:8501`.
2.  **Sleep Phase**: Stop interacting. Watch the sidebar timer.
3.  **Consolidation**: The DMN will activate in the terminal logs, processing your chat.
4.  **Wake Phase**: Resume the chat. The agent will seemingly "remember" or be influenced by the background processing.

---

## Project Structure

```text
lar/
├── services/
│   ├── awake/          # CONSCIOUS: Streamlit UI
│   └── dreamer/        # SUBCONSCIOUS: Background Python Worker
├── src/
│   ├── brain/          # NEURO-MODULES
│   │   ├── amygdala.py # Emotion State Machine
│   │   ├── thalamus.py # Input Routing & Prompting
│   │   ├── hippocampus.py # Vector Memory (ChromaDB)
│   │   └── default_mode_network.py # Consolidation Logic
│   └── lar/            # BASE ENGINE
└── memory/             # PERSISTENCE
    ├── dreams.json     # Sequential Log
    └── chroma_db/      # Vector Index
```

---

## License

This project is open source under **Apache 2.0**.
It serves as a reference implementation for advanced cognitive architectures using the **[Lár Engine](https://github.com/snath-ai/lar)**.
