"""Tests for OWM-powered MCP tools: remember_decision and recall_memories."""

import asyncio
import os
import tempfile

import pytest

_tmpdir = tempfile.mkdtemp()
_test_db = os.path.join(_tmpdir, "test_owm_decisionmemory.db")


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


# -- remember_decision --


@pytest.mark.asyncio
async def test_remember_decision_basic():
    from decisionmemory.mcp_server import remember_decision

    result = await remember_decision(
        symbol="XAUUSD",
        direction="long",
        entry_price=2650.0,
        exit_price=2670.0,
        pnl=200.0,
        strategy_name="VolBreakout",
        market_context="Asian session breakout with high ATR",
    )
    assert result["status"] == "stored"
    assert result["symbol"] == "XAUUSD"
    assert result["direction"] == "long"
    assert result["strategy"] == "VolBreakout"
    assert "episodic" in result["memory_layers"]
    assert "decision_records" in result["memory_layers"]


@pytest.mark.asyncio
async def test_remember_decision_invalid_direction():
    from decisionmemory.mcp_server import remember_decision

    result = await remember_decision(
        symbol="XAUUSD",
        direction="sideways",
        entry_price=2650.0,
        exit_price=2670.0,
        pnl=200.0,
        strategy_name="VolBreakout",
        market_context="test",
    )
    assert "error" in result


@pytest.mark.asyncio
async def test_remember_decision_custom_id():
    from decisionmemory.mcp_server import remember_decision

    result = await remember_decision(
        symbol="XAUUSD",
        direction="long",
        entry_price=2650.0,
        exit_price=2670.0,
        pnl=200.0,
        strategy_name="VolBreakout",
        market_context="test",
        decision_id="custom-owm-001",
    )
    assert result["memory_id"] == "custom-owm-001"


@pytest.mark.asyncio
async def test_remember_decision_writes_episodic():
    """Verify episodic_memory row is created."""
    from decisionmemory.mcp_server import remember_decision, _get_db

    await remember_decision(
        symbol="XAUUSD",
        direction="long",
        entry_price=2650.0,
        exit_price=2670.0,
        pnl=200.0,
        strategy_name="VolBreakout",
        market_context="breakout",
        decision_id="ep-check-001",
    )
    db = _get_db()
    rows = db.query_episodic(strategy="VolBreakout", limit=10)
    assert len(rows) >= 1
    found = [r for r in rows if r["id"] == "ep-check-001"]
    assert len(found) == 1
    assert found[0]["pnl"] == 200.0


@pytest.mark.asyncio
async def test_remember_decision_writes_decision_records():
    """Verify backward-compat decision_records row is created."""
    from decisionmemory.mcp_server import remember_decision, _get_db

    await remember_decision(
        symbol="XAUUSD",
        direction="short",
        entry_price=2700.0,
        exit_price=2680.0,
        pnl=200.0,
        strategy_name="IntradayMomentum",
        market_context="London open",
        decision_id="tr-compat-001",
    )
    db = _get_db()
    decision = db.get_decision("tr-compat-001")
    assert decision is not None
    assert decision["symbol"] == "XAUUSD"
    assert decision["pnl"] == 200.0


@pytest.mark.asyncio
async def test_remember_decision_creates_semantic():
    """Verify semantic memory is created on first decision."""
    from decisionmemory.mcp_server import remember_decision, _get_db

    await remember_decision(
        symbol="XAUUSD",
        direction="long",
        entry_price=2650.0,
        exit_price=2670.0,
        pnl=200.0,
        strategy_name="VolBreakout",
        market_context="test",
    )
    db = _get_db()
    sems = db.query_semantic(strategy="VolBreakout", symbol="XAUUSD", limit=10)
    assert len(sems) >= 1
    sem = sems[0]
    # Winning decision → alpha should be > initial 1.0
    assert sem["alpha"] > 1.0


