"""
Decision Adapter - Convert MT5 deals to DecisionMemory DecisionRecord format
Based on ariadng/metadecision_maker-mcp-server + DecisionMemory Protocol DEC-014

Architecture:
  MT5 Terminal → MetaDecisionMaker5 Python API → decision_adapter.py → DecisionJournal
"""

import os
import time
try:
    import MetaDecisionMaker5 as MT5
except ImportError:
    MT5 = None
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

MT5_LOGIN = int(os.getenv('MT5_LOGIN', '0'))
MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
MT5_SERVER = os.getenv('MT5_SERVER', '')
MT5_PATH = os.getenv('MT5_PATH', r'C:\Program Files\MetaDecisionMaker 5\terminal64.exe')
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', '60'))
DECISIONMEMORY_API = os.getenv('DECISIONMEMORY_API', 'http://localhost:8000')

# Magic number → strategy name mapping
MAGIC_TO_STRATEGY = {
    0: "Manual",                   # Manual decisions (MT5 default, no EA)
    260111: "NG_Gold",             # Mode 0: Impulse-Retrace-Continuation
    260112: "VolBreakout",         # Mode 2
    260113: "MeanReversion",       # Mode 3 (DISABLED)
    260115: "LondonMomentum",      # Mode 5 (DISABLED)
    260118: "IntradayMomentum",    # Mode 8
    20260217: "Pullback",          # Separate EA
}

# State tracking
last_synced_position_id = 0


