"""
DecisionJournal module - Structured decision memory with full context.
Implements Blueprint Section 2.1 DecisionJournal functionality.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .db import Database, get_database
from .models import MarketContext, DecisionDirection, DecisionRecord


class DecisionJournal:
    """
    DecisionJournal records every decision decision with full context:
    entry/exit reasoning, market state, strategy used, confidence level,
    outcome, and post-decision notes.
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initialize DecisionJournal.

        Args:
            db: Database instance (creates new if None)
        """
        self.db = db or get_database()

    def record_decision(
        self,
        decision_id: str,
        symbol: str,
        direction: str,
        lot_size: float,
        strategy: str,
        confidence: float,
        reasoning: str,
        market_context: Dict[str, Any],
        references: Optional[List[str]] = None
    ) -> DecisionRecord:
        """
        Record a decision decision with full context.

        Args:
            decision_id: Unique decision identifier (T-YYYY-NNNN)
            symbol: DecisionMaking instrument (XAUUSD, BTCUSDT, etc.)
            direction: 'long' or 'short'
            lot_size: Position size
            strategy: Strategy tag (VolBreakout, Pullback, etc.)
            confidence: Agent confidence score (0.0 - 1.0)
            reasoning: Natural language explanation of WHY
            market_context: Market snapshot (price, ATR, session, etc.)
            references: Past decision IDs that informed this decision

        Returns:
            DecisionRecord instance

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Confidence must be 0.0-1.0, got {confidence}")

        if direction not in ['long', 'short']:
            raise ValueError(f"Direction must be 'long' or 'short', got {direction}")

        # Create DecisionRecord
        decision = DecisionRecord(
            id=decision_id,
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            direction=DecisionDirection(direction),
            lot_size=lot_size,
            strategy=strategy,
            confidence=confidence,
            reasoning=reasoning,
            market_context=MarketContext(**market_context),
            references=references or []
        )

        # Persist to database
        success = self.db.insert_decision(decision.model_dump())

        if not success:
            raise RuntimeError(f"Failed to insert decision {decision_id} to database")

        return decision

    def record_outcome(
        self,
        decision_id: str,
        exit_price: float,
        pnl: float,
        exit_reasoning: str,
        pnl_r: Optional[float] = None,
        hold_duration: Optional[int] = None,
        slippage: Optional[float] = None,
        execution_quality: Optional[float] = None,
        lessons: Optional[str] = None
    ) -> bool:
        """
        Record decision outcome after position closes.

        Args:
            decision_id: Decision ID to update
            exit_price: Exit price
            pnl: Realized P&L in account currency
            exit_reasoning: Why the agent exited
            pnl_r: P&L in R-multiples (optional)
            hold_duration: Minutes held (optional)
            slippage: Entry slippage in pips (optional)
            execution_quality: 0.0-1.0 score (optional)
            lessons: What was learned (optional)

        Returns:
            True if successful

        Raises:
            ValueError: If validation fails
        """
        # Validate
        if execution_quality is not None and not (0.0 <= execution_quality <= 1.0):
            raise ValueError(f"Execution quality must be 0.0-1.0, got {execution_quality}")

        outcome_data = {
            'exit_timestamp': datetime.now(timezone.utc),
            'exit_price': exit_price,
            'pnl': pnl,
            'exit_reasoning': exit_reasoning
        }

        # Optional fields
        if pnl_r is not None:
            outcome_data['pnl_r'] = pnl_r
        if hold_duration is not None:
            outcome_data['hold_duration'] = hold_duration
        if slippage is not None:
            outcome_data['slippage'] = slippage
        if execution_quality is not None:
            outcome_data['execution_quality'] = execution_quality
        if lessons:
            outcome_data['lessons'] = lessons

        # Update database
        success = self.db.update_decision_outcome(decision_id, outcome_data)

        if not success:
            raise RuntimeError(f"Failed to update decision {decision_id} outcome")

        return True

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """
        Retrieve a decision record by ID.

        Args:
            decision_id: Decision ID

        Returns:
            DecisionRecord or None if not found
        """
        decision_data = self.db.get_decision(decision_id)

        if not decision_data:
            return None

        # Convert back to DecisionRecord model
        return DecisionRecord(**decision_data)

    def query_history(
        self,
        strategy: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[DecisionRecord]:
        """
        Query decision history with filters.

        Args:
            strategy: Filter by strategy tag
            symbol: Filter by symbol
            limit: Maximum results

        Returns:
            List of DecisionRecord instances
        """
        decisions_data = self.db.query_decisions(
            strategy=strategy,
            symbol=symbol,
            limit=limit
        )

        return [DecisionRecord(**td) for td in decisions_data]

    def get_active_decisions(self) -> List[DecisionRecord]:
        """
        Get all currently open decisions (no exit timestamp).

        Returns:
            List of active DecisionRecord instances
        """
        # Query all recent decisions and filter for active
        all_decisions = self.db.query_decisions(limit=1000)

        active = []
        for td in all_decisions:
            if td.get('exit_timestamp') is None:
                active.append(DecisionRecord(**td))

        return active