@pytest.mark.asyncio
async def test_remember_decision_bayesian_update_loss():
    """Verify losing decision increases beta."""
    from decisionmemory.mcp_server import remember_decision, _get_db

    # First decision (creates semantic)
    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, strategy_name="VB",
        market_context="test",
    )
    # Second decision: loss
    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2660.0,
        exit_price=2640.0, pnl=-200.0, strategy_name="VB",
        market_context="test",
    )
    db = _get_db()
    sems = db.query_semantic(strategy="VB", symbol="XAUUSD", limit=10)
    assert len(sems) >= 1
    sem = sems[0]
    # Both alpha and beta should have been incremented
    assert sem["alpha"] > 1.0
    assert sem["beta"] > 1.0
    assert sem["sample_size"] >= 2


@pytest.mark.asyncio
async def test_remember_decision_updates_procedural():
    """Verify procedural memory is created/updated."""
    from decisionmemory.mcp_server import remember_decision, _get_db

    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, strategy_name="VolBreakout",
        market_context="test",
    )
    db = _get_db()
    procs = db.query_procedural(strategy="VolBreakout", symbol="XAUUSD", limit=10)
    assert len(procs) >= 1
    assert procs[0]["sample_size"] == 1

    # Second decision updates running average
    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2660.0,
        exit_price=2680.0, pnl=200.0, strategy_name="VolBreakout",
        market_context="test",
    )
    procs = db.query_procedural(strategy="VolBreakout", symbol="XAUUSD", limit=10)
    assert procs[0]["sample_size"] == 2


@pytest.mark.asyncio
async def test_remember_decision_updates_affective():
    """Verify affective state is initialized and updated."""
    from decisionmemory.mcp_server import remember_decision, _get_db

    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, strategy_name="VB",
        market_context="test", confidence=0.8,
    )
    db = _get_db()
    aff = db.load_affective()
    assert aff is not None
    assert aff["consecutive_wins"] == 1
    assert aff["consecutive_losses"] == 0
    # EWMA: 0.3 * 0.8 + 0.7 * 0.5 = 0.59
    assert 0.55 < aff["confidence_level"] < 0.65


@pytest.mark.asyncio
async def test_remember_decision_affective_streaks():
    """Verify win/loss streak tracking."""
    from decisionmemory.mcp_server import remember_decision, _get_db

    # 2 wins
    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, strategy_name="VB",
        market_context="test",
    )
    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2660.0,
        exit_price=2680.0, pnl=200.0, strategy_name="VB",
        market_context="test",
    )
    db = _get_db()
    aff = db.load_affective()
    assert aff["consecutive_wins"] == 2
    assert aff["consecutive_losses"] == 0

    # 1 loss resets wins
    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2680.0,
        exit_price=2660.0, pnl=-200.0, strategy_name="VB",
        market_context="test",
    )
    aff = db.load_affective()
    assert aff["consecutive_wins"] == 0
    assert aff["consecutive_losses"] == 1


@pytest.mark.asyncio
async def test_remember_decision_with_pnl_r():
    """Verify pnl_r is stored in episodic and used for semantic weight."""
    from decisionmemory.mcp_server import remember_decision, _get_db

    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, pnl_r=1.5,
        strategy_name="VB", market_context="test",
        decision_id="pnlr-001",
    )
    db = _get_db()
    rows = db.query_episodic(strategy="VB", limit=10)
    found = [r for r in rows if r["id"] == "pnlr-001"]
    assert found[0]["pnl_r"] == 1.5


# -- recall_memories --


@pytest.mark.asyncio
async def test_recall_memories_empty():
    from decisionmemory.mcp_server import recall_memories

    result = await recall_memories(
        symbol="XAUUSD",
        market_context="breakout",
    )
    assert result["matches_found"] == 0
    assert result["memories"] == []


@pytest.mark.asyncio
async def test_recall_memories_with_episodic():
    from decisionmemory.mcp_server import remember_decision, recall_memories

    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, pnl_r=1.5,
        strategy_name="VolBreakout", market_context="breakout high ATR",
        context_regime="trending_up", context_atr_d1=150.0,
    )

    result = await recall_memories(
        symbol="XAUUSD",
        market_context="breakout high ATR",
        context_regime="trending_up",
        context_atr_d1=150.0,
    )
    assert result["matches_found"] >= 1
    mem = result["memories"][0]
    assert mem["memory_type"] == "episodic"
    assert "score" in mem
    assert "components" in mem
    assert "Q" in mem["components"]
    assert "Sim" in mem["components"]
    assert "Rec" in mem["components"]


