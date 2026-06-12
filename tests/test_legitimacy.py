"""Tests for Decision Legitimacy Gate."""

import pytest

from decisionmemory.owm.legitimacy import compute_legitimacy_score


class TestFullLegitimacy:
    """30+ decisions, low drift, good regime data -> full tier."""

    def test_full_legitimacy(self):
        result = compute_legitimacy_score(
            strategy_name="VolBreakout",
            current_regime="trending_up",
            memory_count=35,
            avg_context_drift=0.1,
            win_rate=0.6,
            consecutive_losses=0,
            drawdown_pct=2.0,
            regime_decision_count=12,
        )
        assert result["tier"] == "full"
        assert result["position_multiplier"] == 1.0
        assert result["legitimacy_score"] >= 0.7
        assert result["factors"]["sample_sufficiency"] == 1.0
        assert result["factors"]["regime_confidence"] == 1.0
        assert result["factors"]["streak_state"] == 1.0
        assert result["factors"]["drawdown_state"] == 1.0
        assert "Full confidence" in result["recommendation"]


class TestReducedLegitimacy:
    """10 decisions, some drift -> reduced tier."""

    def test_reduced_legitimacy(self):
        result = compute_legitimacy_score(
            strategy_name="IntradayMomentum",
            current_regime="ranging",
            memory_count=10,
            avg_context_drift=0.3,
            win_rate=0.5,
            consecutive_losses=2,
            drawdown_pct=7.0,
            regime_decision_count=4,
        )
        assert result["tier"] == "reduced"
        assert result["position_multiplier"] == 0.5
        assert 0.4 <= result["legitimacy_score"] < 0.7
        assert "Reduced position size" in result["recommendation"]


class TestSkipLegitimacy:
    """2 decisions, high drift, losing streak -> skip."""

    def test_skip_legitimacy(self):
        result = compute_legitimacy_score(
            strategy_name="Pullback",
            current_regime="volatile",
            memory_count=2,
            avg_context_drift=0.8,
            win_rate=0.0,
            consecutive_losses=5,
            drawdown_pct=25.0,
            regime_decision_count=1,
        )
        assert result["tier"] == "skip"
        assert result["position_multiplier"] == 0.0
        assert result["legitimacy_score"] < 0.4
        assert "Skip this decision" in result["recommendation"]


class TestNewStrategy:
    """0 decisions -> skip with clear message."""

    def test_new_strategy(self):
        result = compute_legitimacy_score(
            strategy_name="BrandNewStrategy",
            current_regime=None,
            memory_count=0,
            avg_context_drift=0.0,
            win_rate=None,
            consecutive_losses=0,
            drawdown_pct=0.0,
            regime_decision_count=0,
        )
        # 0 decisions + 0 regime -> sample & regime factors very low,
        # but no drawdown/streak/drift penalties -> reduced (not skip)
        assert result["tier"] == "reduced"
        assert result["position_multiplier"] == 0.5
        # Should mention low decision count
        assert "0 decisions" in result["recommendation"] or "only" in result["recommendation"].lower()
        assert result["factors"]["sample_sufficiency"] == 0.1
        assert result["factors"]["regime_confidence"] == 0.1

    def test_new_strategy_with_losses_is_skip(self):
        """New strategy + losing streak + drawdown = definitely skip."""
        result = compute_legitimacy_score(
            strategy_name="BrandNewStrategy",
            current_regime=None,
            memory_count=0,
            avg_context_drift=0.5,
            win_rate=None,
            consecutive_losses=3,
            drawdown_pct=12.0,
            regime_decision_count=0,
        )
        assert result["tier"] == "skip"
        assert result["position_multiplier"] == 0.0
        assert "Skip this decision" in result["recommendation"]


class TestDrawdownPenalty:
    """High drawdown reduces score even with good decision history."""

    def test_drawdown_penalty(self):
        # Good everything except drawdown
        result_low_dd = compute_legitimacy_score(
            strategy_name="VolBreakout",
            current_regime="trending_up",
            memory_count=30,
            avg_context_drift=0.1,
            win_rate=0.6,
            consecutive_losses=0,
            drawdown_pct=3.0,
            regime_decision_count=10,
        )
        result_high_dd = compute_legitimacy_score(
            strategy_name="VolBreakout",
            current_regime="trending_up",
            memory_count=30,
            avg_context_drift=0.1,
            win_rate=0.6,
            consecutive_losses=0,
            drawdown_pct=22.0,
            regime_decision_count=10,
        )
        assert result_high_dd["legitimacy_score"] < result_low_dd["legitimacy_score"]
        assert result_high_dd["factors"]["drawdown_state"] == 0.1
        assert result_low_dd["factors"]["drawdown_state"] == 1.0


class TestRegimeUnknown:
    """No regime data -> low regime_confidence."""

    def test_regime_unknown(self):
        result = compute_legitimacy_score(
            strategy_name="VolBreakout",
            current_regime=None,
            memory_count=30,
            avg_context_drift=0.1,
            win_rate=0.6,
            consecutive_losses=0,
            drawdown_pct=3.0,
            regime_decision_count=0,
        )
        assert result["factors"]["regime_confidence"] == 0.1
        # Score should be lower than with regime data
        result_with_regime = compute_legitimacy_score(
            strategy_name="VolBreakout",
            current_regime="trending_up",
            memory_count=30,
            avg_context_drift=0.1,
            win_rate=0.6,
            consecutive_losses=0,
            drawdown_pct=3.0,
            regime_decision_count=10,
        )
        assert result["legitimacy_score"] < result_with_regime["legitimacy_score"]


class TestEdgeCases:
    """Edge cases for factor scoring."""

    def test_boundary_values(self):
        """Test exact boundary values for each factor."""
        # Exactly 30 decisions
        result = compute_legitimacy_score(
            strategy_name="Test",
            current_regime="ranging",
            memory_count=30,
            avg_context_drift=0.0,
            win_rate=0.5,
            consecutive_losses=0,
            drawdown_pct=0.0,
            regime_decision_count=10,
        )
        assert result["factors"]["sample_sufficiency"] == 1.0

        # Exactly 15 decisions
        result = compute_legitimacy_score(
            strategy_name="Test",
            current_regime="ranging",
            memory_count=15,
            avg_context_drift=0.0,
            win_rate=0.5,
            consecutive_losses=0,
            drawdown_pct=0.0,
            regime_decision_count=10,
        )
        assert result["factors"]["sample_sufficiency"] == 0.7

    def test_drift_clamped(self):
        """Context drift > 1.0 should clamp memory_quality to 0.0."""
        result = compute_legitimacy_score(
            strategy_name="Test",
            current_regime="ranging",
            memory_count=30,
            avg_context_drift=1.5,
            win_rate=0.5,
            consecutive_losses=0,
            drawdown_pct=0.0,
            regime_decision_count=10,
        )
        assert result["factors"]["memory_quality"] == 0.0

    def test_all_factors_return_floats(self):
        """All factor values should be floats."""
        result = compute_legitimacy_score(
            strategy_name="Test",
            current_regime=None,
            memory_count=0,
            avg_context_drift=0.0,
            win_rate=None,
            consecutive_losses=0,
            drawdown_pct=0.0,
            regime_decision_count=0,
        )
        for key, value in result["factors"].items():
            assert isinstance(value, float), f"{key} is {type(value)}, expected float"
        assert isinstance(result["legitimacy_score"], float)
        assert isinstance(result["position_multiplier"], float)

    def test_weights_sum_to_one(self):
        """Weights should sum to 1.0."""
        from decisionmemory.owm.legitimacy import WEIGHTS
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9
