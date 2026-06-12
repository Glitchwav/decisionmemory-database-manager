"""End-to-end integration tests for ChainBuilder through SurrealConnection.

Tests the full chain: SurrealDatabase → SurrealConnection → ChainBuilder
against a live SurrealDB test database (ns=antigravity, db=decisionmemory_test).

Run with:
  .venv/bin/python -m pytest tests/test_surreal_chain.py -v -m integration
"""

import hashlib
import uuid
from datetime import datetime, timezone

import pytest

# ── Markers ────────────────────────────────────────────────────────────
pytestmark = pytest.mark.integration

# ── Helpers ────────────────────────────────────────────────────────────

GENESIS_HASH = "0" * 64


def _unique_id(prefix="test"):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chained_hash(prev: str, content: str) -> str:
    return hashlib.sha256((prev.lower() + content.lower()).encode("ascii")).hexdigest()


# ══════════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════════


def test_surreal_row_dict_access(db):
    """SurrealRow dict-style row['field']."""
    from decisionmemory.db_surreal import SurrealRow

    row = SurrealRow(
        {"record_id": "abc", "sequence_num": 42, "content_hash": "deadbeef"},
        ["record_id", "sequence_num", "content_hash"],
    )
    assert row["record_id"] == "abc"
    assert row["sequence_num"] == 42


def test_surreal_row_tuple_access(db):
    """SurrealRow tuple-style row[0], row[1]."""
    from decisionmemory.db_surreal import SurrealRow

    row = SurrealRow(
        {"record_id": "abc", "sequence_num": 42, "content_hash": "deadbeef"},
        ["record_id", "sequence_num", "content_hash"],
    )
    assert row[0] == "abc"
    assert row[1] == 42
    assert row[2] == "deadbeef"


def test_surreal_row_unpack(db):
    """SurrealRow unpack via *row."""
    from decisionmemory.db_surreal import SurrealRow

    row = SurrealRow(
        {"record_id": "abc", "sequence_num": 42, "content_hash": "deadbeef"},
        ["record_id", "sequence_num", "content_hash"],
    )
    assert tuple(row) == ("abc", 42, "deadbeef")


def test_surreal_row_len(db):
    """SurrealRow len()."""
    from decisionmemory.db_surreal import SurrealRow

    row = SurrealRow(
        {"record_id": "abc", "sequence_num": 42, "content_hash": "deadbeef"},
        ["record_id", "sequence_num", "content_hash"],
    )
    assert len(row) == 3


def test_append_entry(db):
    """append() returns correct AuditChainEntry."""
    from decisionmemory.audit.chain import ChainBuilder, AuditChainEntry

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        before = builder._latest_entry()
        before_seq = before.sequence_num if before else 0

        rid1 = _unique_id("decision1")
        ch1 = _sha256("content_for_decision_1")
        entry1 = builder.append(rid1, ch1)

        assert isinstance(entry1, AuditChainEntry)
        assert entry1.record_id == rid1
        assert entry1.sequence_num == before_seq + 1
        assert entry1.content_hash == ch1
        assert len(entry1.prev_hash) == 64
        assert len(entry1.data_hash) == 64
        assert entry1.data_hash == chained_hash(entry1.prev_hash, ch1)
        assert "+00:00" in entry1.chained_at or "Z" in entry1.chained_at


def test_latest_entry(db):
    """_latest_entry() returns the just-appended entry."""
    from decisionmemory.audit.chain import ChainBuilder, AuditChainEntry

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        rid = _unique_id("latest_test")
        ch = _sha256("latest_content")
        builder.append(rid, ch)

        latest = builder._latest_entry()
        assert latest is not None
        assert isinstance(latest, AuditChainEntry)
        assert latest.record_id == rid


