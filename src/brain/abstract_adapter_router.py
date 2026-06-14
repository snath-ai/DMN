"""
AbstractAdapterRouter
=====================
Domain-agnostic contract for the two-pass System 1 + System 2 adapter router.

Every Snath domain exposes an AdapterRouter that resolves a routing impasse
(TRIGGER_REPLAN) into a committed action (COMMIT_TRAJECTORY) by consulting:

  System 1 — Identification (trust-invariant)
  -------------------------------------------------------
  Cosine-similarity centroid match on the divergence vector Δ = z_a − z_b.
  The geometric fingerprint of a failure class is durable: "ice causes pitot
  freeze" clusters identically across sensor generations; "scope_overclaim"
  lands in the same region of claims–reviews latent space regardless of
  conference year.  _nearest() fires regardless of adapter age.  No temporal
  gate.

  System 2 — Correction (perishable)
  -------------------------------------------------------
  LoRA .pt injection, gated by W = exp(-λ · Δt) ≥ min_trust.
  A delta trained on one epoch may be wrong for a later epoch (hardware
  revision, market-regime shift, venue culture change).  The temporal gate
  withholds stale corrections while System 1 still commits.

  Degradation path
  -------------------------------------------------------
  System 2 refused → System 1 still identifies and commits.
  Identify correctly, correct conservatively.

Formalised in "Architecture Is All You Need" (Sajeev 2026), §3.4
Remark (Temporal Decay and Synaptic Depression).
"""
from __future__ import annotations

import datetime
import math
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple


class AbstractAdapterRouter(ABC):
    """
    Structural contract for all Snath domain adapter routers.

    Concrete subclasses must implement _load_all, _nearest, resolve, and
    available.  The decay_weight formula is provided as a concrete static
    method so domain owners don't re-derive it — only the λ-table differs
    per domain.
    """

    @abstractmethod
    def _load_all(self) -> None:
        """Load and HMAC-verify all JSON centroid adapters from adapter_dir.
        Called at __init__ and by refresh()."""

    @abstractmethod
    def _nearest(self, delta) -> Optional[Any]:
        """
        System 1 — trust-invariant centroid match.

        Find the closest stored centroid to delta (= z_a − z_b) by cosine
        similarity.  Return the matched adapter object or None if no match
        exceeds tau_sim.

        MUST NOT apply a temporal gate — failure-class identification is
        durable regardless of how old the adapter is.
        """

    @abstractmethod
    def resolve(
        self,
        z_a,
        z_b,
        base_decision,
        conf_a: float,
        conf_b: float,
        enc_a=None,
        enc_b=None,
    ) -> Tuple[Any, str]:
        """
        System 1 + System 2 combined inference.

        Parameters
        ----------
        z_a, z_b        : Latent vectors from the two modal encoders.
        base_decision   : RouteDecision from AbstractDivergenceRouter.
        conf_a, conf_b  : Encoder confidence scalars.
        enc_a, enc_b    : Live encoder objects (optional).  Pass to enable
                          System 2 LoRA injection inside resolve().
                          When omitted, only the System 1 decision override
                          is applied.

        Returns
        -------
        (decision, audit_note)
            decision   — the (possibly updated) route decision
            audit_note — human-readable, HMAC-auditable string recording
                         both the System 1 identification and the System 2
                         trust outcome (injected / stale-refused / ready)
        """

    @abstractmethod
    def available(self) -> List[str]:
        """Return the list of loaded failure-class / cluster IDs."""

    def refresh(self) -> None:
        """Reload adapters from disk (calls _load_all)."""
        self._load_all()

    @staticmethod
    def decay_weight(created_at_iso: Optional[str], lam: float = 0.10) -> float:
        """
        Temporal trust weight W = exp(-λ · Δt), Δt in fractional years.

        Returns 1.0 if created_at_iso is None (no timestamp → treat as fresh).

        Recommended λ values (from domain's _LAMBDA table):
          fast   (environmental / market regime): λ = 0.50
          medium (sensor drift / methodology):    λ = 0.20
          slow   (structural / hardware defect):  λ = 0.02
          default:                                λ = 0.10
        """
        if not created_at_iso:
            return 1.0
        try:
            created = datetime.datetime.fromisoformat(
                created_at_iso.replace("Z", "+00:00")
            )
            now = datetime.datetime.now(datetime.timezone.utc)
            delta_years = (now - created).total_seconds() / (365.25 * 24 * 3600)
            return math.exp(-lam * max(0.0, delta_years))
        except Exception:
            return 1.0
