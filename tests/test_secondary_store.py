import sys
from types import SimpleNamespace

import pytest

from decisionmemory.secondary_store import (
    DisabledSecondaryStore,
    SecondaryWritingDatabase,
    SurrealGraphPublisher,
    get_secondary_store,
    publish_after_primary_write,
    wrap_database,
)


def test_secondary_store_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("DECISIONMEMORY_SECONDARY_STORE", raising=False)

    store = get_secondary_store()

    assert isinstance(store, DisabledSecondaryStore)
    assert publish_after_primary_write({"id": "decision-1"}, store) is True


def test_secondary_failure_is_suppressed():
    class FailingStore:
        def publish_decision(self, decision):
            raise OSError("secondary unavailable")

    primary_result = {"id": "decision-1"}

    assert publish_after_primary_write(primary_result, FailingStore()) is False
    assert primary_result == {"id": "decision-1"}


def test_unknown_secondary_store_is_rejected(monkeypatch):
    monkeypatch.setenv("DECISIONMEMORY_SECONDARY_STORE", "redis")

    with pytest.raises(ValueError, match="Unsupported secondary store"):
        get_secondary_store()


def test_surreal_publisher_uses_v2_client_and_publishes_graph(monkeypatch):
    calls = []

    class FakeSurreal:
        def __init__(self, url):
            calls.append(("init", url))

        def signin(self, credentials):
            calls.append(("signin", credentials))

        def use(self, namespace, database):
            calls.append(("use", namespace, database))

        def query(self, query, variables):
            calls.append(("query", query, variables))

    monkeypatch.setitem(sys.modules, "surrealdb", SimpleNamespace(Surreal=FakeSurreal))
    monkeypatch.setenv("DECISIONMEMORY_SECONDARY_STORE", "surreal")
    monkeypatch.setenv("SURREAL_HOST", "http://surreal.example")
    monkeypatch.setenv("SURREAL_PORT", "9000")
    monkeypatch.setenv("SURREAL_USER", "root")
    monkeypatch.setenv("SURREAL_PASS", "secret")
    monkeypatch.setenv("SURREAL_NS", "memory")
    monkeypatch.setenv("SURREAL_DB", "decisions")

    store = get_secondary_store()
    store.publish_decision(
        {
            "id": "decision-1",
            "symbol": "EURUSD",
            "decision_references": '["decision-0"]',
        }
    )

    assert isinstance(store, SurrealGraphPublisher)
    assert calls[:3] == [
        ("init", "http://surreal.example:9000"),
        ("signin", {"username": "root", "password": "secret"}),
        ("use", "memory", "decisions"),
    ]
    query_calls = [call for call in calls if call[0] == "query"]
    assert len(query_calls) == 2
    assert "UPSERT type::thing('dm_decision', $decision_id)" in query_calls[0][1]
    assert query_calls[0][2]["decision"]["symbol"] == "EURUSD"
    assert "decision_references" not in query_calls[0][2]["decision"]
    assert "RELATE type::thing('dm_decision', $decision_id)" in query_calls[1][1]
    assert query_calls[1][2]["reference_id"] == "decision-0"


def test_surreal_publisher_publishes_episodic_and_embedding(monkeypatch):
    calls = []

    class FakeSurreal:
        def __init__(self, url):
            del url

        def use(self, namespace, database):
            del namespace, database

        def query(self, query, variables):
            calls.append((query, variables))

    monkeypatch.setitem(sys.modules, "surrealdb", SimpleNamespace(Surreal=FakeSurreal))
    monkeypatch.delenv("SURREAL_USER", raising=False)
    monkeypatch.delenv("SURREAL_PASS", raising=False)

    store = SurrealGraphPublisher()
    store.publish_episodic(
        {
            "id": "episode-1",
            "strategy": "VolBreakout",
            "context_json": {"regime": "trend"},
        }
    )
    store.publish_episodic_embedding("episode-1", [0.25, 0.75])

    assert len(calls) == 2
    assert "UPSERT type::thing('tm_episodic_memory', $memory_id)" in calls[0][0]
    assert calls[0][1] == {
        "memory_id": "episode-1",
        "memory": {
            "id": "episode-1",
            "strategy": "VolBreakout",
            "context_json": {"regime": "trend"},
        },
    }
    assert "UPDATE type::thing('tm_episodic_memory', $memory_id)" in calls[1][0]
    assert calls[1][1] == {
        "memory_id": "episode-1",
        "embedding": [0.25, 0.75],
    }


def test_surreal_credentials_must_be_paired(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "surrealdb",
        SimpleNamespace(Surreal=lambda url: object()),
    )
    monkeypatch.setenv("SURREAL_USER", "root")
    monkeypatch.delenv("SURREAL_PASS", raising=False)

    with pytest.raises(ValueError, match="must be set together"):
        SurrealGraphPublisher()