def test_idempotent_append(db):
    """Idempotent append with same record_id + content_hash returns same entry."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        rid = _unique_id("idem_decision")
        ch = _sha256("idem_content")
        entry1 = builder.append(rid, ch)
        entry1b = builder.append(rid, ch)

        assert entry1b.record_id == entry1.record_id
        assert entry1b.sequence_num == entry1.sequence_num
        assert entry1b.data_hash == entry1.data_hash


def test_tamper_detection(db):
    """Same record_id + different content_hash raises ValueError."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        rid = _unique_id("tamper_decision")
        ch = _sha256("original_content")
        builder.append(rid, ch)

        ch_tampered = _sha256("TAMPERED_CONTENT")
        with pytest.raises(ValueError, match="different content_hash"):
            builder.append(rid, ch_tampered)


def test_get_entry_existing(db):
    """get_entry finds an existing entry."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        rid = _unique_id("get_entry_decision")
        ch = _sha256("get_entry_content")
        builder.append(rid, ch)

        found = builder.get_entry(rid)
        assert found is not None
        assert found.record_id == rid


def test_get_entry_missing(db):
    """get_entry returns None for a missing record."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        assert builder.get_entry("nonexistent_record_xyz") is None


def test_chain_three_entries(db):
    """Build a chain of 3 entries and verify sequence numbers and linking."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        before = builder._latest_entry()
        base_seq = before.sequence_num if before else 0

        rid1 = _unique_id("c3_decision1")
        ch1 = _sha256("c3_content_1")
        entry1 = builder.append(rid1, ch1)

        rid2 = _unique_id("c3_decision2")
        ch2 = _sha256("c3_content_2")
        entry2 = builder.append(rid2, ch2)

        assert entry2.sequence_num == base_seq + 2
        assert entry2.prev_hash == entry1.data_hash
        expected_dh2 = chained_hash(entry1.data_hash, ch2)
        assert entry2.data_hash == expected_dh2

        rid3 = _unique_id("c3_decision3")
        ch3 = _sha256("c3_content_3")
        entry3 = builder.append(rid3, ch3)

        assert entry3.sequence_num == base_seq + 3


def test_verify_chain_full(db):
    """verify_chain() on a valid chain returns verified=True."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        before_count = builder.verify_chain().get("checked_count", 0)

        for i in range(3):
            rid = _unique_id(f"vf_decision{i}")
            ch = _sha256(f"vf_content_{i}")
            builder.append(rid, ch)

        result = builder.verify_chain()
        assert result["verified"] is True, f"result={result}"
        assert result["checked_count"] == before_count + 3
        assert result["first_break_at"] is None


def test_verify_chain_range_single(db):
    """verify_chain(from_seq=2, to_seq=2) verifies just one entry."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)

        for i in range(3):
            rid = _unique_id(f"vr1_decision{i}")
            ch = _sha256(f"vr1_content_{i}")
            builder.append(rid, ch)

        result = builder.verify_chain(from_seq=2, to_seq=2)
        assert result["verified"] is True, f"result={result}"
        assert result["checked_count"] == 1


def test_verify_chain_range_pair(db):
    """verify_chain(from_seq=2, to_seq=3) verifies two entries."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)

        for i in range(3):
            rid = _unique_id(f"vr2_decision{i}")
            ch = _sha256(f"vr2_content_{i}")
            builder.append(rid, ch)

        result = builder.verify_chain(from_seq=2, to_seq=3)
        assert result["verified"] is True
        assert result["checked_count"] == 2


def test_build_daily_root(db):
    """build_daily_root returns correct DailyRoot."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        before_count = builder.verify_chain().get("checked_count", 0)

        for i in range(3):
            rid = _unique_id(f"dr_decision{i}")
            ch = _sha256(f"dr_content_{i}")
            builder.append(rid, ch)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        root = builder.build_daily_root(today)

        assert root is not None
        assert root.record_count == before_count + 3
        assert len(root.root_hash) == 64
        assert all(c in "0123456789abcdef" for c in root.root_hash)
        assert root.first_sequence == 1
        assert root.last_sequence == before_count + 3


def test_verify_daily_root_valid(db):
    """verify_daily_root returns verified=True when root matches."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)

        # Build a fresh root for today (includes all entries so far today)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        root = builder.build_daily_root(today)

        vr = builder.verify_daily_root(today)
        assert vr["verified"] is True, f"result={vr}"
        assert vr["stored_root"] == vr["recomputed_root"]
        assert vr["record_count"] == root.record_count


