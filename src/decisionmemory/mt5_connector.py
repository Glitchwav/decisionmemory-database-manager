"""
MT5 Connector - Bridge between MT5 demo account and DecisionMemory.
Records real demo decisions into DecisionJournal automatically.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .journal import DecisionJournal
from .state import StateManager


class MT5Connector:
    """
    Connects to MetaDecisionMaker 5 demo account and records decisions.

    Phase 1: Manual polling mode (agent calls sync_decisions)
    Phase 2: Real-time event hooks (if MT5 API supports)
    """

    def __init__(
        self,
        journal: Optional[DecisionJournal] = None,
        state_manager: Optional[StateManager] = None
    ):
        """
        Initialize MT5 Connector.

        Args:
            journal: DecisionJournal instance
            state_manager: StateManager instance
        """
        self.journal = journal or DecisionJournal()
        self.state_manager = state_manager or StateManager()
        self.mt5 = None
        self._init_mt5()

    def _init_mt5(self):
        """Initialize MT5 connection"""
        try:
            import MetaDecisionMaker5 as MT5
            self.mt5 = MT5
        except ImportError:
            # MT5 library not available - will use mock/file mode
            self.mt5 = None

    def connect(
        self,
        login: int,
        password: str,
        server: str,
        path: Optional[str] = None
    ) -> bool:
        """
        Connect to MT5 account.

        Args:
            login: MT5 account number
            password: Account password
            server: Provider server name
            path: Optional MT5 terminal path

        Returns:
            True if connected successfully
        """
        if not self.mt5:
            raise RuntimeError("MetaDecisionMaker5 library not installed. Run: pip install MetaDecisionMaker5")

        # Initialize MT5
        if path:
            if not self.mt5.initialize(path=path):
                return False
        else:
            if not self.mt5.initialize():
                return False

        # Login
        authorized = self.mt5.login(login=login, password=password, server=server)

        if not authorized:
            self.mt5.shutdown()
            return False

        return True

    def disconnect(self):
        """Disconnect from MT5"""
        if self.mt5:
            self.mt5.shutdown()

    def sync_decisions(self, agent_id: str = "ng-gold-agent") -> Dict[str, int]:
        """
        Sync MT5 decisions to DecisionJournal.
        Checks for new closed positions since last sync.

        Args:
            agent_id: Agent identifier for state tracking

        Returns:
            Dict with sync stats: {synced: int, skipped: int, errors: int}
        """
        if not self.mt5:
            raise RuntimeError("MT5 not connected")

        # Load last sync timestamp from state
        state = self.state_manager.load_state(agent_id)
        last_sync = state.warm_memory.get("last_mt5_sync_timestamp", 0)

        # Get history deals since last sync
        from_date = datetime.fromtimestamp(last_sync) if last_sync > 0 else datetime(2020, 1, 1)
        to_date = datetime.now()

        history = self.mt5.history_deals_get(from_date, to_date)

        if history is None:
            return {"synced": 0, "skipped": 0, "errors": 1}

        synced = 0
        skipped = 0
        errors = 0

        # Group deals by position ticket
        positions = self._group_deals_by_position(history)

        for position_ticket, deals in positions.items():
            try:
                # Check if already synced
                decision_id = f"MT5-{position_ticket}"
                existing = self.journal.get_decision(decision_id)

                if existing:
                    skipped += 1
                    continue

                # Extract decision data from deals
                decision_data = self._extract_decision_data(deals)

                if not decision_data:
                    skipped += 1
                    continue

                # Record decision
                self.journal.record_decision(
                    decision_id=decision_id,
                    symbol=decision_data['symbol'],
                    direction=decision_data['direction'],
                    lot_size=decision_data['lot_size'],
                    strategy=decision_data['strategy'],
                    confidence=decision_data['confidence'],
                    reasoning=decision_data['reasoning'],
                    market_context=decision_data['market_context'],
                    references=decision_data.get('references', [])
                )

                # Record outcome if closed
                if decision_data.get('exit_price'):
                    self.journal.record_outcome(
                        decision_id=decision_id,
                        exit_price=decision_data['exit_price'],
                        pnl=decision_data['pnl'],
                        exit_reasoning=decision_data['exit_reasoning'],
                        pnl_r=decision_data.get('pnl_r'),
                        hold_duration=decision_data.get('hold_duration'),
                        slippage=decision_data.get('slippage')
                    )

                synced += 1

            except Exception as e:
                print(f"Error syncing position {position_ticket}: {e}")
                errors += 1

        # Update last sync timestamp
        self.state_manager.update_warm_memory(
            agent_id,
            "last_mt5_sync_timestamp",
            int(to_date.timestamp())
        )

        return {"synced": synced, "skipped": skipped, "errors": errors}

    def _group_deals_by_position(self, deals: tuple) -> Dict[int, List[Any]]:
        """Group MT5 deals by position ticket."""
        positions: Dict[int, List[Any]] = {}

        for deal in deals:
            ticket = deal.position_id
            if ticket not in positions:
                positions[ticket] = []
            positions[ticket].append(deal)

        return positions

    def _extract_decision_data(self, deals: List) -> Optional[Dict[str, Any]]:
        """
        Extract DecisionRecord data from MT5 deals.

        Args:
            deals: List of MT5 deal objects for one position

        Returns:
            Decision data dict or None if invalid
        """
        if not deals:
            return None

        # Sort by time
        deals = sorted(deals, key=lambda d: d.time)

        entry_deal = deals[0]
        exit_deal = deals[-1] if len(deals) > 1 else None

        # Extract basic data
        symbol = entry_deal.symbol
        lot_size = entry_deal.volume

        # Determine direction (0=BUY, 1=SELL in MT5)
        direction = "long" if entry_deal.type == 0 else "short"

        # Extract prices
        entry_price = entry_deal.price
        exit_price = exit_deal.price if exit_deal else None

        # Calculate P&L
        pnl = sum(d.profit for d in deals)

        # Extract timestamps
        entry_time = datetime.fromtimestamp(entry_deal.time)
        exit_time = datetime.fromtimestamp(exit_deal.time) if exit_deal else None

        # Calculate hold duration
        hold_duration = None
        if exit_time:
            hold_duration = int((exit_time - entry_time).total_seconds() / 60)  # Minutes

        # Build market context
        market_context = {
            "price": entry_price,
            "session": self._detect_session(entry_time)
        }

        # Build decision data
        decision_data = {
            "symbol": symbol,
            "direction": direction,
            "lot_size": lot_size,
            "strategy": "NG_Gold",  # Default - could extract from comment field
            "confidence": 0.5,  # Default - MT5 doesn't store this
            "reasoning": f"MT5 demo decision on {symbol}",  # Default
            "market_context": market_context,
            "exit_price": exit_price,
            "pnl": pnl,
            "exit_reasoning": "Position closed" if exit_deal else None,
            "hold_duration": hold_duration
        }

        return decision_data

    def _detect_session(self, timestamp: datetime) -> str:
        """Detect decision_making session from timestamp"""
        hour = timestamp.hour

        if 0 <= hour < 8:
            return "asian"
        elif 8 <= hour < 16:
            return "london"
        elif 16 <= hour < 24:
            return "newyork"
        else:
            return "unknown"
