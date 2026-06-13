"""
Backtest Importer - Parse MT5 Strategy Tester HTML reports and import as DecisionRecords.

Reads UTF-16LE HTML reports from MT5 Strategy Tester, pairs entry/exit deals,
and bulk-imports them into decisionmemory SQLite database.

All imported decisions have source="backtest" in their reasoning field.
"""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def classify_session(hour: int) -> str:
    """Classify decision_making session based on server hour (GMT+2/+3)."""
    if 0 <= hour < 8:
        return "asian"
    elif 8 <= hour < 16:
        return "london"
    else:
        return "newyork"


def parse_mt5_report(report_path: str) -> List[Dict[str, Any]]:
    """
    Parse an MT5 Strategy Tester HTML report and extract completed decisions.

    Args:
        report_path: Path to the .htm report file (UTF-16LE encoded)

    Returns:
        List of decision dicts with: entry_time, exit_time, symbol, direction,
        volume, entry_price, exit_price, pnl, hold_duration_min
    """
    if not os.path.exists(report_path):
        return []

    content = Path(report_path).read_text(encoding='utf-16-le')
    lines = content.split('\n')

    # Parse deal rows: <tr bgcolor=...><td>...</td>...<td>in/out</td>...
    entries = []  # pending entry deals (FIFO queue per direction)
    decisions = []

    for line in lines:
        # Only process deal rows with in/out direction
        if '<td>in</td>' not in line and '<td>out</td>' not in line:
            continue

        # Extract all <td> values
        td_values = re.findall(r'<td[^>]*>([^<]*)</td>', line)
        if len(td_values) < 12:
            continue

        # Fields: 0=date, 1=deal#, 2=symbol, 3=type(buy/sell), 4=in/out,
        #         5=volume, 6=price, 7=order#, 8=commission, 9=fee,
        #         10=profit, 11=balance, 12=comment(optional)
        deal_time_str = td_values[0]
        deal_type = td_values[3]      # buy or sell
        in_out = td_values[4]         # in or out
        volume_str = td_values[5]
        price_str = td_values[6]
        profit_str = td_values[10].replace(' ', '')  # "10 000.00" → "10000.00"

        try:
            deal_time = datetime.strptime(deal_time_str, "%Y.%m.%d %H:%M:%S")
            deal_time = deal_time.replace(tzinfo=timezone.utc)
            volume = float(volume_str)
            price = float(price_str)
        except (ValueError, IndexError):
            continue

        if in_out == 'in':
            # Entry deal
            direction = 'long' if deal_type == 'buy' else 'short'
            entries.append({
                'time': deal_time,
                'direction': direction,
                'volume': volume,
                'price': price,
                'symbol': td_values[2]
            })
        elif in_out == 'out' and entries:
            # Exit deal - match with first pending entry
            try:
                pnl = float(profit_str)
            except ValueError:
                pnl = 0.0

            # Pop first entry (FIFO matching)
            entry = entries.pop(0)

            # Calculate hold duration in minutes
            hold_minutes = int((deal_time - entry['time']).total_seconds() / 60)

            decisions.append({
                'entry_time': entry['time'],
                'exit_time': deal_time,
                'symbol': entry['symbol'],
                'direction': entry['direction'],
                'volume': entry['volume'],
                'entry_price': entry['price'],
                'exit_price': price,
                'pnl': pnl,
                'hold_duration_min': max(hold_minutes, 1),
            })

    return decisions


def parse_variant_tag(tag: str) -> Dict[str, str]:
    """
    Parse a variant tag into strategy, symbol, direction, and params.

    Examples:
        VB_XAUUSD_BUY_RR3_BUF0.1 → {strategy: VolBreakout, symbol: XAUUSD, ...}
        IM_EURUSD_BOTH_RR2.5_TH0.55 → {strategy: IntradayMomentum, ...}
    """
    parts = tag.split('_')
    strategy_map = {'VB': 'VolBreakout', 'IM': 'IntradayMomentum',
                    'PB': 'PullbackEntry', 'MR': 'MeanReversion'}

    result = {
        'strategy': strategy_map.get(parts[0], parts[0]),
        'symbol': parts[1] if len(parts) > 1 else 'UNKNOWN',
        'direction_filter': parts[2] if len(parts) > 2 else 'BOTH',
        'params': '_'.join(parts[3:]) if len(parts) > 3 else '',
        'tag': tag,
    }
    return result


