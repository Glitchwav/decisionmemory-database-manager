"""Tests for new OWM MCP tools: behavioral analysis, agent state, decision_making plans."""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

_tmpdir = tempfile.mkdtemp()
_test_db = os.path.join(_tmpdir, "test_owm_new_tools.db")


@pytest.fixture(autouse=True)
def _fresh_db(monkeypatch):
    """Use a fresh temp database for each test."""
    import decisionmemory.mcp_server as mod
    from decisionmemory.db import Database

    db = Database(db_path=_test_db)
    mod._db = db
    yield
    mod._db = None
    if os.path.exists(_test_db):
        os.remove(_test_db)


# ---------------------------------------------------------------------------
# Helper: store a decision to populate procedural + affective
# ---------------------------------------------------------------------------


async def _store_decision(
    symbol="XAUUSD",
    direction="long",
    entry_price=2650.0,
    exit_price=2670.0,
    pnl=200.0,
    strategy_name="VolBreakout",
    market_context="breakout",
    confidence=0.5,
    decision_id=None,
):
    from decisionmemory.mcp_server import remember_decision

    return await remember_decision(
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        exit_price=exit_price,
        pnl=pnl,
        strategy_name=strategy_name,
        market_context=market_context,
        confidence=confidence,
        decision_id=decision_id,
    )


# ===========================================================================
# get_behavioral_analysis
# ===========================================================================


@pytest.mark.asyncio
async def test_behavioral_analysis_no_data():
    from decisionmemory.mcp_server import get_behavioral_analysis

    result = await get_behavioral_analysis()
    assert result["status"] == "no_data"
    assert "message" in result


@pytest.mark.asyncio
async def test_behavioral_analysis_with_data():
    from decisionmemory.mcp_server import get_behavioral_analysis

    await _store_decision(strategy_name="VolBreakout", symbol="XAUUSD")

    result = await get_behavioral_analysis()
    assert result["status"] == "ok"
    assert result["count"] >= 1
    b = result["behaviors"][0]
    assert b["strategy"] == "VolBreakout"
    assert b["symbol"] == "XAUUSD"
    assert b["sample_size"] == 1
    assert "avg_hold_winners" in b
    assert "avg_hold_losers" in b
    assert "disposition_ratio" in b
    assert "lot_sizing_variance" in b
    assert "kelly_fraction_suggested" in b
    assert "lot_vs_kelly_ratio" in b


@pytest.mark.asyncio
async def test_behavioral_analysis_filter_strategy():
    from decisionmemory.mcp_server import get_behavioral_analysis

    await _store_decision(strategy_name="VolBreakout", decision_id="ba-vb-001")
    await _store_decision(strategy_name="IntradayMomentum", decision_id="ba-im-001")

    result = await get_behavioral_analysis(strategy_name="VolBreakout")
    assert result["status"] == "ok"
    for b in result["behaviors"]:
        assert b["strategy"] == "VolBreakout"


@pytest.mark.asyncio
async def test_behavioral_analysis_filter_symbol():
    from decisionmemory.mcp_server import get_behavioral_analysis

    await _store_decision(symbol="XAUUSD", decision_id="ba-xau-001")
    await _store_decision(symbol="EURUSD", entry_price=1.08, exit_price=1.09, decision_id="ba-eur-001")

    result = await get_behavioral_analysis(symbol="XAUUSD")
    assert result["status"] == "ok"
    for b in result["behaviors"]:
        assert b["symbol"] == "XAUUSD"


@pytest.mark.asyncio
async def test_behavioral_analysis_sample_size_increments():
    from decisionmemory.mcp_server import get_behavioral_analysis

    await _store_decision(decision_id="ba-inc-001")
    await _store_decision(decision_id="ba-inc-002")

    result = await get_behavioral_analysis(strategy_name="VolBreakout", symbol="XAUUSD")
    assert result["behaviors"][0]["sample_size"] == 2


# ===========================================================================
# get_agent_state
# ===========================================================================


@pytest.mark.asyncio
async def test_agent_state_empty_initializes():
    from decisionmemory.mcp_server import get_agent_state

    result = await get_agent_state()
    assert result["status"] == "ok"
    assert result["confidence_level"] == 0.5
    assert result["risk_appetite"] == 1.0
    assert result["drawdown_pct"] == 0.0
    assert result["consecutive_wins"] == 0
    assert result["consecutive_losses"] == 0
    assert result["recommended_action"] == "normal"


