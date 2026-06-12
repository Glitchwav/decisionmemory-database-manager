"""Kelly criterion position sizing from OWM scored memories.

Reference: Generalized Kelly f* = p/a - q/b
  p = weighted win probability
  q = 1 - p (weighted loss probability)
  a = weighted average loss magnitude
  b = weighted average win magnitude
"""

from __future__ import annotations

from typing import List

from .recall import ScoredMemory


def kelly_from_memory(
    memories: List[ScoredMemory],
    fractional: float = 0.25,
    risk_appetite: float = 1.0,
) -> float:
    """Compute fractional Kelly fraction from OWM scored memories.

    Uses each memory's OWM score as weight and pnl_r (R-multiple) from
    data dict to classify wins/losses and compute weighted statistics.

    Args:
        memories: Scored memories with data["pnl_r"] values.
        fractional: Kelly fraction multiplier (default 0.25 = quarter-Kelly).
        risk_appetite: Additional scaling factor in [0, inf).

    Returns:
        Recommended position size fraction, clamped to [0, 0.5].
        Returns 0.0 if fewer than 10 memories have pnl_r data.
    """
    # Filter to memories that have pnl_r
    valid = [m for m in memories if m.data.get("pnl_r") is not None]

    if len(valid) < 10:
        return 0.0

    # Split into wins and losses, weighted by OWM score
    win_weights: float = 0.0
    loss_weights: float = 0.0
    win_pnl_weighted: float = 0.0
    loss_pnl_weighted: float = 0.0

    for m in valid:
        pnl_r = m.data["pnl_r"]
        w = max(m.score, 0.0)  # ensure non-negative weight

        if pnl_r > 0:
            win_weights += w
            win_pnl_weighted += w * pnl_r
        else:
            loss_weights += w
            loss_pnl_weighted += w * abs(pnl_r)

    total_weight = win_weights + loss_weights
    if total_weight <= 0:
        return 0.0

    p = win_weights / total_weight  # weighted win probability
    q = 1.0 - p                    # weighted loss probability

    # Weighted average magnitudes
    b = (win_pnl_weighted / win_weights) if win_weights > 0 else 0.0   # avg win
    a = (loss_pnl_weighted / loss_weights) if loss_weights > 0 else 0.0  # avg loss

    # f* = p/a - q/b
    # When a=0 (no losses), f* → +inf (bet max). When b=0 (no wins), f* → -inf (don't bet).
    if b <= 0:
        return 0.0

    if a <= 0:
        # No losses observed — Kelly says bet max, clamp will handle
        f_star = float("inf")
    else:
        f_star = p / a - q / b

    # Apply fractional Kelly and risk appetite, clamp to [0, 0.5]
    result = f_star * fractional * risk_appetite
    return max(0.0, min(0.5, result))
