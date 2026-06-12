"""Memory recall for historical runs."""

from typing import Optional

from decisionmemory.db import get_database


def build_memory_context(
    db_path: str | None = None,
    strategy: Optional[str] = None,
    regime: Optional[str] = None,
    session: Optional[str] = None,
    atr_d1: float = 0.0,
    limit: int = 5,
) -> str:
    """Query episodic memory and format matching decisions as prompt context."""
    db = get_database(db_path)
    rows = db.query_episodic(
        strategy=strategy,
        context_regime=regime,
        context_session=session,
        limit=limit,
    )
    if not rows:
        return ""

    lines = ["## Similar Past Decisions"]
    for index, row in enumerate(rows, 1):
        reflection = (row.get("reflection") or "")[:150]
        lines.append(
            f"{index}. [{row.get('strategy', '')}] "
            f"entry={float(row.get('entry_price') or 0):.2f} "
            f"exit={float(row.get('exit_price') or 0):.2f} "
            f"pnl=${float(row.get('pnl') or 0):.2f} "
            f"pnl_r={float(row.get('pnl_r') or 0):.2f}"
        )
        if reflection:
            lines.append(f"   Reflection: {reflection}")
    return "\n".join(lines)
