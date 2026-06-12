"""Tests for RegimeAwareNull."""
from __future__ import annotations

import pytest

from decisionmemory.ssrt.models import DecisionResult
from decisionmemory.ssrt.regime import RegimeAwareNull


def _make_decision(pnl_r: float, regime: str = "trending_up") -> DecisionResult:
    return DecisionResult(
        pnl=pnl_r * 100,
        pnl_r=pnl_r,
        regime=regime,
        timestamp="2026-01-01T00:00:00Z",
        strategy="test",
        symbol="XAUUSD",
    )


class TestRegimeAwareNull:

    def test_update_builds_baselines(self):
        """Adding decisions should build correct baselines."""
        r = RegimeAwareNull(min_decisions_per_regime=3)
        for val in [1.0, 2.0, 3.0]:
            r.update(_make_decision(val, "trending_up"))

        baselines = r.get_baselines()
        assert "trending_up" in baselines
        assert baselines["trending_up"].mean_pnl_r == pytest.approx(2.0)
        assert baselines["trending_up"].decision_count == 3

    def test_insufficient_data_uses_default(self):
        """With <min_decisions in a regime, get_null returns default."""
        r = RegimeAwareNull(min_decisions_per_regime=10)
        for i in range(5):
            r.update(_make_decision(float(i), "ranging"))

        null_mean, sigma = r.get_null("ranging")
        assert null_mean == 0.0  # default_null

    def test_sufficient_data_uses_regime_mean(self):
        """With >=min_decisions, get_null returns regime-specific mean."""
        r = RegimeAwareNull(min_decisions_per_regime=5)
        for _ in range(10):
            r.update(_make_decision(1.5, "trending_up"))

        null_mean, sigma = r.get_null("trending_up")
        assert null_mean == pytest.approx(1.5)

    def test_multi_regime_independence(self):
        """Decisions in one regime don't affect another."""
        r = RegimeAwareNull(min_decisions_per_regime=5)
        for _ in range(10):
            r.update(_make_decision(2.0, "trending_up"))
        for _ in range(10):
            r.update(_make_decision(-1.0, "ranging"))

        up_mean, _ = r.get_null("trending_up")
        rng_mean, _ = r.get_null("ranging")
        assert up_mean == pytest.approx(2.0)
        assert rng_mean == pytest.approx(-1.0)

    def test_invalid_regime_raises(self):
        """Unknown regime should raise ValueError."""
        r = RegimeAwareNull()
        with pytest.raises(ValueError, match="Unknown regime"):
            r.get_null("sideways")
        with pytest.raises(ValueError, match="Unknown regime"):
            r.update(_make_decision(1.0, "invalid_regime"))

    def test_serialization_roundtrip(self):
        """State persistence works correctly."""
        r1 = RegimeAwareNull(min_decisions_per_regime=5)
        for _ in range(10):
            r1.update(_make_decision(1.0, "trending_up"))

        state = r1.get_state()
        r2 = RegimeAwareNull.from_state(state)

        null1 = r1.get_null("trending_up")
        null2 = r2.get_null("trending_up")
        assert null1[0] == pytest.approx(null2[0])
        assert null1[1] == pytest.approx(null2[1])
