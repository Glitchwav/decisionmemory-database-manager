"""Database factory for the SurrealDB-backed DecisionMemory runtime."""

from .db_surreal import SurrealDatabase


def get_database(db_path: str | None = None) -> SurrealDatabase:
    """Return the configured SurrealDB database."""
    return SurrealDatabase()
