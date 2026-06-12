"""
Database factory for DecisionMemory Protocol.
Returns SurrealDB or SQLite backend based on DECISIONMEMORY_BACKEND env var.

Usage:
    from .db_factory import get_database
    db = get_database()  # Returns SurrealDatabase if DECISIONMEMORY_BACKEND=surreal, else Database
"""

import os


def get_database(db_path: str | None = None):
    """Factory: returns SurrealDB backend if DECISIONMEMORY_BACKEND=surreal, else SQLite.

    Args:
        db_path: Only used for SQLite backend. Ignored for SurrealDB.

    Returns:
        Database or SurrealDatabase instance
    """
    backend = os.environ.get("DECISIONMEMORY_BACKEND", "").lower()
    if backend == "surreal":
        from .db_surreal import SurrealDatabase
        return SurrealDatabase()
    from .db import Database
    return Database(db_path)