def test_wrapper_writes_primary_before_secondary():
    calls = []

    class Primary:
        def insert_decision(self, decision):
            calls.append(("primary", decision["id"]))
            decision["reasoning"] = "mutated"
            return True

    class Store(DisabledSecondaryStore):
        def publish_decision(self, decision):
            calls.append(("secondary", decision["id"], decision["reasoning"]))

    original = {"id": "decision-1", "reasoning": "original"}
    wrapped = SecondaryWritingDatabase(Primary(), Store())

    assert wrapped.insert_decision(original) is True
    assert calls == [
        ("primary", "decision-1"),
        ("secondary", "decision-1", "original"),
    ]
    assert original["reasoning"] == "original"


def test_secondary_failure_does_not_change_primary_result():
    class Primary:
        def insert_decision(self, decision):
            return True

    class Store(DisabledSecondaryStore):
        def publish_decision(self, decision):
            raise OSError("offline")

    wrapped = SecondaryWritingDatabase(Primary(), Store())

    assert wrapped.insert_decision({"id": "decision-1"}) is True


def test_wrapper_publishes_episodic_after_primary_without_mutation_leak():
    calls = []

    class Primary:
        def insert_episodic(self, data):
            calls.append(("primary", data["id"]))
            data["context_json"] = '{"regime":"trend"}'
            return True

    class Store(DisabledSecondaryStore):
        def publish_episodic(self, memory):
            calls.append(("secondary", memory["id"], memory["context_json"]))

    original = {"id": "episode-1", "context_json": {"regime": "trend"}}
    wrapped = SecondaryWritingDatabase(Primary(), Store())

    assert wrapped.insert_episodic(original) is True
    assert calls == [
        ("primary", "episode-1"),
        ("secondary", "episode-1", {"regime": "trend"}),
    ]
    assert original["context_json"] == {"regime": "trend"}


def test_wrapper_publishes_embedding_after_primary():
    calls = []

    class Primary:
        def update_episodic_embedding(self, memory_id, embedding):
            calls.append(("primary", memory_id, list(embedding)))
            embedding.append(1.0)
            return True

    class Store(DisabledSecondaryStore):
        def publish_episodic_embedding(self, memory_id, embedding):
            calls.append(("secondary", memory_id, list(embedding)))

    embedding = [0.25, 0.75]
    wrapped = SecondaryWritingDatabase(Primary(), Store())

    assert wrapped.update_episodic_embedding("episode-1", embedding) is True
    assert calls == [
        ("primary", "episode-1", [0.25, 0.75]),
        ("secondary", "episode-1", [0.25, 0.75]),
    ]
    assert embedding == [0.25, 0.75]


@pytest.mark.parametrize("method", ["insert", "embedding"])
def test_episodic_secondary_failure_does_not_change_primary_result(method):
    class Primary:
        def insert_episodic(self, data):
            del data
            return True

        def update_episodic_embedding(self, memory_id, embedding):
            del memory_id, embedding
            return True

    class Store(DisabledSecondaryStore):
        def publish_episodic(self, memory):
            del memory
            raise OSError("offline")

        def publish_episodic_embedding(self, memory_id, embedding):
            del memory_id, embedding
            raise OSError("offline")

    wrapped = SecondaryWritingDatabase(Primary(), Store())

    if method == "insert":
        assert wrapped.insert_episodic({"id": "episode-1"}) is True
    else:
        assert wrapped.update_episodic_embedding("episode-1", [0.5]) is True


@pytest.mark.parametrize("method", ["insert", "embedding"])
def test_episodic_secondary_is_skipped_when_primary_returns_false(method):
    calls = []

    class Primary:
        def insert_episodic(self, data):
            del data
            return False

        def update_episodic_embedding(self, memory_id, embedding):
            del memory_id, embedding
            return False

    class Store(DisabledSecondaryStore):
        def publish_episodic(self, memory):
            calls.append(memory)

        def publish_episodic_embedding(self, memory_id, embedding):
            calls.append((memory_id, embedding))

    wrapped = SecondaryWritingDatabase(Primary(), Store())

    if method == "insert":
        assert wrapped.insert_episodic({"id": "episode-1"}) is False
    else:
        assert wrapped.update_episodic_embedding("episode-1", [0.5]) is False
    assert calls == []


def test_disabled_store_returns_plain_primary(monkeypatch):
    monkeypatch.delenv("DECISIONMEMORY_SECONDARY_STORE", raising=False)
    primary = object()

    assert wrap_database(primary) is primary