@pytest.mark.asyncio
async def test_agent_state_after_wins():
    from decisionmemory.mcp_server import get_agent_state

    await _store_decision(pnl=200.0, confidence=0.8, decision_id="as-w1")
    await _store_decision(pnl=150.0, confidence=0.7, decision_id="as-w2")

    result = await get_agent_state()
    assert result["status"] == "ok"
    assert result["consecutive_wins"] == 2
    assert result["consecutive_losses"] == 0
    assert result["recommended_action"] == "normal"


@pytest.mark.asyncio
async def test_agent_state_after_losses():
    from decisionmemory.mcp_server import get_agent_state

    await _store_decision(pnl=-200.0, decision_id="as-l1")
    await _store_decision(pnl=-150.0, decision_id="as-l2")

    result = await get_agent_state()
    assert result["status"] == "ok"
    assert result["consecutive_wins"] == 0
    assert result["consecutive_losses"] == 2


@pytest.mark.asyncio
async def test_agent_state_recommended_action_reduce_size():
    """Force drawdown between 0.3 and 0.6 → reduce_size."""
    from decisionmemory.mcp_server import get_agent_state, _get_db

    db = _get_db()
    db.init_affective(peak_score=10000.0, current_score=10000.0)
    db.save_affective({
        "confidence_level": 0.3,
        "risk_appetite": 0.5,
        "momentum_bias": 0.0,
        "peak_score": 10000.0,
        "current_score": 6000.0,
        "drawdown_state": 0.4,
        "max_acceptable_drawdown": 0.20,
        "consecutive_wins": 0,
        "consecutive_losses": 5,
        "history_json": [],
    })

    result = await get_agent_state()
    assert result["recommended_action"] == "reduce_size"
    assert result["drawdown_pct"] == 0.4


@pytest.mark.asyncio
async def test_agent_state_recommended_action_stop_decision_making():
    """Force drawdown > 0.6 → stop_decision_making."""
    from decisionmemory.mcp_server import get_agent_state, _get_db

    db = _get_db()
    db.init_affective(peak_score=10000.0, current_score=10000.0)
    db.save_affective({
        "confidence_level": 0.1,
        "risk_appetite": 0.2,
        "momentum_bias": 0.0,
        "peak_score": 10000.0,
        "current_score": 3000.0,
        "drawdown_state": 0.7,
        "max_acceptable_drawdown": 0.20,
        "consecutive_wins": 0,
        "consecutive_losses": 10,
        "history_json": [],
    })

    result = await get_agent_state()
    assert result["recommended_action"] == "stop_decision_making"
    assert result["drawdown_pct"] == 0.7


@pytest.mark.asyncio
async def test_agent_state_score_tracking():
    from decisionmemory.mcp_server import get_agent_state

    await _store_decision(pnl=500.0, decision_id="eq-001")

    result = await get_agent_state()
    assert result["current_score"] == 10500.0
    assert result["peak_score"] == 10500.0


# ===========================================================================
# create_decision_making_plan
# ===========================================================================


@pytest.mark.asyncio
async def test_create_plan_basic():
    from decisionmemory.mcp_server import create_decision_making_plan

    result = await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "ranging"}',
        planned_action='{"type": "skip_decision", "strategy": "VolBreakout"}',
        reasoning="VB underperforms in ranging markets",
    )
    assert result["status"] == "active"
    assert "plan_id" in result
    assert result["plan_id"].startswith("plan-")
    assert "expiry" in result
    assert "message" in result


@pytest.mark.asyncio
async def test_create_plan_custom_expiry():
    from decisionmemory.mcp_server import create_decision_making_plan

    result = await create_decision_making_plan(
        trigger_type="time_based",
        trigger_condition='{"hour": 10}',
        planned_action='{"type": "reduce_lot"}',
        reasoning="Low volume after 10 AM",
        expiry_days=7,
    )
    assert result["status"] == "active"
    # Expiry should be ~7 days from now
    expiry_dt = datetime.fromisoformat(result["expiry"])
    now = datetime.now(timezone.utc)
    delta = expiry_dt - now
    assert 6 <= delta.days <= 7


@pytest.mark.asyncio
async def test_create_plan_custom_priority():
    from decisionmemory.mcp_server import create_decision_making_plan, _get_db

    await create_decision_making_plan(
        trigger_type="drawdown",
        trigger_condition='{"drawdown_pct_min": 0.3}',
        planned_action='{"type": "stop_decision_making"}',
        reasoning="Circuit breaker",
        priority=0.9,
    )
    db = _get_db()
    plans = db.query_prospective(status="active")
    assert len(plans) == 1
    assert plans[0]["priority"] == 0.9