def build_decision_records(
    decisions: List[Dict[str, Any]],
    variant_tag: str,
    backtest_params: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Convert parsed decisions into decisionmemory DecisionRecord format.

    Args:
        decisions: Parsed decisions from parse_mt5_report()
        variant_tag: The variant identifier (e.g., VB_XAUUSD_BUY_RR3_BUF0.1)
        backtest_params: Optional dict of backtest parameters

    Returns:
        List of dicts ready for db.insert_decision()
    """
    variant_info = parse_variant_tag(variant_tag)
    records = []

    for i, decision in enumerate(decisions):
        decision_id = f"BT-{variant_tag}-{i+1:04d}"

        # Market context
        session = classify_session(decision['entry_time'].hour)
        market_ctx = {
            'price': decision['entry_price'],
            'session': session,
            'indicators': {}
        }

        # Build reasoning with source tag
        reasoning = (
            f"Backtest: {variant_info['strategy']} | "
            f"{variant_info['params']} | "
            f"{decision['direction']} entry at {session} session"
        )

        # Tags for filtering
        tags = [
            'backtest',
            variant_info['strategy'],
            variant_info['symbol'],
            variant_info['direction_filter'],
            session,
        ]
        if backtest_params:
            tags.append(f"params:{variant_info['params']}")

        record = {
            'id': decision_id,
            'timestamp': decision['entry_time'],
            'symbol': decision['symbol'],
            'direction': decision['direction'],
            'lot_size': decision['volume'],
            'strategy': variant_info['strategy'],
            'confidence': 0.5,  # No real confidence for backtests
            'reasoning': reasoning,
            'market_context': market_ctx,
            'references': [],
            'exit_timestamp': decision['exit_time'],
            'exit_price': decision['exit_price'],
            'pnl': decision['pnl'],
            'pnl_r': None,
            'hold_duration': decision['hold_duration_min'],
            'exit_reasoning': f"Backtest exit | source=backtest | variant={variant_tag}",
            'slippage': None,
            'execution_quality': None,
            'lessons': None,
            'tags': tags,
            'grade': None,
        }
        records.append(record)

    return records


def import_batch(
    report_dir: str,
    db_path: str,
    manifest_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Batch import all backtest reports from a directory into decisionmemory.

    Args:
        report_dir: Directory containing *_report.htm files
        db_path: Path to decisionmemory SQLite database
        manifest_path: Optional manifest.csv for variant metadata

    Returns:
        Import statistics dict
    """
    from .db import Database

    db = Database(db_path)

    stats = {
        'total_reports': 0,
        'total_decisions': 0,
        'imported': 0,
        'skipped': 0,  # duplicates
        'failed': 0,
        'empty_reports': 0,
        'by_strategy': {},
        'by_symbol': {},
    }

    # Find all report files
    report_files = sorted(Path(report_dir).glob('*_report.htm'))
    stats['total_reports'] = len(report_files)

    for report_path in report_files:
        # Extract variant tag from filename: VB_XAUUSD_BUY_RR3_BUF0.1_report.htm
        tag = report_path.stem.replace('_report', '')

        # Parse decisions
        decisions = parse_mt5_report(str(report_path))
        if not decisions:
            stats['empty_reports'] += 1
            continue

        # Build DecisionRecords
        records = build_decision_records(decisions, tag)
        stats['total_decisions'] += len(records)

        # Track by strategy/symbol
        variant_info = parse_variant_tag(tag)
        strategy = variant_info['strategy']
        symbol = variant_info['symbol']
        stats['by_strategy'][strategy] = stats['by_strategy'].get(strategy, 0) + len(records)
        stats['by_symbol'][symbol] = stats['by_symbol'].get(symbol, 0) + len(records)

        # Batch insert
        batch_count = 0
        for record in records:
            success = db.insert_decision(record)
            if success:
                stats['imported'] += 1
                batch_count += 1
            else:
                stats['skipped'] += 1

        print(f"  {tag}: {len(decisions)} decisions parsed, {batch_count} imported")

    return stats


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m decisionmemory.backtest_importer <report_dir> [db_path]")
        print("  report_dir: Directory with *_report.htm files")
        print("  db_path: decisionmemory SQLite DB (default: data/decisionmemory.db)")
        sys.exit(1)

    report_dir = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "data/decisionmemory.db"

    print(f"Importing from: {report_dir}")
    print(f"Database: {db_path}")
    print()

    stats = import_batch(report_dir, db_path)

    print()
    print("=== IMPORT SUMMARY ===")
    print(f"Reports scanned: {stats['total_reports']}")
    print(f"Empty reports:   {stats['empty_reports']}")
    print(f"Decisions parsed:   {stats['total_decisions']}")
    print(f"Imported:        {stats['imported']}")
    print(f"Skipped (dupes): {stats['skipped']}")
    print()
    print("By strategy:")
    for s, n in sorted(stats['by_strategy'].items()):
        print(f"  {s}: {n}")
    print("By symbol:")
    for s, n in sorted(stats['by_symbol'].items()):
        print(f"  {s}: {n}")
