# EU AI Act Compliance Strategy for Lár DMN

The **Lár DMN (Default Mode Network)** architecture plays a critical role in satisfying the requirements of the **European Union Artificial Intelligence Act (EU AI Act)**, specifically for high-risk AI systems requiring long-term stability and consistency.

By solving the problem of catastrophic forgetting, DMN directly addresses the regulatory need for robust, reproducible AI behavior over extended time horizons.

---

## Key Compliance Pillars

### 1. Article 15: Accuracy, Robustness, and Cybersecurity
**Requirement:** High-risk systems must achieve an appropriate level of accuracy, robustness, and resilience against errors, faults, or inconsistencies.

**Lár DMN Implementation:**
Standard AI systems (particularly stochastic LLMs) violate robustness requirements when they randomly alter their behavior or "forget" previously established facts. The Lár DMN solves this through `AbstractDMN.consolidate()` — the system accumulates high-divergence events (D_hard), clusters them into signed centroid adapters (Tier 2), and optionally distills them into rank-1 LoRA adapters (Tier 3). These artifacts are deterministically recalled at inference time via `AbstractAdapterRouter.resolve()`, ensuring that proven correction geometry is applied consistently rather than stochastically re-derived on each call.

Stale adapters are refused before injection via the temporal trust gate `W = exp(-λ·Δt) ≥ min_trust`. Adapters that degrade below the trust threshold are withheld while System 1 (geometry-based centroid match) still commits — so the system degrades gracefully rather than silently applying outdated corrections.

### 2. Article 12: Record-Keeping (Causal Audit Logging)
**Requirement:** High-risk systems must automatically record events to ensure traceability of the system's functioning throughout its lifecycle.

**Lár DMN Implementation:**
Every durable artifact produced by `AbstractDMN.consolidate()` — signed failure-class centroids, LoRA `.pt` adapters — is **HMAC-SHA256 signed** with a domain-specific secret (`DMN_HMAC_SECRET` env var) before being written to disk. The `hmac_hex` field on every artifact allows auditors to verify that no memory was tampered with after consolidation.

`AbstractAdapterRouter._load_all()` verifies the HMAC of every artifact it loads. Any adapter that fails verification is silently skipped — never injected into inference.

Domain implementations invoke `consolidate()` directly via the `AbstractDMN` contract — typically in a nightly or post-session background cycle. The audit trail for active inference decisions is covered separately by the Lár `AuditLogger` on the main execution path.

### 3. Tensor Safety in Long-Term Storage
**Requirement:** Systems must securely and losslessly process operational data.

**Lár DMN Implementation:**
Inside Lár-JEPA integration, DMN receives raw PyTorch/NumPy tensors (JEPA world-model states). `TensorSafeEncoder` (built into the Lár engine) collapses these to structural metadata during consolidation — ensuring no biological or kinematic context is lost or silently altered over time. The signed artifact pipeline then guarantees that what was consolidated is exactly what is recalled.