@pytest.mark.asyncio
async def test_create_plan_invalid_trigger_json():
    from decisionmemory.mcp_server import create_decision_making_plan

    result = await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition="not valid json {",
        planned_action='{"type": "skip"}',
        reasoning="test",
    )
    assert "error" in result


@pytest.mark.asyncio
async def test_create_plan_invalid_action_json():
    from decisionmemory.mcp_server import create_decision_making_plan

    result = await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "ranging"}',
        planned_action="not valid json",
        reasoning="test",
    )
    assert "error" in result


@pytest.mark.asyncio
async def test_create_plan_stored_in_db():
    from decisionmemory.mcp_server import create_decision_making_plan, _get_db

    result = await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "ranging", "strategy": "VolBreakout"}',
        planned_action='{"type": "skip_decision", "reason": "low edge"}',
        reasoning="VB has poor performance in ranging markets",
    )
    db = _get_db()
    plans = db.query_prospective(status="active")
    assert len(plans) == 1
    p = plans[0]
    assert p["id"] == result["plan_id"]
    assert p["trigger_type"] == "market_condition"
    assert p["trigger_condition"]["regime"] == "ranging"
    assert p["planned_action"]["type"] == "skip_decision"
    assert p["reasoning"] == "VB has poor performance in ranging markets"


# ===========================================================================
# check_active_plans
# ===========================================================================


@pytest.mark.asyncio
async def test_check_plans_empty():
    from decisionmemory.mcp_server import check_active_plans

    result = await check_active_plans()
    assert result["active_count"] == 0
    assert result["triggered"] == []
    assert result["pending"] == []


@pytest.mark.asyncio
async def test_check_plans_triggered_by_regime():
    from decisionmemory.mcp_server import create_decision_making_plan, check_active_plans

    await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "ranging"}',
        planned_action='{"type": "skip_decision"}',
        reasoning="test",
    )

    result = await check_active_plans(context_regime="ranging")
    assert result["active_count"] == 1
    assert len(result["triggered"]) == 1
    assert len(result["pending"]) == 0
    assert result["triggered"][0]["trigger_condition"]["regime"] == "ranging"


@pytest.mark.asyncio
async def test_check_plans_not_triggered_by_different_regime():
    from decisionmemory.mcp_server import create_decision_making_plan, check_active_plans

    await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "ranging"}',
        planned_action='{"type": "skip_decision"}',
        reasoning="test",
    )

    result = await check_active_plans(context_regime="trending_up")
    assert result["active_count"] == 1
    assert len(result["triggered"]) == 0
    assert len(result["pending"]) == 1


@pytest.mark.asyncio
async def test_check_plans_atr_filtering():
    from decisionmemory.mcp_server import create_decision_making_plan, check_active_plans

    await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"atr_d1_min": 100, "atr_d1_max": 200}',
        planned_action='{"type": "increase_size"}',
        reasoning="Good volatility range",
    )

    # Within range → triggered
    result = await check_active_plans(context_atr_d1=150.0)
    assert len(result["triggered"]) == 1

    # Below range → pending
    result = await check_active_plans(context_atr_d1=50.0)
    assert len(result["triggered"]) == 0
    assert len(result["pending"]) == 1

    # Above range → pending
    result = await check_active_plans(context_atr_d1=250.0)
    assert len(result["triggered"]) == 0
    assert len(result["pending"]) == 1


@pytest.mark.asyncio
async def test_check_plans_expired_auto_removed():
    from decisionmemory.mcp_server import create_decision_making_plan, check_active_plans, _get_db

    # Create plan with 0-day expiry (already expired)
    result = await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "ranging"}',
        planned_action='{"type": "skip_decision"}',
        reasoning="test",
        expiry_days=0,
    )

    # Manually set expiry to the past
    db = _get_db()
    past_expiry = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    db.update_prospective_status(result["plan_id"], "active")
    # Directly update expiry in DB
    conn = db._get_connection()
    try:
        conn.execute(
            "UPDATE prospective_memory SET expiry = ? WHERE id = ?",
            (past_expiry, result["plan_id"]),
        )
        conn.commit()
    finally:
        conn.close()

    check = await check_active_plans(context_regime="ranging")
    assert check["active_count"] == 0
    assert len(check["triggered"]) == 0

    # Verify it was marked expired in DB
    expired = db.query_prospective(status="expired")
    assert len(expired) == 1


