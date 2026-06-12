"""MaxDDStop baseline: reduce lot when score drawdown exceeds threshold.

This is the standard risk management approach that the paper should compare against.
When score DD exceeds X% of peak, reduce lot by 50%. Restore when DD recovers.

Usage: imported by compare_maxdd.py
"""
from __future__ import annotations

import sys
import os
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from decisionmemory.simulation.agent import BaseAgent, SimulatedDecision, DecisionSignal
from decisionmemory.data.context_builder import MarketContext
from decisionmemory.evolution.models import CandidatePattern

from typing import Optional


class MaxDDStopAgent(BaseAgent):
    """Reduce lot when score drawdown exceeds threshold.

    Standard risk management approach: track score curve,
    when DD from peak > dd_threshold, reduce lot by reduce_pct.
    """

    def __init__(
        self,
        strategy: CandidatePattern,
        fixed_lot: float = 0.01,
        dd_threshold: float = 0.15,  # 15% DD triggers reduction
        reduce_pct: float = 0.5,
    ):
        super().__init__(strategy, fixed_lot=fixed_lot)
        self._dd_threshold = dd_threshold
        self._reduce_pct = reduce_pct
        self._score = 0.0
        self._peak_score = 0.0
        self._reduced_count = 0
        self._decision_index = 0

    def warm_start(self, is_decisions: List[SimulatedDecision]):
        """Compute IS score to set initial peak."""
        for t in is_decisions:
            self._score += t.pnl
            self._peak_score = max(self._peak_score, self._score)

    def _get_dd_adjusted_lot(self) -> float:
        """Compute lot size based on current score drawdown."""
        if self._peak_score > 0:
            dd_pct = (self._peak_score - self._score) / self._peak_score
        else:
            dd_pct = 0.0

        if dd_pct > self._dd_threshold:
            self._reduced_count += 1
            return self.fixed_lot * self._reduce_pct
        return self.fixed_lot

    def should_decision(self, context: MarketContext) -> Optional[DecisionSignal]:
        """Override to apply DD-adjusted lot sizing."""
        base_signal = super().should_decision(context)
        if base_signal is None:
            return None

        lot = self._get_dd_adjusted_lot()
        self._decision_index += 1

        return DecisionSignal(
            direction=base_signal.direction,
            lot_size=lot,
            reason=f"MaxDDStop: lot={lot:.4f}",
        )

    def on_decision_complete(self, decision: SimulatedDecision):
        """Update score tracking after decision completes."""
        self.decisions.append(decision)
        self._score += decision.pnl * (decision.lot_size / self.fixed_lot)
        self._peak_score = max(self._peak_score, self._score)
