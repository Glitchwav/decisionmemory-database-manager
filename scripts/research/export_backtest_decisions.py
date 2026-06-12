#!/usr/bin/env python3
"""Export strategy backtest decisions to JSON.

Fetches BTCUSDT 1H data from Binance (2024-06-01 to now),
runs backtest, and exports each decision with full metadata.

Usage:
    cd C:/Users/johns/projects/decisionmemory-protocol
    python scripts/research/export_backtest_decisions.py              # default: Strategy E
    python scripts/research/export_backtest_decisions.py --strategy c  # Strategy C
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/ for strategy_definitions

from decisionmemory.data.binance import BinanceDataSource
from decisionmemory.data.context_builder import ContextConfig, build_context, compute_atr
from decisionmemory.data.models import OHLCV, OHLCVSeries, Timeframe
from decisionmemory.evolution.backtester import (
    Position,
    Decision,
    _compute_fitness,
    check_entry,
    check_exit_position,
    force_close_position,
    open_position,
)
from decisionmemory.evolution.models import (
    CandidatePattern,
    FitnessMetrics,
)


def precompute_contexts(series: OHLCVSeries, config: Optional[ContextConfig] = None):
    """Precompute MarketContext for every bar in the series."""
    cfg = config or ContextConfig()
    n = len(series.bars)
    min_bar = cfg.atr_period + 1
    contexts = [None] * n
    for i in range(min_bar, n):
        if i % 500 == 0:
            print(f"    context {i}/{n}...", flush=True)
        contexts[i] = build_context(series, bar_index=i, config=cfg)
    return contexts


def precompute_atrs(bars: List[OHLCV], atr_period: int = 14):
    """Precompute ATR for every bar in the series."""
    n = len(bars)
    atrs = [None] * n
    for i in range(atr_period + 1, n):
        atrs[i] = compute_atr(bars[max(0, i - atr_period - 1) : i + 1], atr_period)
    return atrs


def fast_backtest_with_decisions(
    bars: List[OHLCV],
    contexts: list,
    atrs: list,
    pattern: CandidatePattern,
    config: Optional[ContextConfig] = None,
    timeframe: str = "1h",
) -> Tuple[FitnessMetrics, List[Decision]]:
    """Backtest returning both FitnessMetrics and the list of Decision objects."""
    if not bars or len(bars) < 30:
        return FitnessMetrics(), []
    cfg = config or ContextConfig()
    min_bar = cfg.atr_period + 1
    decisions: List[Decision] = []
    position: Optional[Position] = None

    for i in range(min_bar, len(bars)):
        current_bar = bars[i]
        ctx = contexts[i]

        if position is not None:
            decision = check_exit_position(position, current_bar, i)
            if decision is not None:
                decisions.append(decision)
                position = None

        if position is None and ctx is not None:
            if check_entry(pattern, ctx):
                atr = atrs[i]
                if atr is None or atr <= 0:
                    continue
                position = open_position(pattern, current_bar, i, atr)

    if position is not None:
        last_bar = bars[-1]
        decision = force_close_position(position, last_bar, len(bars) - 1, "end")
        decisions.append(decision)

    fitness = _compute_fitness(decisions, timeframe=timeframe)
    return fitness, decisions


from strategy_definitions import build_strategy_c, build_strategy_e  # noqa: E402

STRATEGY_BUILDERS = {
    "c": (build_strategy_c, "STRAT-C", "strategy_c_backtest.json"),
    "e": (build_strategy_e, "STRAT-E", "strategy_e_backtest.json"),
}


def decision_to_dict(
    decision: Decision,
    bars: List[OHLCV],
    contexts: list,
    atrs: list,
    strategy_id: str = "STRAT-E",
    symbol: str = "BTCUSDT",
) -> dict:
    """Convert a Decision dataclass to a rich dict with metadata."""
    entry_bar = bars[decision.entry_bar]
    exit_bar = bars[decision.exit_bar]

    # ATR at entry
    atr_at_entry = atrs[decision.entry_bar]

    # trend_12h_pct at entry
    ctx = contexts[decision.entry_bar]
    trend_12h_pct = ctx.trend_12h_pct if ctx and ctx.trend_12h_pct is not None else None

    # pnl_r = pnl / risk (risk = 1 ATR for SL)
    pnl_r = None
    if atr_at_entry and atr_at_entry > 0:
        pnl_r = round(decision.pnl / atr_at_entry, 4)

    # pnl_pct = pnl / entry_price * 100
    pnl_pct = round(decision.pnl / decision.entry_price * 100, 4) if decision.entry_price else 0.0

    return {
        "strategy_id": strategy_id,
        "symbol": symbol,
        "direction": decision.direction,
        "entry_price": round(decision.entry_price, 2),
        "exit_price": round(decision.exit_price, 2),
        "entry_time": entry_bar.timestamp.isoformat(),
        "exit_time": exit_bar.timestamp.isoformat(),
        "pnl_pct": pnl_pct,
        "pnl_r": pnl_r,
        "exit_reason": decision.exit_reason,
        "holding_bars": decision.holding_bars,
        "atr_at_entry": round(atr_at_entry, 2) if atr_at_entry else None,
        "trend_12h_pct": round(trend_12h_pct, 4) if trend_12h_pct is not None else None,
        "decision_type": "backtest",
    }


async def main():
    parser = argparse.ArgumentParser(description="Export strategy backtest decisions to JSON")
    parser.add_argument("--strategy", choices=["c", "e"], default="e", help="Strategy to backtest (default: e)")
    args = parser.parse_args()

    builder, strategy_id, json_filename = STRATEGY_BUILDERS[args.strategy]

    print(f"=== Export Strategy {args.strategy.upper()} Backtest Decisions ===\n")

    # 1. Fetch data
    start = datetime(2024, 6, 1, tzinfo=timezone.utc)
    end = datetime.now(timezone.utc)
    symbol = "BTCUSDT"
    timeframe = Timeframe.H1

    print(f"Fetching {symbol} {timeframe.value} from {start.date()} to {end.date()}...")
    ds = BinanceDataSource()
    try:
        series = await ds.fetch_ohlcv(symbol, timeframe, start, end)
    finally:
        await ds.close()
    print(f"  Got {len(series.bars)} bars\n")

    # 2. Precompute
    print("Precomputing contexts...")
    contexts = precompute_contexts(series)
    print("Precomputing ATRs...")
    atrs = precompute_atrs(series.bars)

    # 3. Run backtest
    strategy = builder()
    print(f"\nRunning backtest: {strategy.name}...")
    fitness, decisions = fast_backtest_with_decisions(
        series.bars, contexts, atrs, strategy, timeframe="1h"
    )

    # 4. Convert decisions to dicts
    decision_dicts = [
        decision_to_dict(t, series.bars, contexts, atrs, strategy_id=strategy_id, symbol=symbol)
        for t in decisions
    ]

    # 5. Write JSON
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / json_filename
    output_path.write_text(json.dumps(decision_dicts, indent=2), encoding="utf-8")
    print(f"\nWrote {len(decision_dicts)} decisions to {output_path}")

    # 6. Summary
    print(f"\n--- Summary ---")
    print(f"  Decisions:        {fitness.decision_count}")
    print(f"  Win Rate:      {fitness.win_rate:.1%}")
    print(f"  Sharpe:        {fitness.sharpe_ratio:.2f}")
    print(f"  Profit Factor: {fitness.profit_factor:.2f}")
    print(f"  Total PnL:     {fitness.total_pnl:.2f}")
    print(f"  Max Drawdown:  {fitness.max_drawdown_pct:.1f}%")
    print(f"  Avg Holding:   {fitness.avg_holding_bars:.1f} bars")

    if decision_dicts:
        wins = [t for t in decision_dicts if t["pnl_pct"] > 0]
        losses = [t for t in decision_dicts if t["pnl_pct"] <= 0]
        print(f"  Wins:          {len(wins)}")
        print(f"  Losses:        {len(losses)}")
        first = decision_dicts[0]["entry_time"][:10]
        last = decision_dicts[-1]["exit_time"][:10]
        print(f"  Period:        {first} → {last}")


if __name__ == "__main__":
    asyncio.run(main())
