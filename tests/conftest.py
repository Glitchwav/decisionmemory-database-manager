"""Shared fixtures for SurrealDB integration tests.

Provides:
- db: SurrealDatabase connected to 'decisionmemory_test' (never production)
- Test isolation: full cleanup of the test database before/after the session
- Automatic skip when SurrealDB is unavailable
"""

import os
import urllib.request

import pytest


# ── Force test database BEFORE any SurrealDatabase import ──────────────
os.environ["SURREAL_DB"] = os.environ.get("SURREAL_DB_TEST", "decisionmemory_test")
# SurrealDB v2 requires auth by default
os.environ.setdefault("SURREAL_USER", "root")
os.environ.setdefault("SURREAL_PASS", "root")


def _surreal_available() -> bool:
    """Return True if SurrealDB is reachable."""
    host = os.environ.get("SURREAL_HOST", "http://localhost")
    port = os.environ.get("SURREAL_PORT", "8000")
    try:
        urllib.request.urlopen(f"{host}:{port}/health", timeout=2)
        return True
    except Exception:
        return False


_AVAILABLE = _surreal_available()

# ── Tables used by tests ───────────────────────────────────────────────
_TEST_TABLES = [
    "tm_decision_records",
    "tm_session_state",
    "tm_episodic_memory",
    "tm_semantic_memory",
    "tm_procedural_memory",
    "tm_affective_state",
    "tm_prospective_memory",
    "tm_patterns",
    "tm_strategy_adjustments",
    "tm_audit_chain",
    "tm_audit_roots",
]


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def db():
    """Yield a SurrealDatabase connected to the test database.

    Skips the entire session if SurrealDB is not running.
    Cleans up all test tables on teardown.
    """
    if not _AVAILABLE:
        pytest.skip("SurrealDB is not running on localhost:8000")

    from decisionmemory.db_surreal import SurrealDatabase

    instance = SurrealDatabase()

    # Pre-clean: wipe test tables so prior runs don't interfere
    for table in _TEST_TABLES:
        try:
            instance._surreal.query(f"DELETE FROM {table}")
        except Exception:
            pass

    yield instance

    # Post-clean: remove everything this session created
    for table in _TEST_TABLES:
        try:
            instance._surreal.query(f"DELETE FROM {table}")
        except Exception:
            pass
