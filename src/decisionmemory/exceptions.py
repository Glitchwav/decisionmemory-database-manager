"""
Custom exceptions for DecisionMemory Protocol.

Hierarchy:
    DecisionMemoryError
    ├── DecisionMemoryDBError        — database operation failed
    ├── DecisionMemoryValidationError — input validation failed
    ├── DatabaseConnectionError   — legacy alias (dashboard API)
    ├── DatabaseQueryError        — legacy alias (dashboard API)
    └── StrategyNotFoundError     — strategy lookup miss
"""


class DecisionMemoryError(Exception):
    """Base exception for DecisionMemory."""


class DecisionMemoryDBError(DecisionMemoryError):
    """Database operation failed (insert, update, query)."""


class DecisionMemoryValidationError(DecisionMemoryError):
    """Input validation failed."""


# Legacy aliases — used by dashboard_api.py / services
class DatabaseConnectionError(DecisionMemoryError):
    """Raised when database connection fails."""


class DatabaseQueryError(DecisionMemoryError):
    """Raised when a database query fails."""


class StrategyNotFoundError(DecisionMemoryError):
    """Raised when a requested strategy does not exist."""