def init_mt5() -> bool:
    """Initialize MT5 connection"""
    if MT5 is None:
        print("[ERROR] MetaDecisionMaker5 package not installed. Run: pip install MetaDecisionMaker5")
        return False
    try:
        if not MT5.initialize(path=MT5_PATH):
            print(f"[ERROR] MT5 initialize() failed: {MT5.last_error()}")
            return False
        
        authorized = MT5.login(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
        
        if not authorized:
            print(f"[ERROR] MT5 login() failed: {MT5.last_error()}")
            MT5.shutdown()
            return False
        
        account_info = MT5.account_info()
        print(f"[OK] Connected to MT5: {account_info.name} ({account_info.server})")
        print(f"[OK] Account: {account_info.login}, Balance: ${account_info.balance:.2f}")
        
        return True
    
    except Exception as e:
        print(f"[ERROR] MT5 initialization failed: {e}")
        return False


def get_completed_positions(from_date: datetime) -> List[tuple]:
    """
    Get completed positions (has both entry and exit deals) since from_date.

    Returns:
        List of (position_id, deals) tuples
    """
    if MT5 is None:
        return []
    # CRITICAL: Use UTC timezone (CIO fix - DEC-014)
    timezone = pytz.timezone("Etc/UTC")
    
    # Convert to UTC if not already
    if from_date.tzinfo is None:
        from_date = timezone.localize(from_date)
    
    # Provider timezone may differ from UTC - query into "future" to avoid missing decisions
    # Use end of current year as safe upper bound
    to_date = datetime(datetime.now().year, 12, 31, 23, 59, 59, tzinfo=timezone)
    
    deals = MT5.history_deals_get(from_date, to_date)
    
    if deals is None or len(deals) == 0:
        return []
    
    # Group by position_id
    positions = {}
    for deal in deals:
        pos_id = deal.position_id
        
        # Skip non-position deals (deposits, withdrawals, etc.)
        if pos_id == 0:
            continue
        
        if pos_id not in positions:
            positions[pos_id] = []
        positions[pos_id].append(deal)
    
    # Filter completed positions (has both entry and exit)
    completed = []
    for pos_id, pos_deals in positions.items():
        has_entry = any(d.entry == 0 for d in pos_deals)  # DEAL_ENTRY_IN
        has_exit = any(d.entry == 1 for d in pos_deals)   # DEAL_ENTRY_OUT
        
        if has_entry and has_exit:
            completed.append((pos_id, sorted(pos_deals, key=lambda d: d.time)))
    
    return completed


def convert_to_decision_record(position_id: int, deals: List) -> Dict[str, Any]:
    """
    Convert MT5 position deals to DecisionMemory DecisionRecord format.
    
    Args:
        position_id: MT5 position ID
        deals: List of MT5 deals for this position
    
    Returns:
        DecisionRecord dict ready for DecisionJournal API
    """
    # Get entry and exit deals
    entry_deal = [d for d in deals if d.entry == 0][0]  # First entry
    exit_deal = [d for d in deals if d.entry == 1][-1]   # Last exit
    
    # Calculate totals
    total_profit = sum(d.profit for d in deals)
    total_commission = sum(d.commission for d in deals)
    total_swap = sum(d.swap for d in deals)
    
    # Determine direction
    direction = "long" if entry_deal.type == 0 else "short"
    
    # Calculate hold duration (minutes)
    hold_duration = int((exit_deal.time - entry_deal.time) / 60)
    
    # Market context
    entry_hour = datetime.fromtimestamp(entry_deal.time).hour
    if 0 <= entry_hour < 8:
        session = "asian"
    elif 8 <= entry_hour < 16:
        session = "london"
    else:
        session = "newyork"
    
    market_context = {
        "price": entry_deal.price,
        "session": session
    }
    
    # Resolve strategy from magic number
    magic = entry_deal.magic
    strategy = MAGIC_TO_STRATEGY.get(magic, f"Unknown_Magic_{magic}")

    # Build DecisionRecord
    decision_record = {
        # Decision phase (when decision was opened)
        "decision_id": f"MT5-{position_id}",
        "symbol": entry_deal.symbol,
        "direction": direction,
        "lot_size": entry_deal.volume,
        "strategy": strategy,
        "confidence": 0.5,       # Default - MT5 doesn't store this
        "reasoning": f"Auto-synced from MT5 (magic={magic}, position={position_id})",
        "market_context": {**market_context, "magic_number": magic},
        "references": [],
        
        # Outcome phase (when decision was closed)
        "exit_price": exit_deal.price,
        "pnl": total_profit,
        "exit_reasoning": f"Position closed (commission: ${total_commission:.2f}, swap: ${total_swap:.2f})",
        "hold_duration": hold_duration,
        
        # Metadata
        "mt5_position_id": position_id,
        "mt5_entry_ticket": entry_deal.ticket,
        "mt5_exit_ticket": exit_deal.ticket,
        "entry_time": datetime.fromtimestamp(entry_deal.time).isoformat(),
        "exit_time": datetime.fromtimestamp(exit_deal.time).isoformat(),
    }
    
    return decision_record


def sync_to_decisionmemory(decision_record: Dict[str, Any]) -> bool:
    """
    Sync one decision record to DecisionMemory API.
    
    Args:
        decision_record: DecisionRecord dict
    
    Returns:
        True if successful
    """
    import requests
    
    decision_id = decision_record['decision_id']
    
    try:
        # Record decision
        decision_resp = requests.post(
            f"{DECISIONMEMORY_API}/decision/record_decision",
            json={
                "decision_id": decision_record['decision_id'],
                "symbol": decision_record['symbol'],
                "direction": decision_record['direction'],
                "lot_size": decision_record['lot_size'],
                "strategy": decision_record['strategy'],
                "confidence": decision_record['confidence'],
                "reasoning": decision_record['reasoning'],
                "market_context": decision_record['market_context'],
                "references": decision_record['references']
            },
            timeout=5
        )
        
        if decision_resp.status_code != 200:
            print(f"[ERROR] Failed to record decision for {decision_id}: {decision_resp.text}")
            return False
        
        # Record outcome
        outcome_resp = requests.post(
            f"{DECISIONMEMORY_API}/decision/record_outcome",
            json={
                "decision_id": decision_record['decision_id'],
                "exit_price": decision_record['exit_price'],
                "pnl": decision_record['pnl'],
                "exit_reasoning": decision_record['exit_reasoning'],
                "hold_duration": decision_record['hold_duration']
            },
            timeout=5
        )
        
        if outcome_resp.status_code != 200:
            print(f"[ERROR] Failed to record outcome for {decision_id}: {outcome_resp.text}")
            return False
        
        print(f"[SYNC] {decision_id}: {decision_record['symbol']} {decision_record['direction']} "
              f"{decision_record['lot_size']} lots, P&L: ${decision_record['pnl']:.2f}, "
              f"Duration: {decision_record['hold_duration']}min")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API request failed for {decision_id}: {e}")
        return False


def main_loop():
    """Main synchronization loop"""
    global last_synced_position_id
    
    print("=" * 60)
    print("DecisionMemory Adapter - MT5 to DecisionMemory")
    print("=" * 60)
    print(f"API Endpoint: {DECISIONMEMORY_API}")
    print(f"Sync Interval: {SYNC_INTERVAL}s")
    print(f"MT5 Account: {MT5_LOGIN} @ {MT5_SERVER}")
    print("=" * 60)
    
    # Initialize MT5
    if not init_mt5():
        print("[FATAL] Cannot connect to MT5. Exiting.")
        return
    
    print("\n[OK] Monitoring started. Press Ctrl+C to stop.\n")
    
    try:
        # Use UTC timezone (CIO fix - DEC-014)
        timezone = pytz.timezone("Etc/UTC")
        
        while True:
            # Check for new completed positions
            # Use wide date range to avoid provider timezone issues
            # Start from beginning of current year
            from_date = datetime(datetime.now().year, 1, 1, tzinfo=timezone)
            completed_positions = get_completed_positions(from_date)
            
            # Filter new positions
            new_positions = [(pid, deals) for pid, deals in completed_positions if pid > last_synced_position_id]
            
            if len(new_positions) > 0:
                print(f"[SCAN] Found {len(new_positions)} new completed position(s)")
                
                for position_id, deals in new_positions:
                    # Convert to DecisionRecord
                    decision_record = convert_to_decision_record(position_id, deals)
                    
                    # Sync to DecisionMemory
                    success = sync_to_decisionmemory(decision_record)
                    
                    if success:
                        # Update last synced position ID
                        last_synced_position_id = max(last_synced_position_id, position_id)
                
                print(f"[OK] Sync complete. Last position ID: {last_synced_position_id}\n")
            
            # Sleep until next check
            time.sleep(SYNC_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down gracefully...")
        MT5.shutdown()
        print("[OK] Disconnected from MT5. Goodbye!")


if __name__ == "__main__":
    main_loop()
