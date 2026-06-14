<p align="center">
  <img src="https://raw.githubusercontent.com/snath-ai/.github/main/assets/lar-logo.png" width="80" alt="Lár Logo" />
</p>
<p align="center"><em>Lár DMN — The Memory Layer for the Snath AI Cognitive Architecture</em></p>
<p align="center">
  <a href="https://github.com/snath-ai/lar">
    <img alt="Based on" src="https://img.shields.io/badge/Spine-Lár%20Engine%20v2.2.0-blue?style=for-the-badge">
  </a>
  <a href="https://github.com/snath-ai/DMN/releases/tag/v2.4.0">
    <img alt="Version" src="https://img.shields.io/badge/lar--dmn-v2.4.0-blueviolet?style=for-the-badge">
  </a>
  <a href="https://doi.org/10.5281/zenodo.18175178">
    <img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18175178-blue?style=for-the-badge" alt="DOI">
  </a>
</p>

# Lár DMN — Continual Learning Without Retraining

Every AI agent forgets everything the moment it stops running. Context windows fill up, old messages get silently truncated, and the agent permanently loses knowledge of past interactions. In world-model systems, high-divergence events are discarded instead of becoming the curriculum for adaptation.

**DMN solves this architecturally.** No weight updates to the base model. No catastrophic forgetting. No retraining loops. Memory and adaptation are treated as infrastructure problems — the same way a database solves persistence without touching application code.

This repo is a **blueprint** — two abstract base classes that define how any domain accumulates high-divergence events, consolidates them into signed adapters, and applies them at inference time. Clone it, extend it, and the OS-level promise holds by construction.

---

## Part of a Larger System

DMN is the memory layer of a three-part cognitive architecture:

| Repository | Role |
| :--- | :--- |
| **[Lár](https://github.com/snath-ai/lar)** | The execution spine — deterministic graph engine, HMAC audit trail, EU AI Act compliance |
| **[Lár DMN](https://github.com/snath-ai/DMN)** ← you are here | The memory layer — continual learning contracts |
| **[Lár-JEPA](https://github.com/snath-ai/Lar-JEPA)** | The world model — 10 ABCs for divergence routing, modal encoding, fault localisation |

The industry is building the Brain (LLMs, JEPAs). We are building the Nervous System.

---

## The Blueprint: ABC Contract Layer

### `AbstractDMN` — the memory contract

```python
from brain.abstract_dmn import AbstractDMN

class AbstractDMN(ABC):
    def ingest(self, event) -> None: ...               # Tier 1: accept event, non-blocking
    def consolidate(self, **kwargs) -> List[dict]: ... # Tier 2/3: D_hard → signed adapters
    def recall(self, query, **kwargs) -> Any: ...      # Tier 2: retrieve context, silent on miss
    def stats(self) -> dict: ...                       # queue / memory introspection
```

**Three invariants that every implementation must satisfy:**

| Invariant | Rule |
|:---|:---|
| **D1 — Non-blocking ingest** | `ingest()` must never raise. Catch and log. |
| **D2 — Signed artifacts** | Every durable artifact from `consolidate()` carries `hmac_hex`. |
| **D3 — Silent recall** | `recall()` returns `None` / `""` / `{}` on miss. Never raises. |

### `AbstractAdapterRouter` — the inference bridge

```python
from brain.abstract_adapter_router import AbstractAdapterRouter

class AbstractAdapterRouter(ABC):
    def _load_all(self) -> None: ...           # load + HMAC-verify all centroid adapters
    def _nearest(self, delta) -> Optional[Any]: ...  # System 1: trust-invariant centroid match
    def resolve(self, z_a, z_b, base_decision,
                conf_a, conf_b, enc_a=None, enc_b=None) -> Tuple[Any, str]: ...
    def available(self) -> List[str]: ...

    def refresh(self) -> None: ...             # concrete — calls _load_all()
    @staticmethod
    def decay_weight(created_at_iso, lam=0.10) -> float: ...  # W = exp(-λ·Δt)
```

### System 1 / System 2 trust asymmetry

`_nearest()` is **trust-invariant** — it fires regardless of adapter age. Failure-class geometry is durable: "ice causes pitot freeze" clusters identically across sensor generations. The temporal gate `W = exp(-λ·Δt)` lives exclusively in `resolve()`, at the `.pt` loading step.

When `W < min_trust`, System 1 still identifies and commits. System 2 correction is withheld. **Identify correctly, correct conservatively.**

Formalised in *Architecture Is All You Need* (Sajeev 2026), §3.4 — see [Papers & Research](#papers--research).

### The complete inference contract

Together with `AbstractModalEncoder` and `AbstractDivergenceRouter` from Lár-JEPA, the full loop is formally contracted:

```
AbstractModalEncoder      →  encode z_a, z_b
AbstractDivergenceRouter  →  V1–V6 routing decision
AbstractDMN               →  ingest → consolidate → recall
AbstractAdapterRouter     →  resolve → (decision, audit_note)
```

Any new domain implements four classes and the OS-level promise holds by construction.

---

## Domain Extensions

All five DMN implementations satisfy `AbstractDMN`. All four domain adapter routers satisfy `AbstractAdapterRouter`:

| Project | DMN class | AdapterRouter class | Domain |
|---|---|---|---|
| **DMN** (this repo) | `DefaultModeNetwork` | — | LLM conversation memory (ChromaDB) |
| **[Snath Robotics](https://github.com/snath-ai/snath-robotics)** | `RoboticsDMN` | `RoboticsAdapterRouter` | Dual-stream sensor fusion (vision + proprioception) |
| **[Snath Aviation](https://github.com/snath-ai/snath-aviation)** | `AviationDMN` | `AviationAdapterRouter` | Flight anomaly detection (pitot / radar) |
| **[Snath Basis](https://github.com/snath-ai/snath-basis)** | `BasisDMN` | `BasisAdapterRouter` | Factor-model divergence (fundamentals / market) |
| **[Snath Research](https://github.com/snath-ai/snath-research)** | `ResearchDMN` | `ResearchAdapterRouter` | Paper review routing (claims / reviews) |

Each domain owns its HMAC key, λ-table, and centroid field names. `AbstractDMN` and `AbstractAdapterRouter` own the structural guarantee.

---

## The Human Analogy

Human brains don't rewrite neural weights every night. The **Hippocampus** consolidates the day's experiences into long-term cortical storage during sleep. Raw sensory data is gone by morning; the meaning persists.

DMN implements this exact strategy as software:

| Human Brain | Lár DMN |
|---|---|
| Sensory Input | D_hard events / domain observations |
| Hippocampal Consolidation (Sleep) | `consolidate()` — D_hard queue → signed adapters |
| Long-Term Cortical Storage | Tier 2 semantic centroids + Tier 3 LoRA `.pt` adapters |
| Working Memory | Tier 1 episodic queue |
| Synaptic Depression | `W = exp(-λ·Δt)` — stale adapters refused at inference |

---

## 3-Tier Memory

| Tier | Contents | Lifetime | Written by |
|:---|:---|:---|:---|
| **Tier 1 — Episodic** | D_hard events (divergence vectors, failure labels) | Perishable | `ingest()` only |
| **Tier 2 — Semantic** | HMAC-signed JSON centroid cache | Durable (geometry-stable) | `consolidate()` only |
| **Tier 3 — Procedural** | HMAC-signed LoRA `.pt` adapters | Perishable (time-gated by W) | `consolidate()` only |

Write direction is strictly upward: Tier 1 → Tier 2 → Tier 3. `recall()` reads from Tier 2. `AdapterRouter.resolve()` reads from Tier 2 (System 1) and Tier 3 (System 2).

Not every domain reaches Tier 3. Domains with open-vocabulary recall requirements consolidate into Tier 2 via ChromaDB semantic search (`DefaultModeNetwork`). Domains with a fixed failure-class vocabulary go all the way to Tier 3 (signed LoRA adapters) with flat-file JSON centroids as Tier 2.

---

## Implementing a New Domain

```python
from brain.abstract_dmn import AbstractDMN
from brain.abstract_adapter_router import AbstractAdapterRouter

class MyDMN(AbstractDMN):
    def ingest(self, event) -> None:
        try:
            self.queue.push(event)            # Tier 1: non-blocking write
        except Exception as e:
            print(f"[DMN] ingest failed: {e}")

    def consolidate(self, **kwargs) -> List[dict]:
        # pull resolved D_hard events, build signed centroids + LoRA adapters
        ...

    def recall(self, query, **kwargs) -> Any:
        return self.load_centroid(query)      # Tier 2: silent on miss


class MyAdapterRouter(AbstractAdapterRouter):
    def _load_all(self) -> None:
        # load + HMAC-verify *.json centroid adapters
        ...

    def _nearest(self, delta) -> Optional[dict]:
        # cosine similarity match — NO temporal gate here
        ...

    def resolve(self, z_a, z_b, base_decision, conf_a, conf_b,
                enc_a=None, enc_b=None):
        # System 1 centroid match → System 2 LoRA injection if W ≥ min_trust
        ...

    def available(self) -> List[str]:
        return [c["failure_class"] for c in self._centroids]
```

---

## Implementing `consolidate()` — The LoRA Training Loop

`consolidate()` is the heart of the continual learning contract. Here is the full blueprint — the same pattern used across all Snath domain implementations.

### What it does

1. Pull **resolved** D_hard events from the queue (events labelled with a winner stream)
2. Group events by `failure_class`
3. For each class with enough events: build a **System 1 centroid** (JSON) and a **System 2 LoRA adapter** (`.pt`)
4. HMAC-sign both artifacts before writing to disk

### System 1 — JSON centroid

```python
import hashlib, hmac, json
from pathlib import Path

ADAPTER_KEY = b"your-domain-hmac-secret"  # keep per-domain, never commit

def build_centroid(failure_class, group, adapter_dir):
    dim = len(group[0].z_a)
    centroid_a = [sum(e.z_a[i] for e in group) / len(group) for i in range(dim)]
    centroid_b = [sum(e.z_b[i] for e in group) / len(group) for i in range(dim)]

    payload = {
        "failure_class": failure_class,
        "centroid_a":    centroid_a,
        "centroid_b":    centroid_b,
        "n_events":      len(group),
    }
    sig = hmac.new(
        ADAPTER_KEY,
        json.dumps(payload, sort_keys=True).encode(),
        hashlib.sha256,
    ).hexdigest()
    payload["hmac_hex"] = sig

    Path(adapter_dir, f"{failure_class}.json").write_text(json.dumps(payload, indent=2))
```

### System 2 — Rank-1 LoRA adapter

```python
import torch, torch.nn as nn, torch.optim as optim

def build_lora(failure_class, group, winner_stream, adapter_dir,
               n_epochs=100, lr=0.01):
    target = torch.tensor([e.z_a if winner_stream == "a" else e.z_b
                           for e in group], dtype=torch.float32)
    faulty = torch.tensor([e.z_b if winner_stream == "a" else e.z_a
                           for e in group], dtype=torch.float32)
    dim = faulty.shape[1]

    A = nn.Parameter(torch.randn(dim, 1) * 0.01)
    B = nn.Parameter(torch.randn(1, dim) * 0.01)
    opt = optim.AdamW([A, B], lr=lr)

    for _ in range(n_epochs):
        opt.zero_grad()
        loss = nn.functional.l1_loss(faulty + (faulty @ A) @ B, target)
        loss.backward()
        opt.step()

    a_hex = hashlib.sha256(A.detach().numpy().tobytes()).hexdigest()[:16]
    b_hex = hashlib.sha256(B.detach().numpy().tobytes()).hexdigest()[:16]
    sig = hmac.new(
        ADAPTER_KEY,
        f"{failure_class}|{winner_stream}|{a_hex}|{b_hex}".encode(),
        hashlib.sha256,
    ).hexdigest()

    torch.save({
        "A": A.detach(), "B": B.detach(),
        "failure_class": failure_class, "winner_stream": winner_stream,
        "n_events": len(group), "final_loss": round(float(loss), 6),
        "hmac_hex": sig,
    }, str(Path(adapter_dir) / f"{failure_class}.pt"))
```

### Minimum events threshold

```python
MIN_EVENTS = 3  # tune per domain — higher for noisier sensors

for failure_class, group in by_class.items():
    if len(group) < MIN_EVENTS:
        continue
    build_centroid(failure_class, group, adapter_dir)
    build_lora(failure_class, group, winner_stream, adapter_dir)
```

### `_load_all()` — verify before trust

```python
def _load_all(self):
    self._centroids = []
    for path in Path(self.adapter_dir).glob("*.json"):
        data = json.loads(path.read_text())
        sig = data.pop("hmac_hex")
        expected = hmac.new(
            ADAPTER_KEY,
            json.dumps(data, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(sig, expected):
            data["hmac_hex"] = sig
            self._centroids.append(data)
        # silently skip tampered or unsigned adapters
```

### Reference implementation

See **[snath-robotics](https://github.com/snath-ai/snath-robotics)** for a complete working implementation: dual-stream sensor fusion, full `consolidate()` with centroid + LoRA training, HMAC signing, and `RoboticsAdapterRouter` with System 1/2 resolution.

---

## Background Consolidation Daemon

`services/dreamer/dreamer_worker.py` shows how to run `consolidate()` as a background process — watching the interaction log for idle periods and triggering the DMN sleep cycle automatically:

```bash
LOG_FILE=/data/short_term_memory.jsonl \
MEMORY_FILE=/data/long_term_insights.json \
OLLAMA_MODEL=qwen2.5:14b \
python services/dreamer/dreamer_worker.py
```

---

## JEPA Integration — World Model Memories

DMN is the memory layer for [Lár-JEPA](https://github.com/snath-ai/Lar-JEPA). After a `COMMIT_TRAJECTORY` routing decision, the JEPA world model writes trajectory heuristics into a `DefaultModeNetwork`-backed Hippocampus via the `AbstractDMN.ingest()` → `consolidate()` → `recall()` contract. At the next planning cycle, `recall()` retrieves the closest prior heuristic and injects it into the JEPA latent prompt.

The integration bridge lives in **Lár-JEPA** (not this repo). Clone [snath-ai/Lar-JEPA](https://github.com/snath-ai/Lar-JEPA) and see `dmn/` for the consolidation node that connects the two repos.

---

## Papers & Research

The formal foundations of the Lár DMN blueprint:

| Paper | What it establishes | Reference |
|:---|:---|:---|
| **Annotation-Free Continual Learning** (Sajeev 2026) | 7 formal proofs that high-divergence events can be accumulated and consolidated without human annotation — the theoretical basis for the `ingest → consolidate` contract and the D_hard queue | [DOI 10.5281/zenodo.18175178](https://doi.org/10.5281/zenodo.18175178) |
| **Difficulty Invariance (V7)** (Sajeev 2026) | Proves that failure-class centroid geometry is world-grounded and persists across encoder upgrades — the formal basis for `_nearest()` carrying no temporal gate | [DOI 10.5281/zenodo.20614051](https://doi.org/10.5281/zenodo.20614051) |
| **Architecture Is All You Need** (Sajeev 2026) | Formalises the D1–D5 `AbstractDMN` invariants, AR1–AR5 `AbstractAdapterRouter` invariants, System 1 / System 2 trust asymmetry, and the synaptic depression remark (§3.4) | In preparation |

The `AbstractAdapterRouter` trust-invariant design (`_nearest()` fires regardless of adapter age) is a direct consequence of V7: because D_hard geometry is world-grounded, identification does not decay — only correction does.

---

## EU AI Act Compliance

Lár DMN is structurally designed to support EU AI Act compliance for high-risk systems:

- **Article 15 (Robustness):** Proven correction geometry is deterministically recalled, eliminating stochastic drift. Stale adapters are refused via `W = exp(-λ·Δt)` before injection.
- **Article 12 (Record-Keeping):** Every durable artifact from `consolidate()` is HMAC-SHA256 signed. `AbstractAdapterRouter` verifies before trusting. The background daemon invokes `consolidate()` via the `AbstractDMN` contract — no bypassing the signed artifact pipeline.

See [EU_AI_ACT_COMPLIANCE.md](EU_AI_ACT_COMPLIANCE.md) for full architectural details.

---

## License

Apache 2.0. Built on the [Lár Engine](https://github.com/snath-ai/lar).
