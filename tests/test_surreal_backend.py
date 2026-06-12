"""
Comprehensive edge-case test suite for the SurrealDB backend.

Covers 23 scenarios that basic tests miss:
  1. Duplicate insert_decision idempotency
  2. get_decision nonexistent → None
  3. update_decision_outcome with no matching fields → False
  4. query_decisions with no matches → []
  5. save_session_state overwrite
  6. load_session_state nonexistent → None
  7. insert_episodic with tags as list
  8. insert_episodic with tags as dict
  9. insert_semantic with validity_conditions round-trip
 10. update_semantic_bayesian confirmed=False → beta update
 11. update_semantic_validity_conditions round-trip
 12. upsert_procedural overwrite
 13. init_affective idempotent
 14. save_affective with history_json as list
 15. insert_prospective all JSON fields round-trip
 16. update_prospective_status partial fields
 17. insert_pattern with dict metrics round-trip
 18. insert_adjustment + query_adjustments filter
 19. update_adjustment_status
 20. Semantic confidence formula
 21. Audit chain via get_connection()
 22. Large JSON payload (50+ keys)
 23. Special characters in strings

Run with:
  .venv/bin/python -m pytest tests/test_surreal_backend.py -v -m integration
"""

import uuid
from datetime import datetime, timezone

import pytest

# ── Markers ────────────────────────────────────────────────────────────
pytestmark = pytest.mark.integration

# ── Helpers ────────────────────────────────────────────────────────────
TEST_PREFIX = f"test_{uuid.uuid4().hex[:8]}"


def uid(suffix: str) -> str:
    """Generate a unique ID per test."""
    return f"{TEST_PREFIX}_{suffix}"


def make_decision(decision_id: str, **overrides) -> dict:
    base = {
        "id": decision_id,
        "symbol": "EURUSD",
        "direction": "long",
        "strategy": "test_strategy",
        "confidence": 0.75,
        "reasoning": "Test reasoning",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_context": {"trend": "up", "volatility": 0.5},
        "references": ["ref1"],
        "tags": ["test"],
    }
    base.update(overrides)
    return base


# ══════════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════════


def test_01_duplicate_insert_decision(db):
    """Inserting the same decision ID twice should be idempotent (return True)."""
    tid = uid("dup_decision")
    decision = make_decision(tid)
    r1 = db.insert_decision(decision)
    r2 = db.insert_decision(decision)
    assert r1 is True, f"first insert returned {r1!r}"
    assert r2 is True, f"second insert returned {r2!r}"


def test_02_get_decision_nonexistent(db):
    """get_decision with nonexistent ID should return None."""
    result = db.get_decision(uid("no_such_decision_xyz"))
    assert result is None, f"expected None, got {result!r}"


def test_03_update_decision_outcome_no_fields(db):
    """update_decision_outcome with no matching outcome fields → False."""
    tid = uid("upd_no_fields")
    db.insert_decision(make_decision(tid))
    result = db.update_decision_outcome(tid, {"unrelated_field": 42})
    assert result is False, f"expected False, got {result!r}"


def test_04_query_decisions_no_matches(db):
    """query_decisions with filters that match nothing → empty list."""
    results = db.query_decisions(strategy="nonexistent_strategy_xyz_999")
    assert isinstance(results, list), f"expected list, got {type(results)}"
    assert len(results) == 0, f"expected 0 results, got {len(results)}"


def test_05_save_session_state_overwrite(db):
    """Saving same agent_id twice should replace, not duplicate."""
    aid = uid("agent_overwrite")
    now = datetime.now(timezone.utc).isoformat()
    db.save_session_state({
        "agent_id": aid,
        "last_active": now,
        "warm_memory": {"key": "old"},
        "active_positions": [],
        "risk_constraints": {},
    })
    db.save_session_state({
        "agent_id": aid,
        "last_active": now,
        "warm_memory": {"key": "new"},
        "active_positions": [{"id": "p1"}],
        "risk_constraints": {"max_dd": 0.1},
    })
    loaded = db.load_session_state(aid)
    assert loaded is not None, "session state not loaded"
    assert loaded.get("warm_memory", {}).get("key") == "new"


def test_06_load_session_state_nonexistent(db):
    """load_session_state for nonexistent agent → None."""
    result = db.load_session_state(uid("no_such_agent"))
    assert result is None, f"expected None, got {result!r}"