@pytest.mark.asyncio
async def test_recall_memories_with_semantic():
    from decisionmemory.mcp_server import remember_decision, recall_memories

    # Store a decision to create semantic memory
    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, strategy_name="VolBreakout",
        market_context="test",
    )

    result = await recall_memories(
        symbol="XAUUSD",
        market_context="test",
        memory_types=["semantic"],
    )
    assert result["matches_found"] >= 1
    sem = result["memories"][0]
    assert sem["memory_type"] == "semantic"
    assert "proposition" in sem


@pytest.mark.asyncio
async def test_recall_memories_owm_scoring_ranks_winners_higher():
    """Store 3 decisions: 1 big win, 1 small win, 1 loss. OWM should rank big win highest."""
    from decisionmemory.mcp_server import remember_decision, recall_memories

    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2680.0, pnl=300.0, pnl_r=2.0,
        strategy_name="VB", market_context="breakout",
        context_regime="trending_up", context_atr_d1=150.0,
        decision_id="big-win",
    )
    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2655.0, pnl=50.0, pnl_r=0.3,
        strategy_name="VB", market_context="breakout",
        context_regime="trending_up", context_atr_d1=150.0,
        decision_id="small-win",
    )
    await remember_decision(
        symbol="XAUUSD", direction="short", entry_price=2650.0,
        exit_price=2670.0, pnl=-200.0, pnl_r=-1.5,
        strategy_name="VB", market_context="breakout",
        context_regime="trending_up", context_atr_d1=150.0,
        decision_id="loss",
    )

    result = await recall_memories(
        symbol="XAUUSD",
        market_context="breakout",
        context_regime="trending_up",
        context_atr_d1=150.0,
        memory_types=["episodic"],
    )
    assert result["matches_found"] >= 3

    episodic_results = [m for m in result["memories"] if m["memory_type"] == "episodic"]
    assert len(episodic_results) >= 3

    # Big win should have highest Q component
    big_win = next(m for m in episodic_results if m["memory_id"] == "big-win")
    loss = next(m for m in episodic_results if m["memory_id"] == "loss")
    assert big_win["components"]["Q"] > loss["components"]["Q"]
    assert big_win["score"] > loss["score"]


@pytest.mark.asyncio
async def test_recall_memories_symbol_filter():
    """Ensure only matching symbol is returned."""
    from decisionmemory.mcp_server import remember_decision, recall_memories

    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, strategy_name="VB",
        market_context="test", decision_id="gold-001",
    )
    await remember_decision(
        symbol="EURUSD", direction="long", entry_price=1.08,
        exit_price=1.09, pnl=100.0, strategy_name="VB",
        market_context="test", decision_id="eur-001",
    )

    result = await recall_memories(
        symbol="XAUUSD",
        market_context="test",
        memory_types=["episodic"],
    )
    ep_ids = [m["memory_id"] for m in result["memories"] if m["memory_type"] == "episodic"]
    assert "gold-001" in ep_ids
    assert "eur-001" not in ep_ids


@pytest.mark.asyncio
async def test_recall_memories_strategy_filter():
    from decisionmemory.mcp_server import remember_decision, recall_memories

    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, strategy_name="VolBreakout",
        market_context="test",
    )
    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2660.0, pnl=100.0, strategy_name="IntradayMomentum",
        market_context="test",
    )

    result = await recall_memories(
        symbol="XAUUSD",
        market_context="test",
        strategy_name="VolBreakout",
        memory_types=["episodic"],
    )
    for m in result["memories"]:
        if m["memory_type"] == "episodic":
            assert m["strategy"] == "VolBreakout"


