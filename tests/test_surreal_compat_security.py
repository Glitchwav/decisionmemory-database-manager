from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from decisionmemory.db_surreal import SurrealConnection, SurrealDatabase
from decisionmemory.exceptions import DecisionMemoryDBError


class QueryRecorder:
    def __init__(self):
        self.calls = []

    def query(self, query, bindings):
        self.calls.append((query, bindings))
        return []


@pytest.mark.parametrize(
    "payload",
    [
        "'; DELETE tm_audit_chain; --",
        "\\'; UPDATE tm_decision_records SET reasoning = 'owned'",
        "x' OR true OR reasoning = 'x",
        {"nested": ["'; RETURN true; --"]},
    ],
)
def test_compat_values_are_bound_not_interpolated(payload):
    driver = QueryRecorder()
    conn = SurrealConnection(driver)

    conn.execute(
        "INSERT INTO audit_chain (record_id, content_hash) VALUES (?, ?)",
        (payload, payload),
    )

    query, bindings = driver.calls[0]
    assert query == "CREATE tm_audit_chain SET record_id = $p0, content_hash = $p1"
    assert bindings == {"p0": payload, "p1": payload}
    assert str(payload) not in query


def test_compat_select_binds_adversarial_where_value():
    driver = QueryRecorder()
    conn = SurrealConnection(driver)
    payload = "id' OR true; DELETE tm_audit_chain; --"

    conn.execute(
        "SELECT record_id FROM audit_chain WHERE record_id = ?",
        (payload,),
    )

    query, bindings = driver.calls[0]
    assert query == "SELECT * FROM tm_audit_chain WHERE record_id = $p0"
    assert bindings == {"p0": payload}
    assert payload not in query


def test_compat_rejects_unparsed_where_sql():
    conn = SurrealConnection(QueryRecorder())

    with pytest.raises(ValueError, match="Unsupported literal WHERE"):
        conn.execute("SELECT * FROM audit_chain WHERE true; DELETE audit_chain")


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM audit_chain WHERE true",
        "SELECT * FROM audit_chain ORDER BY sequence_num; DELETE audit_chain",
        "INSERT INTO audit_chain (record_id) VALUES (?) RETURN AFTER",
    ],
)
def test_compat_rejects_trailing_or_structural_sql(sql):
    conn = SurrealConnection(QueryRecorder())

    with pytest.raises(ValueError):
        conn.execute(sql, ("record-1",) if "?" in sql else ())


class FakeDecisionDatabase(SurrealDatabase):
    def __init__(self):
        self.records = {}
        self.audit = {}
        self.deleted = []

    def _q(self, query, params=None):
        record_id = params["rid"]
        if query.startswith("SELECT *"):
            record = self.records.get(record_id)
            return [dict(record)] if record else []
        if query.startswith("DELETE"):
            self.deleted.append(record_id)
            self.records.pop(record_id, None)
            return []
        raise AssertionError(query)

    def _create(self, table, record_id, data):
        self.records[record_id] = {"id": record_id, **data}
        return True

    @contextmanager
    def get_connection(self):
        yield SimpleNamespace(database=self)


class FakeChainBuilder:
    mode = "ok"

    def __init__(self, conn):
        self.database = conn.database

    def get_entry(self, record_id):
        content_hash = self.database.audit.get(record_id)
        return (
            SimpleNamespace(content_hash=content_hash)
            if content_hash is not None
            else None
        )

    def append(self, record_id, content_hash):
        if self.mode == "fail_before_commit":
            raise RuntimeError("injected append failure")
        self.database.audit[record_id] = content_hash
        if self.mode == "fail_after_commit":
            raise RuntimeError("injected response loss")
        return SimpleNamespace(content_hash=content_hash)


def decision(decision_id="decision-1", reasoning="original"):
    return {
        "id": decision_id,
        "timestamp": "2026-06-12T12:00:00+00:00",
        "symbol": "EURUSD",
        "direction": "long",
        "strategy": "test",
        "confidence": 0.8,
        "reasoning": reasoning,
        "market_context": {"price": 1.1},
        "references": [],
        "tags": [],
    }


@pytest.fixture
def fake_chain(monkeypatch):
    monkeypatch.setattr(
        "decisionmemory.audit.chain.ChainBuilder", FakeChainBuilder
    )
    FakeChainBuilder.mode = "ok"
    return FakeChainBuilder


def test_failed_audit_append_removes_new_decision_and_raises(fake_chain):
    db = FakeDecisionDatabase()
    fake_chain.mode = "fail_before_commit"

    with pytest.raises(DecisionMemoryDBError, match="rolled back"):
        db.insert_decision(decision())

    assert "decision-1" not in db.records
    assert db.deleted == ["decision-1"]


def test_append_error_after_commit_is_verified_as_success(fake_chain):
    db = FakeDecisionDatabase()
    fake_chain.mode = "fail_after_commit"

    assert db.insert_decision(decision()) is True
    assert "decision-1" in db.records
    assert "decision-1" in db.audit
    assert db.deleted == []


def test_duplicate_with_changed_immutable_content_is_rejected(fake_chain):
    db = FakeDecisionDatabase()
    assert db.insert_decision(decision()) is True

    with pytest.raises(DecisionMemoryDBError, match="different immutable content"):
        db.insert_decision(decision(reasoning="tampered"))


def test_duplicate_with_qualified_surreal_record_id_is_idempotent(fake_chain):
    db = FakeDecisionDatabase()
    assert db.insert_decision(decision()) is True
    db.records["decision-1"]["id"] = "tm_decision_records:decision-1"

    assert db.insert_decision(decision()) is True


def test_existing_decision_with_tampered_audit_hash_is_rejected(fake_chain):
    db = FakeDecisionDatabase()
    assert db.insert_decision(decision()) is True
    db.audit["decision-1"] = "0" * 64

    with pytest.raises(DecisionMemoryDBError, match="audit hash does not match"):
        db.insert_decision(decision())


def test_missing_audit_entry_is_repaired_from_stored_content(fake_chain):
    db = FakeDecisionDatabase()
    assert db.insert_decision(decision()) is True
    expected_hash = db.audit.pop("decision-1")

    assert db.insert_decision(decision()) is True
    assert db.audit["decision-1"] == expected_hash


def test_missing_audit_repair_failure_is_truthful(fake_chain):
    db = FakeDecisionDatabase()
    assert db.insert_decision(decision()) is True
    db.audit.clear()
    fake_chain.mode = "fail_before_commit"

    with pytest.raises(DecisionMemoryDBError, match="Failed to insert decision"):
        db.insert_decision(decision())
