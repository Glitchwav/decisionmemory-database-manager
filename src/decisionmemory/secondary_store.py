"""Optional, fail-open publication of SQLite records to a secondary store."""

from __future__ import annotations

import logging
import os
from copy import deepcopy
from collections.abc import Mapping
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class SecondaryStore(Protocol):
    """Destination that receives a copy after the primary SQLite write commits."""

    def publish_decision(self, decision: Mapping[str, Any]) -> None:
        """Publish a decision and its graph relationships."""

    def publish_outcome(self, decision_id: str, outcome: Mapping[str, Any]) -> None:
        """Patch the published decision with its outcome."""

    def publish_session_state(self, state: Mapping[str, Any]) -> None:
        """Publish the latest agent session state."""


class DisabledSecondaryStore:
    """Default secondary store; intentionally performs no work."""

    def publish_decision(self, decision: Mapping[str, Any]) -> None:
        del decision

    def publish_outcome(self, decision_id: str, outcome: Mapping[str, Any]) -> None:
        del decision_id, outcome

    def publish_session_state(self, state: Mapping[str, Any]) -> None:
        del state


class SurrealGraphPublisher:
    """Publish decision nodes and reference edges to SurrealDB."""

    def __init__(self) -> None:
        try:
            from surrealdb import Surreal
        except ImportError as exc:
            raise RuntimeError(
                "DECISIONMEMORY_SECONDARY_STORE=surreal requires surrealdb>=2,<3"
            ) from exc

        host = os.environ.get("SURREAL_HOST", "http://localhost").rstrip("/")
        port = os.environ.get("SURREAL_PORT", "8000")
        username = os.environ.get("SURREAL_USER", "")
        password = os.environ.get("SURREAL_PASS", "")

        if bool(username) != bool(password):
            raise ValueError("SURREAL_USER and SURREAL_PASS must be set together")

        self._client = Surreal(f"{host}:{port}")
        if username:
            self._client.signin({"username": username, "password": password})
        self._client.use(
            os.environ.get("SURREAL_NS", "antigravity"),
            os.environ.get("SURREAL_DB", "unified"),
        )

    def publish_decision(self, decision: Mapping[str, Any]) -> None:
        decision_id = str(decision["id"])
        payload = dict(decision)
        references = payload.pop("decision_references", []) or []
        if isinstance(references, str):
            import json

            try:
                references = json.loads(references)
            except (TypeError, ValueError):
                references = [references]
        if not isinstance(references, list):
            references = [references]

        self._client.query(
            """
            UPSERT type::thing('dm_decision', $decision_id)
            CONTENT $decision;
            """,
            {"decision_id": decision_id, "decision": payload},
        )
        for reference in references:
            reference_id = str(reference)
            self._client.query(
                """
                UPSERT type::thing('dm_decision', $reference_id)
                MERGE { id: $reference_id };
                RELATE type::thing('dm_decision', $decision_id)
                    ->dm_references->type::thing('dm_decision', $reference_id)
                SET published_at = time::now();
                """,
                {
                    "decision_id": decision_id,
                    "reference_id": reference_id,
                },
            )

    def publish_outcome(self, decision_id: str, outcome: Mapping[str, Any]) -> None:
        self._client.query(
            """
            UPDATE type::thing('dm_decision', $decision_id)
            MERGE $outcome;
            """,
            {"decision_id": decision_id, "outcome": dict(outcome)},
        )

    def publish_session_state(self, state: Mapping[str, Any]) -> None:
        self._client.query(
            """
            UPSERT type::thing('dm_session', $agent_id)
            CONTENT $state;
            """,
            {"agent_id": str(state["agent_id"]), "state": dict(state)},
        )


def get_secondary_store() -> SecondaryStore:
    """Build the configured store. Empty/disabled/none values select a no-op."""

    backend = os.environ.get("DECISIONMEMORY_SECONDARY_STORE", "").strip().lower()
    if backend in {"", "disabled", "none", "off"}:
        return DisabledSecondaryStore()
    if backend == "surreal":
        return SurrealGraphPublisher()
    raise ValueError(f"Unsupported secondary store: {backend}")


def publish_after_primary_write(
    decision: Mapping[str, Any],
    store: SecondaryStore | None = None,
) -> bool:
    """Publish fail-open after SQLite succeeds.

    Callers must invoke this only after the primary transaction commits. Any
    secondary-store error is logged and suppressed, so it cannot replace the
    primary result or trigger a rollback.
    """

    try:
        (store or get_secondary_store()).publish_decision(decision)
    except Exception:
        logger.exception("Secondary-store publication failed for decision %s", decision.get("id"))
        return False
    return True


class SecondaryWritingDatabase:
    """SQLite-first decorator that mirrors selected writes after commit."""

    def __init__(self, primary: Any, store: SecondaryStore):
        self.primary = primary
        self.store = store

    def __getattr__(self, name: str) -> Any:
        return getattr(self.primary, name)

    def insert_decision(self, decision: Mapping[str, Any]) -> bool:
        primary_payload = deepcopy(dict(decision))
        secondary_payload = deepcopy(dict(decision))
        result = self.primary.insert_decision(primary_payload)
        if result:
            publish_after_primary_write(secondary_payload, self.store)
        return result

    def update_decision_outcome(
        self,
        decision_id: str,
        outcome: Mapping[str, Any],
    ) -> bool:
        primary_payload = deepcopy(dict(outcome))
        secondary_payload = deepcopy(dict(outcome))
        result = self.primary.update_decision_outcome(decision_id, primary_payload)
        if result and self.primary.get_decision(decision_id) is not None:
            try:
                self.store.publish_outcome(decision_id, secondary_payload)
            except Exception:
                logger.exception(
                    "Secondary-store outcome publication failed for decision %s",
                    decision_id,
                )
        return result

    def save_session_state(self, state: Mapping[str, Any]) -> bool:
        primary_payload = deepcopy(dict(state))
        secondary_payload = deepcopy(dict(state))
        result = self.primary.save_session_state(primary_payload)
        if result:
            try:
                self.store.publish_session_state(secondary_payload)
            except Exception:
                logger.exception(
                    "Secondary-store state publication failed for agent %s",
                    state.get("agent_id"),
                )
        return result


def wrap_database(primary: Any) -> Any:
    """Wrap SQLite only when a secondary store is explicitly enabled."""
    store = get_secondary_store()
    if isinstance(store, DisabledSecondaryStore):
        return primary
    return SecondaryWritingDatabase(primary, store)
