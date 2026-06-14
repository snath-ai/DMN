# Changelog

## v2.3.2 — README overhaul (2026-06-14)
### Changed
- `README.md`: complete rewrite to reflect v2.3.x state
  - Added ABC contract layer section: `AbstractDMN` + `AbstractAdapterRouter` with code examples
  - Added domain extensions table: all 6 DMN implementations + 4 AdapterRouter implementations
  - Added "Implementing a New Domain" quick-start stubs
  - Added domain continual learning architecture diagram (Mermaid)
  - Updated 3-tier memory table to include Tier 1/2/3 labels and lifetime column
  - Updated version badge from v2.1.0 → v2.3.2
  - Updated human analogy table to include synaptic depression / LoRA adapter story
  - Preserved original conversation memory content (Hippocampus, Dreamer, PFC)

## v2.3.1 — AbstractAdapterRouter (2026-06-14)
### Added
- `brain/abstract_adapter_router.py`: `AbstractAdapterRouter` — domain-agnostic contract for the two-pass System 1 + System 2 inference bridge
  - `_load_all()` — abstract: load and HMAC-verify JSON centroid adapters at construction
  - `_nearest(delta) → Optional[Any]` — abstract: System 1 trust-invariant centroid match (no temporal gate)
  - `resolve(z_a, z_b, base_decision, conf_a, conf_b, enc_a, enc_b) → (decision, audit_note)` — abstract: System 1 + System 2 combined inference
  - `available() → List[str]` — abstract: loaded failure-class / cluster IDs
  - `refresh() → None` — concrete: calls `_load_all()` (removes copy-paste from all domain routers)
  - `decay_weight(created_at_iso, lam) → float` — concrete static: `W = exp(-λ · Δt)`, the temporal trust formula copy-pasted across all four domains, now canonical
- `AbstractAdapterRouter` exported from `brain/__init__.py`
### Extension contract
- Snath Robotics `RoboticsAdapterRouter`, Snath Aviation `AviationAdapterRouter`, Snath Basis `BasisAdapterRouter`, Snath Research `ResearchAdapterRouter` — all extend `AbstractAdapterRouter`
- Domain routers own their HMAC key, λ-table, and centroid field names; `AbstractAdapterRouter` owns the structural guarantee and the decay formula
### Closes the OS-level loop
- With `AbstractAdapterRouter` in place, `AbstractModalEncoder` (Lár-JEPA), `AbstractDMN` (v2.3.0), and `AbstractAdapterRouter` together form the complete inference-time contract: encode → diverge → remember → route → adapt
- Any new domain can swap encoders and the adapter system wires up automatically through the contract, not through copy-paste

## v2.3.0 — AbstractDMN (2026-06-14)
### Added
- `brain/abstract_dmn.py`: `AbstractDMN` — domain-agnostic base class for all Snath DMN implementations
  - `ingest(event)` — accept a domain event into Tier 1 (episodic) memory
  - `consolidate(**kwargs) → List[dict]` — process events into Tier 2/3 (semantic/procedural) artifacts; all durable artifacts must be HMAC-signed
  - `recall(query, **kwargs) → Any` — retrieve Tier 2 context for the current inference cycle
  - `stats() → dict` — optional, default returns `{}`
- `DefaultModeNetwork` now extends `AbstractDMN`; `activate()` retained as backward-compatible alias for `consolidate()`
- `AbstractDMN` exported from `brain/__init__.py`
### Extension contract
- Snath Robotics `RoboticsDMN`, Snath Aviation, Snath Basis, Snath Research — all must extend `AbstractDMN`
- Domain implementations own their type contracts; `AbstractDMN` owns the structural guarantee

## v2.2.0 — Audit Patch Release (2026-03-15)
### Fixed
- `formatter.py`: `summarize_diff()` was checking key `"modified"` but `compute_state_diff()` writes `"updated"` — Modified column in Rich log tables was silently empty for every run
- `memory_tiers.py`: `get_hot_memory()` used literal `\n` (double-escaped) in `join()`, causing hot-memory prompts to show `\n` as plain text instead of newlines
- `hippocampus.py`: `_format_insights()` had the same literal `\n` join bug for legacy insight formatting
- `default_mode_network.py` / `hippocampus.py`: Hardcoded `"llama3.2"` embedding model replaced with `OLLAMA_EMBED_MODEL` env var (defaults to `"llama3.2"`) for cross-model compatibility
- `thalamus.py`: Removed dead `MemoryTiers` instantiation that was never called (hot-memory reads went through `_get_short_term_memory()` directly)
- `node.py`: Removed duplicate `from .state import GraphState` import
- `serializer.py`: Changed exported manifest default `allow_env_access` from `True` to `False` (secure-by-default)
- `consciousness_stream.py`: Fixed misleading error message "Error parsing log stream" → "Error closing stale handler"
- `app.py`: Version string updated from v1.0.0 to v2.0.1 in both UI title and sidebar caption
- `services/awake/Dockerfile` + `services/dreamer/Dockerfile`: Base image upgraded from `python:3.10-slim` to `python:3.11-slim` to match `pyproject.toml` requirement `python = "^3.11"`
- `tests/conftest.py`: Created to fix `test_cold_never_injected_directly` — was failing with `ModuleNotFoundError: No module named 'lar.consciousness_stream'` due to missing sys.path fixture
### Changed
- `pyproject.toml`: Added missing deps `chromadb ^1.4.0`, `streamlit ^1.32.0`, `requests ^2.31.0`, `pandas ^2.2.1`; aligned `litellm` pin from `^1.80.0` to `^1.34.0` (matching installed version in requirements.txt)


## v2.0.0 — Prefrontal Cortex Update
### Added
- PrefrontalCortex compression layer
- Three-tier memory architecture (hot/warm/cold)
- Warm memory ChromaDB collection
- lar-dreamer warm memory population
### Fixed  
- KV cache bottleneck on long-horizon agents
- Raw chunk injection replaced with compressed synthesis
### Biological Completion
- DMN v1 had: Hippocampus ✅ Amygdala ✅ Dreamer ✅
- DMN v2 adds: Prefrontal Cortex ✅
- Human memory architecture now complete