def test_07_insert_episodic_tags_list(db):
    """insert_episodic with tags as list should serialize to JSON."""
    eid = uid("ep_list")
    db.insert_episodic({
        "id": eid,
        "decision_id": uid("ep_decision_1"),
        "symbol": "EURUSD",
        "direction": "long",
        "strategy": "test_strat",
        "outcome": "win",
        "pnl_r": 2.0,
        "reasoning": "test",
        "tags": ["momentum", "breakout"],
        "context_json": {"vol": 0.3},
    })
    results = db.query_episodic(strategy="test_strat")
    match = [r for r in results if r.get("id", "").endswith("ep_list")]
    assert match, "record not found in query"
    tags = match[0].get("tags")
    assert isinstance(tags, list), f"expected list, got {type(tags)}"
    assert "momentum" in tags, f"expected 'momentum' in tags, got {tags!r}"


def test_08_insert_episodic_tags_dict(db):
    """insert_episodic with tags as dict should serialize to JSON."""
    eid = uid("ep_dict")
    db.insert_episodic({
        "id": eid,
        "decision_id": uid("ep_decision_2"),
        "symbol": "GBPUSD",
        "direction": "short",
        "strategy": "test_strat_dict",
        "outcome": "loss",
        "pnl_r": -1.0,
        "reasoning": "test dict tags",
        "tags": {"type": "reversal", "confidence": "high"},
        "context_json": {"vol": 0.8},
    })
    results = db.query_episodic(strategy="test_strat_dict")
    assert results, "no results returned"
    tags = results[0].get("tags")
    assert isinstance(tags, dict), f"expected dict, got {type(tags)}"
    assert tags.get("type") == "reversal"


def test_09_insert_semantic_validity_conditions(db):
    """insert_semantic with validity_conditions should round-trip."""
    sid = uid("sem_vc")
    vc = {"regime": "trending", "min_volatility": 0.3, "max_drawdown": 0.1}
    db.insert_semantic({
        "id": sid,
        "strategy": "vc_test",
        "symbol": "USDJPY",
        "pattern_type": "entry_signal",
        "description": "test validity",
        "validity_conditions": vc,
    })
    results = db.query_semantic(strategy="vc_test")
    assert results, "no results"
    got_vc = results[0].get("validity_conditions")
    assert isinstance(got_vc, dict), f"expected dict, got {type(got_vc)}"
    assert got_vc.get("regime") == "trending"


def test_10_update_semantic_bayesian_not_confirmed(db):
    """update_semantic_bayesian with confirmed=False should update beta, not alpha."""
    sid = uid("sem_bayes")
    db.insert_semantic({
        "id": sid,
        "strategy": "bayes_test",
        "symbol": "AUDUSD",
        "pattern_type": "exit_signal",
        "description": "bayes test",
        "alpha": 2.0,
        "beta": 1.0,
    })
    db.update_semantic_bayesian(sid, confirmed=False, weight=1.5)
    results = db.query_semantic(strategy="bayes_test")
    assert results, "no results"
    r = results[0]
    # alpha should still be ~2.0, beta should be ~2.5
    assert abs(r["alpha"] - 2.0) < 0.01, f"alpha={r['alpha']}"
    assert abs(r["beta"] - 2.5) < 0.01, f"beta={r['beta']}"


def test_11_update_semantic_validity_conditions(db):
    """update_semantic_validity_conditions should round-trip."""
    sid = uid("sem_vc_upd")
    db.insert_semantic({
        "id": sid,
        "strategy": "vc_upd_test",
        "symbol": "NZDUSD",
        "pattern_type": "hold",
        "description": "vc update test",
        "validity_conditions": {"old": True},
    })
    new_vc = {"regime": "ranging", "adx_below": 25}
    db.update_semantic_validity_conditions(sid, new_vc)
    results = db.query_semantic(strategy="vc_upd_test")
    assert results, "no results"
    got = results[0].get("validity_conditions")
    assert isinstance(got, dict), f"expected dict, got {type(got)}"
    assert got.get("regime") == "ranging"


def test_12_upsert_procedural_overwrite(db):
    """Upserting procedural with same ID should replace."""
    pid = uid("proc_overwrite")
    db.upsert_procedural({
        "id": pid,
        "strategy": "proc_test",
        "symbol": "EURUSD",
        "skill_name": "entry",
        "skill_description": "old desc",
        "execution_count": 1,
    })
    db.upsert_procedural({
        "id": pid,
        "strategy": "proc_test",
        "symbol": "EURUSD",
        "skill_name": "entry",
        "skill_description": "new desc",
        "execution_count": 5,
    })
    results = db.query_procedural(strategy="proc_test")
    match = [r for r in results if r.get("id", "").endswith("proc_overwrite")]
    assert match, "record not found"
    assert match[0].get("skill_description") == "new desc"
    assert match[0].get("execution_count") == 5