@pytest.mark.asyncio
async def test_recall_memories_includes_affective_state():
    from decisionmemory.mcp_server import remember_decision, recall_memories

    await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2670.0, pnl=200.0, strategy_name="VB",
        market_context="test",
    )

    result = await recall_memories(
        symbol="XAUUSD",
        market_context="test",
    )
    assert result["affective_state"] is not None
    assert "drawdown_state" in result["affective_state"]
    assert "consecutive_losses" in result["affective_state"]


# -- recall_similar_decisions removed in 2026-04-08 audit --
# Use recall_memories instead (OWM scoring + context drift).


# -- Full integration: store 3 → recall → verify OWM scoring --


@pytest.mark.asyncio
async def test_full_owm_integration():
    """End-to-end: store 3 decisions, recall, verify OWM scoring works correctly."""
    from decisionmemory.mcp_server import remember_decision, recall_memories, _get_db

    # Store 3 decisions with different outcomes
    t1 = await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2650.0,
        exit_price=2700.0, pnl=500.0, pnl_r=3.0,
        strategy_name="VolBreakout", market_context="strong breakout above resistance",
        context_regime="trending_up", context_atr_d1=150.0,
        confidence=0.9, reflection="Perfect setup",
        decision_id="integ-win-big",
    )
    assert t1["status"] == "stored"

    t2 = await remember_decision(
        symbol="XAUUSD", direction="long", entry_price=2660.0,
        exit_price=2665.0, pnl=50.0, pnl_r=0.3,
        strategy_name="VolBreakout", market_context="weak breakout low volume",
        context_regime="ranging", context_atr_d1=80.0,
        confidence=0.4, reflection="Marginal entry",
        decision_id="integ-win-small",
    )
    assert t2["status"] == "stored"

    t3 = await remember_decision(
        symbol="XAUUSD", direction="short", entry_price=2680.0,
        exit_price=2710.0, pnl=-300.0, pnl_r=-2.0,
        strategy_name="VolBreakout", market_context="counter-trend failure",
        context_regime="trending_up", context_atr_d1=160.0,
        confidence=0.3, reflection="Should not fade trend",
        decision_id="integ-loss",
    )
    assert t3["status"] == "stored"

    # Verify DB state
    db = _get_db()

    # Episodic: 3 records
    eps = db.query_episodic(strategy="VolBreakout", limit=10)
    assert len(eps) == 3

    # Semantic: 1 record (all same strategy+symbol)
    sems = db.query_semantic(strategy="VolBreakout", symbol="XAUUSD", limit=10)
    assert len(sems) == 1
    sem = sems[0]
    assert sem["sample_size"] == 3

    # Procedural: 1 record
    procs = db.query_procedural(strategy="VolBreakout", symbol="XAUUSD", limit=10)
    assert len(procs) == 1
    assert procs[0]["sample_size"] == 3

    # Affective: should reflect 2 wins then 1 loss
    aff = db.load_affective()
    assert aff is not None
    assert aff["consecutive_wins"] == 0  # last decision was a loss
    assert aff["consecutive_losses"] == 1

    # Decision records: 3 backward-compat entries
    for tid in ["integ-win-big", "integ-win-small", "integ-loss"]:
        assert db.get_decision(tid) is not None

    # Recall with matching context
    result = await recall_memories(
        symbol="XAUUSD",
        market_context="breakout above resistance trending",
        context_regime="trending_up",
        context_atr_d1=150.0,
        memory_types=["episodic", "semantic"],
    )
    assert result["matches_found"] >= 3  # 3 episodic + 1 semantic

    # Check all memories have scores and component breakdowns
    for m in result["memories"]:
        assert m["score"] >= 0
        assert "Q" in m["components"]
        assert "Sim" in m["components"]
        assert "Rec" in m["components"]
        assert "Conf" in m["components"]
        assert "Aff" in m["components"]

    # The big winner (pnl_r=3.0) in matching regime should score highest among episodic
    episodic_results = [m for m in result["memories"] if m["memory_type"] == "episodic"]
    if len(episodic_results) >= 2:
        by_id = {m["memory_id"]: m for m in episodic_results}
        big_win = by_id.get("integ-win-big")
        small_win = by_id.get("integ-win-small")
        if big_win and small_win:
            assert big_win["components"]["Q"] > small_win["components"]["Q"]