def test_verify_daily_root_missing_date(db):
    """verify_daily_root for a date with no root returns not verified."""
    from decisionmemory.audit.chain import ChainBuilder

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)

        vr = builder.verify_daily_root("2000-01-01")
        assert vr["verified"] is False
        assert "no root" in vr.get("reason", "").lower()


def test_insert_decision_with_audit(db):
    """insert_decision creates both the decision record and audit chain entry."""
    from decisionmemory.audit.chain import ChainBuilder
    from decisionmemory.domain.tdr import DecisionMakingDecisionRecord

    decision_id = _unique_id("full_decision")
    decision_data = {
        "id": decision_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": "EURUSD",
        "direction": "long",
        "strategy": "test_strategy",
        "confidence": 0.85,
        "reasoning": "test entry for integration test",
        "market_context": {"price": 1.0850, "session": "london"},
        "references": [],
        "tags": ["test"],
    }

    expected_ch = DecisionMakingDecisionRecord.compute_hash(
        decision_id=decision_id,
        timestamp=decision_data["timestamp"],
        symbol=decision_data["symbol"],
        direction=decision_data["direction"],
        strategy=decision_data["strategy"],
        confidence=decision_data["confidence"],
        reasoning=decision_data["reasoning"],
        market_context=decision_data["market_context"],
    )

    result = db.insert_decision(decision_data)
    assert result is True

    stored_decision = db.get_decision(decision_id)
    assert stored_decision is not None
    assert stored_decision.get("symbol") == "EURUSD"

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        decision_entry = builder.get_entry(decision_id)
        assert decision_entry is not None
        assert decision_entry.record_id == decision_id
        assert decision_entry.content_hash == expected_ch


def test_audit_chain_entry_fields(db):
    """Audit chain entry has correct types and hash chaining."""
    from decisionmemory.audit.chain import ChainBuilder
    from decisionmemory.domain.tdr import DecisionMakingDecisionRecord

    decision_id = _unique_id("fields_decision")
    decision_data = {
        "id": decision_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": "GBPUSD",
        "direction": "short",
        "strategy": "fields_strategy",
        "confidence": 0.7,
        "reasoning": "fields test",
        "market_context": {"session": "ny"},
        "references": [],
        "tags": [],
    }
    db.insert_decision(decision_data)

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        e = builder.get_entry(decision_id)
        assert e is not None, "audit chain entry is None"

        assert isinstance(e.record_id, str)
        assert isinstance(e.sequence_num, int)
        assert len(e.content_hash) == 64
        assert len(e.prev_hash) == 64
        assert len(e.data_hash) == 64
        assert "T" in e.chained_at
        assert "+00:00" in e.chained_at or "Z" in e.chained_at

        expected = chained_hash(e.prev_hash, e.content_hash)
        assert e.data_hash == expected


def test_final_chain_valid_after_insert_decision(db):
    """Chain remains valid after insert_decision."""
    from decisionmemory.audit.chain import ChainBuilder

    decision_id = _unique_id("final_decision")
    decision_data = {
        "id": decision_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": "USDJPY",
        "direction": "long",
        "strategy": "final_strategy",
        "confidence": 0.9,
        "reasoning": "final verification",
        "market_context": {},
        "references": [],
        "tags": [],
    }
    db.insert_decision(decision_data)

    with db.get_connection() as conn:
        builder = ChainBuilder(conn)
        final_verify = builder.verify_chain()
        assert final_verify["verified"] is True, f"result={final_verify}"
