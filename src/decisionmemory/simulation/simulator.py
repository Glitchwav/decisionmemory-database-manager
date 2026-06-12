"""Bar-by-bar simulator that runs an agent through OHLCV data.

Reuses position management logic from evolution/backtester.py:
- ATR-based SL/TP
- Trailing stops
- Time-based exits
- Single position (no pyramiding)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from decisionmemory.data.context_builder import ContextConfig, build_context, compute_atr
from decisionmemory.data.models import OHLCVSeries
from decisionmemory.evolution.backtester import (
    Position,
    Decision,
    _compute_fitness,
    check_exit_position,
    force_close_position,
    open_position,
)
from decisionmemory.evolution.models import FitnessMetrics
from decisionmemory.simulation.agent import BaseAgent, SimulatedDecision, DecisionSignal


@dataclass
class SimulationResult:
    """Full results from running one agent on one data series."""

    agent_name: str
    strategy_name: str
    symbol: str
    timeframe: str
    fitness: FitnessMetrics
    decisions: List[SimulatedDecision] = field(default_factory=list)
    dqs_log: List[dict] = field(default_factory=list)
    changepoint_log: List[dict] = field(default_factory=list)
    skipped_signals: int = 0
    total_signals: int = 0
    # Score-based metrics (lot-adjusted)
    score_total_pnl: float = 0.0  # sum(pnl * lot_size)
    score_max_dd: float = 0.0  # max drawdown in $ (lot-adjusted)
    score_calmar: float = 0.0  # annual return / max DD


class Simulator:
    """Bar-by-bar simulation engine.

    Walks through each bar, asks the agent for decision signals,
    manages open positions using backtester's SL/TP/trailing logic,
    and feeds completed decisions back to the agent.
    """

    def __init__(
        self,
        agent: BaseAgent,
        series: OHLCVSeries,
        timeframe_str: str = "1h",
        context_config: Optional[ContextConfig] = None,
    ):
        self.agent = agent
        self.series = series
        self.timeframe_str = timeframe_str
        self.config = context_config or ContextConfig()

    def run(self) -> SimulationResult:
        """Run the full simulation bar-by-bar.

        Returns SimulationResult with fitness metrics and decision log.
        """
        bars = self.series.bars
        if not bars or len(bars) < 30:
            return SimulationResult(
                agent_name=self.agent.name,
                strategy_name=self.agent.strategy.name,
                symbol=self.series.symbol,
                timeframe=self.timeframe_str,
                fitness=FitnessMetrics(),
            )

        # Set current symbol on agent for memory storage
        if hasattr(self.agent, '_current_symbol'):
            self.agent._current_symbol = self.series.symbol
        else:
            self.agent._current_symbol = self.series.symbol

        position: Optional[Position] = None
        pending_signal: Optional[DecisionSignal] = None
        backtester_decisions: List[Decision] = []
        sim_decisions: List[SimulatedDecision] = []
        total_signals = 0

        min_bar = self.config.atr_period + 1

        for i in range(min_bar, len(bars)):
            current_bar = bars[i]

            # Check exits on open position
            if position is not None:
                bt_decision = check_exit_position(position, current_bar, i)
                if bt_decision is not None:
                    backtester_decisions.append(bt_decision)
                    sim_decision = self._bt_decision_to_sim(bt_decision, pending_signal)
                    sim_decisions.append(sim_decision)
                    self.agent.on_decision_complete(sim_decision)
                    position = None
                    pending_signal = None

            # Check entry when flat
            if position is None:
                ctx = build_context(self.series, bar_index=i, config=self.config)
                signal = self.agent.should_decision(ctx)

                if signal is not None:
                    total_signals += 1
                    # Compute ATR for position sizing
                    atr = compute_atr(
                        bars[max(0, i - self.config.atr_period - 1): i + 1],
                        self.config.atr_period,
                    )
                    if atr is not None and atr > 0:
                        position = open_position(
                            self.agent.strategy, current_bar, i, atr
                        )
                        pending_signal = signal
                elif check_entry_would_trigger(self.agent, ctx):
                    # Agent's base conditions met but calibration rejected it
                    total_signals += 1

        # Close any remaining position at last bar
        if position is not None:
            bt_decision = force_close_position(position, bars[-1], len(bars) - 1, "end")
            backtester_decisions.append(bt_decision)
            sim_decision = self._bt_decision_to_sim(bt_decision, pending_signal)
            sim_decisions.append(sim_decision)
            self.agent.on_decision_complete(sim_decision)

        # Compute fitness from backtester decisions
        fitness = _compute_fitness(backtester_decisions, timeframe=self.timeframe_str)

        # Collect agent-specific logs
        dqs_log = getattr(self.agent, 'dqs_log', [])
        cp_log = getattr(self.agent, 'changepoint_log', [])
        skipped = getattr(self.agent, 'skipped_signals', 0)

        # Compute score-based metrics (lot_size-adjusted)
        score_pnl, score_dd, score_calmar = _compute_score_metrics(
            sim_decisions, self.timeframe_str
        )

        return SimulationResult(
            agent_name=self.agent.name,
            strategy_name=self.agent.strategy.name,
            symbol=self.series.symbol,
            timeframe=self.timeframe_str,
            fitness=fitness,
            decisions=sim_decisions,
            dqs_log=dqs_log,
            changepoint_log=cp_log,
            skipped_signals=skipped,
            total_signals=total_signals + skipped,
            score_total_pnl=score_pnl,
            score_max_dd=score_dd,
            score_calmar=score_calmar,
        )

    def _bt_decision_to_sim(
        self, bt_decision: Decision, signal: Optional[DecisionSignal]
    ) -> SimulatedDecision:
        """Convert backtester Decision to SimulatedDecision."""
        lot = signal.lot_size if signal else self.agent.fixed_lot

        # Compute pnl_r: pnl / (entry_price * SL_distance) as R-multiple
        # Approximate: use SL ATR distance from strategy
        sl_atr = self.agent.strategy.exit_condition.stop_loss_atr
        if sl_atr and sl_atr > 0 and bt_decision.entry_price > 0:
            # Risk per unit ≈ entry_price * some fraction
            # Use absolute PnL / approximate risk
            pnl_r = bt_decision.pnl / (bt_decision.entry_price * sl_atr * 0.01) if bt_decision.entry_price > 0 else 0.0
        else:
            pnl_r = bt_decision.pnl / max(bt_decision.entry_price * 0.01, 0.001)

        return SimulatedDecision(
            decision_id=f"sim-{uuid.uuid4().hex[:8]}",
            entry_bar_index=bt_decision.entry_bar,
            exit_bar_index=bt_decision.exit_bar,
            entry_price=bt_decision.entry_price,
            exit_price=bt_decision.exit_price,
            direction=bt_decision.direction,
            lot_size=lot,
            pnl=bt_decision.pnl,
            pnl_r=round(pnl_r, 4),
            hold_bars=bt_decision.holding_bars,
            exit_reason=bt_decision.exit_reason,
        )


def _compute_score_metrics(
    decisions: List[SimulatedDecision], timeframe: str
) -> tuple:
    """Compute lot-adjusted score metrics.

    Unlike Sharpe (a ratio), these metrics capture position sizing differences:
    - Total PnL: sum(pnl * lot_size / base_lot) — normalized to base_lot=0.01
    - Max DD: maximum peak-to-trough in dollar score
    - Calmar: annualized return / max DD
    """
    if not decisions:
        return 0.0, 0.0, 0.0

    base_lot = 0.01  # normalize relative to BaseAgent's fixed lot
    score = 0.0
    peak = 0.0
    max_dd = 0.0

    for t in decisions:
        lot_multiplier = t.lot_size / base_lot if base_lot > 0 else 1.0
        score += t.pnl * lot_multiplier
        if score > peak:
            peak = score
        dd = peak - score
        if dd > max_dd:
            max_dd = dd

    # Annualization factor
    _ann = {"1m": 525960, "5m": 105192, "15m": 35064, "30m": 17532,
            "1h": 8766, "4h": 2191, "1d": 365, "1w": 52}
    bars_per_year = _ann.get(timeframe, 8766)
    total_bars = sum(t.hold_bars for t in decisions) if decisions else 1
    years = max(total_bars / bars_per_year, 0.01)

    annual_return = score / years if years > 0 else 0.0
    calmar = annual_return / max_dd if max_dd > 0 else 0.0

    return round(score, 2), round(max_dd, 2), round(calmar, 4)


def check_entry_would_trigger(agent: BaseAgent, ctx) -> bool:
    """Check if base entry conditions are met (ignoring calibration).

    Used to count signals that the CalibratedAgent would have skipped.
    """
    from decisionmemory.evolution.backtester import check_entry
    from decisionmemory.simulation.agent import CalibratedAgent

    if isinstance(agent, CalibratedAgent):
        # For CalibratedAgent, check raw strategy conditions
        return check_entry(agent.strategy, ctx)
    return False
