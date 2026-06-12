"""Primary SurrealDB storage interface for DecisionMemory."""

from .db_surreal import SurrealDatabase

Database = SurrealDatabase


def get_database(db_path: str | None = None) -> SurrealDatabase:
    """Return the configured SurrealDB database."""
    return SurrealDatabase()