def test_13_init_affective_idempotent(db):
    """Second call to init_affective should return False."""
    db.init_affective(10000.0, 10000.0)
    result = db.init_affective(10000.0, 10000.0)
    assert result is False, f"expected False, got {result!r}"


def test_14_save_affective_history_list(db):
    """save_affective with history_json as list should serialize."""
    history = [
        {"event": "win", "pnl": 50.0, "ts": "2026-01-01T00:00:00Z"},
        {"event": "loss", "pnl": -30.0, "ts": "2026-01-02T00:00:00Z"},
    ]
    db.save_affective({
        "confidence_level": 0.6,
        "risk_appetite": 0.8,
        "momentum_bias": 0.1,
        "peak_score": 10500.0,
        "current_score": 10020.0,
        "drawdown_state": 0.045,
        "max_acceptable_drawdown": 0.20,
        "consecutive_wins": 1,
        "consecutive_losses": 1,
        "history_json": history,
    })
    loaded = db.load_affective()
    assert isinstance(loaded.get("history_json"), list), "history_json not a list"
    assert len(loaded["history_json"]) == 2
    assert loaded["history_json"][0]["event"] == "win"


def test_15_insert_prospective_all_json_fields(db):
    """All JSON fields in prospective should round-trip."""
    pid = uid("prosp_all")
    data = {
        "id": pid,
        "trigger_type": "price_level",
        "trigger_condition": {"symbol": "EURUSD", "price_above": 1.1000},
        "planned_action": {"type": "close", "reason": "take_profit"},
        "source_episodic_ids": [uid("ep1"), uid("ep2")],
        "source_semantic_ids": [uid("sem1")],
        "strategy": "prosp_test",
        "priority": 0.9,
    }
    db.insert_prospective(data)
    results = db.query_prospective(trigger_type="price_level")
    match = [r for r in results if r.get("id", "").endswith("prosp_all")]
    assert match, "record not found"
    r = match[0]
    assert isinstance(r["trigger_condition"], dict)
    assert r["trigger_condition"].get("price_above") == 1.1
    assert isinstance(r["planned_action"], dict)
    assert r["planned_action"].get("type") == "close"
    assert isinstance(r["source_episodic_ids"], list)
    assert len(r["source_episodic_ids"]) == 2
    assert isinstance(r["source_semantic_ids"], list)
    assert len(r["source_semantic_ids"]) == 1


def test_16_update_prospective_status_partial(db):
    """Only provided fields should update."""
    pid = uid("prosp_partial")
    db.insert_prospective({
        "id": pid,
        "trigger_type": "time_based",
        "trigger_condition": {"after": "2026-01-01"},
        "planned_action": {"type": "review"},
        "strategy": "partial_test",
    })
    db.update_prospective_status(pid, status="triggered",
                                  triggered_at="2026-06-01T12:00:00Z")
    results = db.query_prospective(trigger_type="time_based")
    match = [r for r in results if r.get("id", "").endswith("prosp_partial")]
    assert match, "record not found"
    r = match[0]
    assert r.get("status") == "triggered"
    assert r.get("triggered_at") is not None
    assert r.get("outcome_pnl_r") is None


def test_17_insert_pattern_dict_metrics(db):
    """insert_pattern with dict metrics should round-trip."""
    pid = uid("pat_dict")
    db.insert_pattern({
        "pattern_id": pid,
        "strategy": "pattern_test",
        "symbol": "GBPJPY",
        "pattern_type": "momentum",
        "source": "test",
        "metrics": {
            "win_rate": 0.65,
            "avg_rr": 2.1,
            "sample_size": 50,
            "sub_metrics": {"sharpe": 1.5, "sortino": 2.0},
        },
        "discovered_at": datetime.now(timezone.utc).isoformat(),
    })
    results = db.query_patterns(strategy="pattern_test")
    assert results, "no results"
    m = results[0].get("metrics")
    assert isinstance(m, dict), f"expected dict, got {type(m)}"
    assert m.get("win_rate") == 0.65
    assert isinstance(m.get("sub_metrics"), dict)


