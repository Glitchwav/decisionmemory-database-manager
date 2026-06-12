"""DecisionMaking agents for A/B simulation experiments.

BaseAgent: Mechanical execution — no learning, no calibration.
CalibratedAgent: Same strategy + DecisionMemory calibration layer (DQS + changepoint + Kelly).
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from decisionmemory.data.context_builder import MarketContext
from decisionmemory.evolution.backtester import check_entry, evaluate_condition
from decisionmemory.evolution.models import CandidatePattern

logger = logging.getLogger(__name__)


@dataclass
class DecisionSignal:
    """Entry signal from an agent."""

    direction: str  # "long" or "short"
    lot_size: float
    reason: str


@dataclass
class SimulatedDecision:
    """Completed decision with full metadata."""

    decision_id: str
    entry_bar_index: int
    exit_bar_index: int
    entry_price: float
    exit_price: float
    direction: str
    lot_size: float
    pnl: float
    pnl_r: float  # PnL in R-multiples (pnl / risk_per_decision)
    hold_bars: int
    exit_reason: str = ""
    dqs_score: Optional[float] = None
    dqs_tier: Optional[str] = None
    changepoint_prob: Optional[float] = None
    cusum_alert: Optional[bool] = None


class BaseAgent:
    """Agent A — mechanical execution, no learning, no calibration."""

    def __init__(self, strategy: CandidatePattern, fixed_lot: float = 0.01):
        self.strategy = strategy
        self.fixed_lot = fixed_lot
        self.decisions: List[SimulatedDecision] = []

    @property
    def name(self) -> str:
        return f"BaseAgent({self.strategy.name})"

    def should_decision(self, context: MarketContext) -> Optional[DecisionSignal]:
        """Evaluate entry conditions. Returns DecisionSignal or None."""
        if check_entry(self.strategy, context):
            return DecisionSignal(
                direction=self.strategy.entry_condition.direction,
                lot_size=self.fixed_lot,
                reason=f"Entry conditions met for {self.strategy.name}",
            )
        return None

    def on_decision_complete(self, decision: SimulatedDecision):
        """BaseAgent only records, no calibration."""
        self.decisions.append(decision)


class CalibratedAgent(BaseAgent):
    """Agent B — same strategy + DecisionMemory calibration layer.

    Calibration gates (applied in order):
    1. DQS check — skip tier → reject decision
    2. DQS tier multiplier — go=1.0, proceed=0.7, caution=0.3
    3. Changepoint — if cp_prob > 0.5 or CUSUM alert → lot × 0.5
    4. Kelly sizing — use procedural memory's kelly_fraction if available
    """

    def __init__(
        self,
        strategy: CandidatePattern,
        db_path: Optional[str] = None,
        fixed_lot: float = 0.01,
        hazard_lambda: float = 50.0,
    ):
        super().__init__(strategy, fixed_lot)
        from decisionmemory.db import Database
        from decisionmemory.owm.changepoint import BayesianChangepoint
        from decisionmemory.owm.dqs import DQSEngine

        if db_path is None:
            import tempfile
            db_path = os.path.join(tempfile.mkdtemp(), f"sim_{uuid.uuid4().hex[:8]}.db")
        self._db_path = db_path
        self.db = Database(db_path=db_path)
        self.changepoint = BayesianChangepoint(hazard_lambda=hazard_lambda)
        self.dqs_engine = DQSEngine(self.db)
        self._decision_count = 0
        self._last_cp_prob = 0.0
        self._last_cusum_alert = False
        self._last_dqs_score: Optional[float] = None
        self._last_dqs_tier: Optional[str] = None

        # DQS log and changepoint log for reporting
        self.dqs_log: List[Dict[str, Any]] = []
        self.changepoint_log: List[Dict[str, Any]] = []
        self.skipped_signals: int = 0

    @property
    def name(self) -> str:
        return f"CalibratedAgent({self.strategy.name})"

    def should_decision(self, context: MarketContext) -> Optional[DecisionSignal]:
        """BaseAgent entry logic + calibration gates."""
        base_signal = super().should_decision(context)
        if base_signal is None:
            return None

        # 1. Compute DQS
        try:
            dqs = self.dqs_engine.compute(
                symbol=context.symbol or "UNKNOWN",
                strategy_name=self.strategy.name,
                direction=base_signal.direction,
                proposed_lot_size=base_signal.lot_size,
                context_regime=context.regime.value if context.regime else None,
                context_atr_d1=context.atr_d1,
            )
            self._last_dqs_score = dqs.score
            self._last_dqs_tier = dqs.tier

            self.dqs_log.append({
                "decision_index": self._decision_count,
                "score": dqs.score,
                "tier": dqs.tier,
                "multiplier": dqs.position_multiplier,
                "factors": {k: v["score"] for k, v in dqs.factors.items()},
            })

            if dqs.tier == "skip":
                self.skipped_signals += 1
                return None

            # 2. Apply DQS tier multiplier
            lot = base_signal.lot_size * dqs.position_multiplier
        except Exception as e:
            logger.warning("DQS computation failed: %s — proceeding without gate", e)
            lot = base_signal.lot_size
            self._last_dqs_score = None
            self._last_dqs_tier = None

        # 3. Changepoint discount
        if self._last_cp_prob > 0.5 or self._last_cusum_alert:
            lot *= 0.5

        # 4. Kelly sizing from procedural memory
        try:
            procs = self.db.query_procedural(
                strategy=self.strategy.name,
                symbol=context.symbol or "UNKNOWN",
                limit=1,
            )
            if procs:
                kelly = procs[0].get("kelly_fraction_suggested")
                if kelly and kelly > 0:
                    lot = min(lot, kelly)
        except Exception:
            pass  # No procedural memory yet — use DQS-adjusted lot

        if lot <= 0:
            self.skipped_signals += 1
            return None

        return DecisionSignal(
            direction=base_signal.direction,
            lot_size=lot,
            reason=f"Calibrated: DQS={self._last_dqs_score}, tier={self._last_dqs_tier}",
        )

    def on_decision_complete(self, decision: SimulatedDecision):
        """Record to DecisionMemory + update changepoint."""
        super().on_decision_complete(decision)
        self._decision_count += 1

        # Attach DQS info to decision
        decision.dqs_score = self._last_dqs_score
        decision.dqs_tier = self._last_dqs_tier

        symbol = "UNKNOWN"
        # Try to get symbol from context
        if hasattr(self, '_current_symbol'):
            symbol = self._current_symbol

        # Write to episodic memory
        try:
            from datetime import datetime, timezone
            ts = datetime.now(timezone.utc).isoformat()
            self.db.insert_episodic({
                "id": decision.decision_id,
                "timestamp": ts,
                "context_json": {"symbol": symbol, "dqs_score": decision.dqs_score},
                "context_regime": None,
                "context_volatility_regime": None,
                "context_session": None,
                "context_atr_d1": None,
                "context_atr_h1": None,
                "strategy": self.strategy.name,
                "direction": decision.direction,
                "entry_price": decision.entry_price,
                "lot_size": decision.lot_size,
                "exit_price": decision.exit_price,
                "pnl": decision.pnl,
                "pnl_r": decision.pnl_r,
                "hold_duration_seconds": decision.hold_bars * 3600,  # assume 1H bars
                "max_adverse_excursion": None,
                "reflection": None,
                "confidence": 0.5,
                "tags": [],
                "retrieval_strength": 1.0,
                "retrieval_count": 0,
                "last_retrieved": None,
            })
        except Exception as e:
            logger.warning("Failed to store episodic memory: %s", e)

        # Update procedural memory
        try:
            from decisionmemory.owm_helpers import update_procedural_from_decision
            update_procedural_from_decision(
                self.db,
                symbol=symbol,
                strategy_name=self.strategy.name,
                pnl=decision.pnl,
                lot_size=decision.lot_size,
                hold_duration_seconds=decision.hold_bars * 3600,
                pnl_r=decision.pnl_r,
            )
        except Exception as e:
            logger.warning("Failed to update procedural memory: %s", e)

        # Update affective state
        try:
            from decisionmemory.owm_helpers import update_affective_from_decision
            update_affective_from_decision(
                self.db,
                pnl=decision.pnl,
                confidence=0.5,
                strategy_name=self.strategy.name,
                symbol=symbol,
            )
        except Exception as e:
            logger.warning("Failed to update affective state: %s", e)

        # Update changepoint detector
        try:
            result = self.changepoint.update({
                "won": decision.pnl > 0,
                "pnl_r": decision.pnl_r,
                "hold_seconds": decision.hold_bars * 3600,
            })
            self._last_cp_prob = result.changepoint_probability
            self._last_cusum_alert = result.cusum_alert
            decision.changepoint_prob = result.changepoint_probability
            decision.cusum_alert = result.cusum_alert

            self.changepoint_log.append({
                "decision_index": self._decision_count,
                "cp_prob": result.changepoint_probability,
                "cusum_alert": result.cusum_alert,
                "cusum_value": result.cusum_value,
                "max_run_length": result.max_run_length,
            })
        except Exception as e:
            logger.warning("Changepoint update failed: %s", e)
