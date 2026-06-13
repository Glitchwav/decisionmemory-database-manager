"""Canonical DecisionMemory database factory."""


def get_database(db_path: str | None = None):
    """Delegate to the SQLite-first factory."""
    from .db import get_database as _get_database

    return _get_database(db_path)
