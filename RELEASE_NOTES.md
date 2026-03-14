# Release Notes — v2.0.0

## Lár DMN v2.0 — Prefrontal Cortex & 3-Tier Memory Architecture

**Release date:** 2026-03-14

---

### What's New

#### Prefrontal Cortex Layer (`src/brain/prefrontal.py`)
A biologically-inspired compression gateway inspired by the human PFC.  
Instead of injecting raw ChromaDB chunks (~2000 tokens) directly into the context window, every query now routes through the Prefrontal Cortex, which synthesises retrieved memories into a dense ≤100 token paragraph.  
**Result: context footprint reduced from ~2000 tokens → ~380 tokens.**

#### 3-Tier Memory Architecture
| Tier | Name | Storage | Token Budget |
|------|------|---------|--------------|
| 1 | Hot Memory | In-process JSONL rolling buffer | ~200 tokens |
| 2 | Warm Memory | ChromaDB `warm_memory` collection | ~80 tokens |
| 3 | Cold Memory | ChromaDB `long_term_memory` collection | Never injected directly |

#### Dual-Pass Dreamer Consolidation
The `lar-dreamer` service now performs two passes on idle:
- **Pass 1**: Saves the raw dream narrative as Cold Memory embeddings.
- **Pass 2**: Compresses the dream into a single semantic sentence, stored in Warm Memory.

#### Full Pytest Suite
`tests/test_prefrontal.py` and `tests/test_memory_tiers.py` added.  
**6/6 tests pass** without requiring a live Ollama instance.

---

### Bug Fixes
- Restored missing `_generate_embedding()` in `Hippocampus` (caused silent embedding failures).
- Fixed double-escaped `\n` in `Thalamus` system prompt construction.
- Removed duplicate `recall()` and `run_lifecycle()` method definitions.
- Removed legacy daemons (`memory_retrieval.py`, `dmn_dreamer.py`, `autonomic_system.py`, `lar_orchestrator.py`).
- Replaced all bare `except: pass` blocks with explicit error logging.
- Fixed `asyncio` backport dependency conflict in `requirements.txt`.

---

### Biological Completion
| Component | DMN v1 | DMN v2 |
|-----------|--------|--------|
| Hippocampus (ChromaDB retrieval) | ✅ | ✅ |
| Amygdala (emotional gating) | ✅ | ✅ |
| Dreamer (sleep consolidation) | ✅ | ✅ |
| Prefrontal Cortex (compression gateway) | ❌ | ✅ |

Human memory architecture is now architecturally complete.
