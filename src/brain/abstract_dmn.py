"""
AbstractDMN — Domain-agnostic Default Mode Network contract.
============================================================
Every Snath domain project (Robotics, Aviation, Basis, Research, Locus)
runs a DMN with the same three-phase cycle:

  ingest     → accept a domain event into working memory
  consolidate → process accumulated events into durable corrections/memories
  recall     → retrieve relevant context for the current inference cycle

The data types are fundamentally different across domains — robot sensor
vectors, crystal trajectory heuristics, adverse event narratives — so the
interface is intentionally generic. Domain implementations own their type
contracts; this ABC owns the structural guarantee.

Three-tier memory correspondence
---------------------------------
  Tier 1 — Episodic  : ingest() writes here (fast, perishable)
  Tier 2 — Semantic  : consolidate() clusters here (ChromaDB / centroid cache)
  Tier 3 — Procedural: consolidate() may write here (LoRA .pt, weight-level)

Not every domain reaches Tier 3. Materials and Locus consolidate into
Tier 2 (ChromaDB summaries). Robotics, Aviation, and Basis go all the way
to Tier 3 (signed LoRA adapters). The ABC does not mandate which tiers
are populated — only that the cycle is defined.

Derivation note
---------------
All domain DMN implementations are Derivative Works of this interface.
Implementing projects must preserve the three-method contract and the
HMAC signing requirement on any durable artifacts produced by consolidate().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List


class AbstractDMN(ABC):
    """
    Abstract base class for all Snath DMN implementations.

    Subclass this in each domain project and implement the three
    abstract methods. The consolidation loop, fleet distribution,
    and adapter signing are domain responsibilities; this class
    enforces only that the interface exists.
    """

    # ------------------------------------------------------------------
    # Core three-phase cycle
    # ------------------------------------------------------------------

    @abstractmethod
    def ingest(self, event: Any) -> None:
        """
        Accept a domain event into the DMN's working memory (Tier 1).

        The event type is domain-specific:
          Robotics  — RoboticsDHardEvent (sensor divergence vectors)
          Materials — trajectory_log dict (JEPA heuristic)
          Locus     — routing decision record
          General   — log entry dict (role, content, timestamp)

        Implementations must be non-blocking. If writing to disk or a
        queue, failures should be caught and logged, not raised.
        """

    @abstractmethod
    def consolidate(self, **kwargs) -> List[dict]:
        """
        Process accumulated Tier-1 events into durable corrections (Tier 2/3).

        Called overnight, on threshold, or on demand. Returns a list of
        metadata dicts describing what was built — one dict per artifact
        (adapter, dream, summary). Empty list if nothing was built.

        Any durable artifact (LoRA .pt, ChromaDB entry, centroid cache)
        produced here MUST be HMAC-signed with a domain-specific key.
        The signature must be verifiable by the corresponding adapter router.
        """

    @abstractmethod
    def recall(self, query: Any, **kwargs) -> Any:
        """
        Retrieve relevant context from Tier 2 memory for the current cycle.

        The query type and return type are domain-specific:
          Robotics  — failure_class str → centroid dict
          Materials — query str → heuristic str (ChromaDB semantic search)
          General   — query str → narrative str

        Return None or an empty value (not an exception) when no relevant
        context exists. The inference spine must never block on recall.
        """

    # ------------------------------------------------------------------
    # Optional — default implementations
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """
        Return queue and memory statistics.

        Override to expose domain-specific metrics (queue depth, adapter
        count, cluster sizes). Default returns an empty dict so callers
        can always call stats() without checking the implementation.
        """
        return {}