@pytest.mark.asyncio
async def test_check_plans_multiple_plans():
    from decisionmemory.mcp_server import create_decision_making_plan, check_active_plans

    # Plan 1: triggers on ranging
    await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "ranging"}',
        planned_action='{"type": "skip_vb"}',
        reasoning="VB bad in ranging",
    )
    # Plan 2: triggers on trending_up
    await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "trending_up"}',
        planned_action='{"type": "increase_im"}',
        reasoning="IM great in trends",
    )

    result = await check_active_plans(context_regime="ranging")
    assert result["active_count"] == 2
    assert len(result["triggered"]) == 1
    assert len(result["pending"]) == 1
    assert result["triggered"][0]["planned_action"]["type"] == "skip_vb"


@pytest.mark.asyncio
async def test_check_plans_no_context_with_conditions():
    """When no context is provided but plan has conditions, it should be pending."""
    from decisionmemory.mcp_server import create_decision_making_plan, check_active_plans

    await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "ranging"}',
        planned_action='{"type": "skip_decision"}',
        reasoning="test",
    )

    result = await check_active_plans()
    assert result["active_count"] == 1
    assert len(result["triggered"]) == 0
    assert len(result["pending"]) == 1


@pytest.mark.asyncio
async def test_check_plans_empty_condition_always_triggers():
    """Plan with empty trigger_condition should always match."""
    from decisionmemory.mcp_server import create_decision_making_plan, check_active_plans

    await create_decision_making_plan(
        trigger_type="always",
        trigger_condition='{}',
        planned_action='{"type": "log_state"}',
        reasoning="Always check",
    )

    result = await check_active_plans(context_regime="trending_up")
    assert len(result["triggered"]) == 1


@pytest.mark.asyncio
async def test_check_plans_combined_regime_and_atr():
    from decisionmemory.mcp_server import create_decision_making_plan, check_active_plans

    await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "trending_up", "atr_d1_min": 100}',
        planned_action='{"type": "go_big"}',
        reasoning="Strong trend + high vol",
    )

    # Both match
    result = await check_active_plans(context_regime="trending_up", context_atr_d1=150.0)
    assert len(result["triggered"]) == 1

    # Regime matches but ATR too low
    result = await check_active_plans(context_regime="trending_up", context_atr_d1=50.0)
    assert len(result["triggered"]) == 0

    # ATR matches but wrong regime
    result = await check_active_plans(context_regime="ranging", context_atr_d1=150.0)
    assert len(result["triggered"]) == 0


# ===========================================================================
# Integration: full workflow
# ===========================================================================


@pytest.mark.asyncio
async def test_full_workflow():
    """Store decisions → check behavioral analysis → check agent state → create plan → check plans."""
    from decisionmemory.mcp_server import (
        get_behavioral_analysis,
        get_agent_state,
        create_decision_making_plan,
        check_active_plans,
    )

    # Store some decisions
    await _store_decision(pnl=200.0, confidence=0.8, decision_id="fw-001")
    await _store_decision(pnl=-100.0, confidence=0.4, decision_id="fw-002")
    await _store_decision(pnl=300.0, confidence=0.9, decision_id="fw-003")

    # Check behavioral analysis
    ba = await get_behavioral_analysis(strategy_name="VolBreakout")
    assert ba["status"] == "ok"
    assert ba["behaviors"][0]["sample_size"] == 3

    # Check agent state
    state = await get_agent_state()
    assert state["status"] == "ok"
    assert state["consecutive_wins"] == 1  # last decision was a win
    assert state["recommended_action"] == "normal"

    # Create a plan
    plan = await create_decision_making_plan(
        trigger_type="market_condition",
        trigger_condition='{"regime": "ranging"}',
        planned_action='{"type": "skip_decision", "strategy": "VolBreakout"}',
        reasoning="VB underperforms in ranging",
    )
    assert plan["status"] == "active"

    # Check plans — should trigger
    check = await check_active_plans(context_regime="ranging")
    assert check["active_count"] == 1
    assert len(check["triggered"]) == 1

    # Check plans — should not trigger
    check = await check_active_plans(context_regime="trending_up")
    assert check["active_count"] == 1
    assert len(check["triggered"]) == 0
    assert len(check["pending"]) == 1