def test_18_insert_and_query_adjustments(db):
    """Insert adjustments then query with status/type filters."""
    adj1 = uid("adj1")
    adj2 = uid("adj2")
    db.insert_adjustment({
        "adjustment_id": adj1,
        "strategy": "adj_test",
        "adjustment_type": "risk_limit",
        "description": "reduce size",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    db.insert_adjustment({
        "adjustment_id": adj2,
        "strategy": "adj_test",
        "adjustment_type": "entry_filter",
        "description": "add filter",
        "status": "applied",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    pending = db.query_adjustments(status="pending")
    risk_adj = db.query_adjustments(adjustment_type="risk_limit")
    pending_ids = [r.get("id", "") for r in pending]
    risk_ids = [r.get("id", "") for r in risk_adj]
    assert any(adj1 in pid for pid in pending_ids), f"adj1 not in pending: {pending_ids}"
    assert any(adj1 in rid for rid in risk_ids), f"adj1 not in risk: {risk_ids}"


def test_19_update_adjustment_status(db):
    """update_adjustment_status should return True."""
    adj_id = uid("adj_upd")
    db.insert_adjustment({
        "adjustment_id": adj_id,
        "strategy": "adj_upd_test",
        "adjustment_type": "tp_adjust",
        "description": "move tp",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    result = db.update_adjustment_status(adj_id, "applied",
                                          applied_at="2026-06-01T00:00:00Z")
    assert result is True, f"expected True, got {result!r}"


def test_20_semantic_confidence_formula(db):
    """alpha/(alpha+beta) formula should be correct."""
    sid = uid("sem_conf")
    alpha, beta = 3.0, 7.0
    db.insert_semantic({
        "id": sid,
        "strategy": "conf_test",
        "symbol": "USDCAD",
        "pattern_type": "entry",
        "description": "confidence test",
        "alpha": alpha,
        "beta": beta,
    })
    results = db.query_semantic(strategy="conf_test")
    assert results, "no results"
    r = results[0]
    expected_conf = alpha / (alpha + beta)  # 0.3
    expected_unc = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
    assert abs(r["confidence"] - expected_conf) < 0.001, (
        f"confidence={r['confidence']}, expected={expected_conf}"
    )
    assert abs(r["uncertainty"] - expected_unc) < 0.001, (
        f"uncertainty={r['uncertainty']}, expected={expected_unc}"
    )


def test_21_audit_chain(db):
    """Insert a decision then query tm_audit_chain to verify chain entry exists."""
    tid = uid("audit_decision")
    db.insert_decision(make_decision(tid))
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT record_id, sequence_num, content_hash "
            "FROM audit_chain WHERE record_id = ?",
            (tid,),
        )
        row = cursor.fetchone()
        assert row is not None, f"no audit chain entry for {tid}"


def test_22_large_json_payload(db):
    """Decision with deeply nested market_context (50+ keys) should survive round-trip."""
    tid = uid("large_json")
    # Build 60-key nested market context
    mc = {}
    for i in range(60):
        mc[f"indicator_{i}"] = {
            "value": i * 0.1,
            "signal": "buy" if i % 2 == 0 else "sell",
            "sub": {"a": i, "b": str(i) * 5},
        }
    decision = make_decision(tid, market_context=mc)
    db.insert_decision(decision)
    loaded = db.get_decision(tid)
    assert loaded is not None, "decision not found"
    got_mc = loaded.get("market_context", {})
    assert isinstance(got_mc, dict), f"expected dict, got {type(got_mc)}"
    assert len(got_mc) == 60, f"expected 60 keys, got {len(got_mc)}"
    assert got_mc["indicator_59"]["value"] == 5.9


def test_23_special_characters(db):
    """Decision reasoning with quotes, backslashes should survive round-trip."""
    tid = uid("special_chars")
    reasoning = (
        "He said 'buy now' with \"high confidence\". "
        "Path: C:\\Users\\decision_maker\\data. "
        "Signal: price > 1.1000 && RSI < 30. "
        "Note: don't forget trailing stop\\breakeven."
    )
    decision = make_decision(tid, reasoning=reasoning)
    db.insert_decision(decision)
    loaded = db.get_decision(tid)
    assert loaded is not None, "decision not found"
    got = loaded.get("reasoning", "")
    assert "He said 'buy now'" in got, f"single quotes lost: {got[:120]}"
    assert '"high confidence"' in got, f"double quotes lost: {got[:120]}"
    assert "C:\\Users" in got, f"backslashes lost: {got[:120]}"
