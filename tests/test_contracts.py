"""
Contract tests for the two Lár DMN abstract base classes.

These tests verify structural guarantees — not any concrete implementation.
All imports are stdlib; no external dependencies required.
"""
import datetime
import math
import pytest

from brain.abstract_dmn import AbstractDMN
from brain.abstract_adapter_router import AbstractAdapterRouter


# ── Minimal concrete stubs ────────────────────────────────────────────────────

class _StubDMN(AbstractDMN):
    def ingest(self, event) -> None: pass
    def consolidate(self, **kwargs): return []
    def recall(self, query=None, **kwargs): return ""
    def stats(self) -> dict: return {}


class _StubRouter(AbstractAdapterRouter):
    def _load_all(self) -> None: pass
    def _nearest(self, delta): return None
    def resolve(self, z_a, z_b, base_decision, conf_a, conf_b, enc_a=None, enc_b=None):
        return base_decision, "stub"
    def available(self): return []


# ── AbstractDMN ──────────────────────────────────────────────────────────────

class TestAbstractDMN:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            AbstractDMN()

    def test_concrete_subclass_instantiates(self):
        assert isinstance(_StubDMN(), AbstractDMN)

    def test_missing_ingest_raises(self):
        class Bad(AbstractDMN):
            def consolidate(self, **kwargs): return []
            def recall(self, query=None, **kwargs): return ""
            def stats(self): return {}
        with pytest.raises(TypeError):
            Bad()

    def test_missing_consolidate_raises(self):
        class Bad(AbstractDMN):
            def ingest(self, event): pass
            def recall(self, query=None, **kwargs): return ""
            def stats(self): return {}
        with pytest.raises(TypeError):
            Bad()

    def test_missing_recall_raises(self):
        class Bad(AbstractDMN):
            def ingest(self, event): pass
            def consolidate(self, **kwargs): return []
            def stats(self): return {}
        with pytest.raises(TypeError):
            Bad()

    def test_stats_has_default_implementation(self):
        dmn = _StubDMN()
        assert isinstance(dmn.stats(), dict)


# ── AbstractAdapterRouter ────────────────────────────────────────────────────

class TestAbstractAdapterRouter:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            AbstractAdapterRouter()

    def test_concrete_subclass_instantiates(self):
        assert isinstance(_StubRouter(), AbstractAdapterRouter)

    def test_refresh_calls_load_all(self, monkeypatch):
        called = []
        router = _StubRouter()
        monkeypatch.setattr(router, "_load_all", lambda: called.append(1))
        router.refresh()
        assert called == [1]

    def test_missing_load_all_raises(self):
        class Bad(AbstractAdapterRouter):
            def _nearest(self, delta): return None
            def resolve(self, z_a, z_b, base_decision, conf_a, conf_b, enc_a=None, enc_b=None):
                return base_decision, ""
            def available(self): return []
        with pytest.raises(TypeError):
            Bad()

    def test_missing_nearest_raises(self):
        class Bad(AbstractAdapterRouter):
            def _load_all(self): pass
            def resolve(self, z_a, z_b, base_decision, conf_a, conf_b, enc_a=None, enc_b=None):
                return base_decision, ""
            def available(self): return []
        with pytest.raises(TypeError):
            Bad()


# ── decay_weight ─────────────────────────────────────────────────────────────

class TestDecayWeight:
    def test_none_returns_one(self):
        assert AbstractAdapterRouter.decay_weight(None) == 1.0

    def test_empty_string_returns_one(self):
        assert AbstractAdapterRouter.decay_weight("") == 1.0

    def test_future_timestamp_returns_one(self):
        future = (
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        ).isoformat()
        assert AbstractAdapterRouter.decay_weight(future) == 1.0

    def test_two_year_old_adapter_decays(self):
        old = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=730)
        ).isoformat()
        w = AbstractAdapterRouter.decay_weight(old, lam=0.10)
        assert abs(w - math.exp(-0.10 * 2.0)) < 0.01

    def test_high_lambda_decays_faster(self):
        ts = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)
        ).isoformat()
        assert AbstractAdapterRouter.decay_weight(ts, lam=0.50) < AbstractAdapterRouter.decay_weight(ts, lam=0.02)

    def test_malformed_timestamp_returns_one(self):
        assert AbstractAdapterRouter.decay_weight("not-a-date") == 1.0

    def test_lambda_table_slow_structural(self):
        ts = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)
        ).isoformat()
        w = AbstractAdapterRouter.decay_weight(ts, lam=0.02)
        assert w > 0.97

    def test_lambda_table_fast_environmental(self):
        ts = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)
        ).isoformat()
        w = AbstractAdapterRouter.decay_weight(ts, lam=0.50)
        assert w < 0.61
