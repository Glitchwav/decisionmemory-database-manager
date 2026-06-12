"""
Decision repository — data access layer for dashboard.

Tries PostgreSQL first, falls back to SurrealDB.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from ..db import Database, get_database
from ..exceptions import DatabaseConnectionError, DatabaseQueryError

logger = logging.getLogger(__name__)


@dataclass
class DecisionStats:
    """Raw decision statistics from the database."""

    total_decisions: int = 0
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    strategies: list = None
    last_decision_date: Optional[str] = None

    def __post_init__(self):
        if self.strategies is None:
            self.strategies = []


@dataclass
class MemoryStats:
    """Raw memory statistics from the database."""

    memory_count: int = 0
    avg_confidence: float = 0.0


@dataclass
class ScoreStats:
    """Raw score/drawdown statistics from the database."""

    current_score: float = 0.0
    peak_score: float = 0.0
    drawdown_state: float = 0.0


class DecisionRepository:
    """Data access layer for decision and memory data."""

    def __init__(self, db: Optional[Database] = None):
        self._db = db

    def _get_db(self) -> Database:
        if self._db is not None:
            return self._db
        try:
            return get_database()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseConnectionError(f"Cannot connect to database: {e}")

    def get_decision_stats(self) -> DecisionStats:
        """Query decision_records for P&L statistics."""
        db = self._get_db()
        conn = db._get_connection()
        try:
            # Aggregate P&L stats from closed decisions (pnl IS NOT NULL)
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_decisions,
                    COALESCE(SUM(pnl), 0.0) as total_pnl,
                    COALESCE(SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END), 0.0) as gross_profit,
                    COALESCE(ABS(SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END)), 0.0) as gross_loss,
                    COALESCE(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END), 0) as win_count,
                    COALESCE(SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END), 0) as loss_count
                FROM decision_records
                WHERE pnl IS NOT NULL
            """).fetchone()

            # Distinct strategies
            strategy_rows = conn.execute(
                "SELECT DISTINCT strategy FROM decision_records ORDER BY strategy"
            ).fetchall()
            strategies = [r["strategy"] for r in strategy_rows]

            # Last decision date
            last_row = conn.execute(
                "SELECT MAX(timestamp) as last_ts FROM decision_records"
            ).fetchone()
            last_decision_date = last_row["last_ts"] if last_row else None

            return DecisionStats(
                total_decisions=row["total_decisions"],
                total_pnl=row["total_pnl"],
                gross_profit=row["gross_profit"],
                gross_loss=row["gross_loss"],
                win_count=row["win_count"],
                loss_count=row["loss_count"],
                strategies=strategies,
                last_decision_date=last_decision_date,
            )
        except DatabaseConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to query decision stats: {e}")
            raise DatabaseQueryError(f"Decision stats query failed: {e}")
        finally:
            conn.close()

    def get_memory_stats(self) -> MemoryStats:
        """Query episodic_memory for memory count and avg confidence."""
        db = self._get_db()
        conn = db._get_connection()
        try:
            row = conn.execute("""
                SELECT
                    COUNT(*) as memory_count,
                    COALESCE(AVG(confidence), 0.0) as avg_confidence
                FROM episodic_memory
            """).fetchone()

            return MemoryStats(
                memory_count=row["memory_count"],
                avg_confidence=round(row["avg_confidence"], 4),
            )
        except Exception as e:
            logger.error(f"Failed to query memory stats: {e}")
            raise DatabaseQueryError(f"Memory stats query failed: {e}")
        finally:
            conn.close()

    def get_score_stats(self) -> ScoreStats:
        """Query affective_state for score and drawdown."""
        db = self._get_db()
        conn = db._get_connection()
        try:
            row = conn.execute("""
                SELECT current_score, peak_score, drawdown_state
                FROM affective_state
                LIMIT 1
            """).fetchone()

            if row is None:
                return ScoreStats()

            return ScoreStats(
                current_score=row["current_score"],
                peak_score=row["peak_score"],
                drawdown_state=row["drawdown_state"],
            )
        except Exception as e:
            logger.error(f"Failed to query score stats: {e}")
            raise DatabaseQueryError(f"Score stats query failed: {e}")
        finally:
            conn.close()

    def get_closed_decisions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> List["DecisionRow"]:
        """
        Query decision_records WHERE pnl IS NOT NULL, ordered by timestamp ASC.

        Returns raw rows as DecisionRow dataclasses.
        """
        db = self._get_db()
        conn = db._get_connection()
        try:
            query = """
                SELECT id, timestamp, strategy, pnl, pnl_r
                FROM decision_records
                WHERE pnl IS NOT NULL
            """
            params: list = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            if strategy:
                query += " AND strategy = ?"
                params.append(strategy)

            query += " ORDER BY timestamp ASC"

            rows = conn.execute(query, params).fetchall()
            return [
                DecisionRow(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    strategy=r["strategy"],
                    pnl=r["pnl"],
                    pnl_r=r["pnl_r"],
                )
                for r in rows
            ]
        except DatabaseConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to query closed decisions: {e}")
            raise DatabaseQueryError(f"Closed decisions query failed: {e}")
        finally:
            conn.close()

    def get_memory_growth_by_regime(self) -> List["MemoryRegimeRow"]:
        """
        Query episodic_memory grouped by DATE(created_at) and context_regime.

        Returns raw counts per (date, regime).
        """
        db = self._get_db()
        conn = db._get_connection()
        try:
            rows = conn.execute("""
                SELECT
                    DATE(created_at) as date,
                    COALESCE(context_regime, 'unknown') as regime,
                    COUNT(*) as count
                FROM episodic_memory
                GROUP BY DATE(created_at), COALESCE(context_regime, 'unknown')
                ORDER BY date ASC
            """).fetchall()
            return [
                MemoryRegimeRow(
                    date=r["date"],
                    regime=r["regime"],
                    count=r["count"],
                )
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to query memory growth: {e}")
            raise DatabaseQueryError(f"Memory growth query failed: {e}")
        finally:
            conn.close()


    def get_calibration_data(self) -> List["CalibrationRow"]:
        """
        Query episodic_memory WHERE confidence IS NOT NULL AND pnl_r IS NOT NULL.

        Returns decision_id, confidence, pnl_r, strategy for calibration plot.
        """
        db = self._get_db()
        conn = db._get_connection()
        try:
            rows = conn.execute("""
                SELECT id, confidence, pnl_r, strategy
                FROM episodic_memory
                WHERE confidence IS NOT NULL AND pnl_r IS NOT NULL
                ORDER BY timestamp ASC
            """).fetchall()
            return [
                CalibrationRow(
                    decision_id=r["id"],
                    entry_confidence=r["confidence"],
                    actual_pnl_r=r["pnl_r"],
                    strategy=r["strategy"],
                )
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to query calibration data: {e}")
            raise DatabaseQueryError(f"Calibration query failed: {e}")
        finally:
            conn.close()

    def get_strategy_decisions(self, strategy: str) -> List["StrategyDecisionRow"]:
        """
        Query decision_records and episodic_memory for a specific strategy.

        Returns detailed decision rows for strategy analysis.
        """
        db = self._get_db()
        conn = db._get_connection()
        try:
            rows = conn.execute("""
                SELECT
                    tr.id, tr.timestamp, tr.pnl, tr.pnl_r,
                    tr.hold_duration,
                    em.context_session, em.confidence
                FROM decision_records tr
                LEFT JOIN episodic_memory em ON tr.id = em.id
                WHERE tr.strategy = ? AND tr.pnl IS NOT NULL
                ORDER BY tr.timestamp ASC
            """, (strategy,)).fetchall()
            return [
                StrategyDecisionRow(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    pnl=r["pnl"],
                    pnl_r=r["pnl_r"],
                    hold_duration=r["hold_duration"],
                    context_session=r["context_session"],
                    confidence=r["confidence"],
                )
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to query strategy decisions: {e}")
            raise DatabaseQueryError(f"Strategy decisions query failed: {e}")
        finally:
            conn.close()

    def get_adjustments(self) -> List["AdjustmentRow"]:
        """
        Query strategy_adjustments joined with patterns for strategy name.

        Returns adjustment events sorted by created_at DESC.
        """
        db = self._get_db()
        conn = db._get_connection()
        try:
            rows = conn.execute("""
                SELECT
                    sa.adjustment_id, sa.created_at, sa.adjustment_type,
                    sa.parameter, sa.old_value, sa.new_value, sa.reason,
                    sa.status, p.strategy
                FROM strategy_adjustments sa
                LEFT JOIN patterns p ON sa.source_pattern_id = p.pattern_id
                ORDER BY sa.created_at DESC
            """).fetchall()
            return [
                AdjustmentRow(
                    adjustment_id=r["adjustment_id"],
                    created_at=r["created_at"],
                    adjustment_type=r["adjustment_type"],
                    parameter=r["parameter"],
                    old_value=r["old_value"],
                    new_value=r["new_value"],
                    reason=r["reason"],
                    status=r["status"],
                    strategy=r["strategy"],
                )
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to query adjustments: {e}")
            raise DatabaseQueryError(f"Adjustments query failed: {e}")
        finally:
            conn.close()

    def get_beliefs(self) -> List["BeliefRow"]:
        """
        Query semantic_memory for Bayesian beliefs.

        Returns all beliefs sorted by sample_size DESC.
        """
        db = self._get_db()
        conn = db._get_connection()
        try:
            rows = conn.execute("""
                SELECT
                    id, proposition, alpha, beta, sample_size,
                    strategy, regime, last_confirmed, last_contradicted
                FROM semantic_memory
                ORDER BY sample_size DESC
            """).fetchall()
            return [
                BeliefRow(
                    id=r["id"],
                    proposition=r["proposition"],
                    alpha=r["alpha"],
                    beta=r["beta"],
                    sample_size=r["sample_size"],
                    strategy=r["strategy"],
                    regime=r["regime"],
                    last_confirmed=r["last_confirmed"],
                    last_contradicted=r["last_contradicted"],
                )
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to query beliefs: {e}")
            raise DatabaseQueryError(f"Beliefs query failed: {e}")
        finally:
            conn.close()

    def get_distinct_strategies(self) -> List[str]:
        """Return list of distinct strategy names from decision_records."""
        db = self._get_db()
        conn = db._get_connection()
        try:
            rows = conn.execute(
                "SELECT DISTINCT strategy FROM decision_records ORDER BY strategy"
            ).fetchall()
            return [r["strategy"] for r in rows]
        except Exception as e:
            logger.error(f"Failed to query distinct strategies: {e}")
            raise DatabaseQueryError(f"Distinct strategies query failed: {e}")
        finally:
            conn.close()


@dataclass
class DecisionRow:
    """Raw decision row from database."""

    id: str
    timestamp: str
    strategy: str
    pnl: float
    pnl_r: Optional[float] = None


@dataclass
class MemoryRegimeRow:
    """Raw memory regime count row from database."""

    date: str
    regime: str
    count: int


@dataclass
class CalibrationRow:
    """Raw calibration data row from database."""

    decision_id: str
    entry_confidence: float
    actual_pnl_r: float
    strategy: str


@dataclass
class StrategyDecisionRow:
    """Detailed decision row for strategy analysis."""

    id: str
    timestamp: str
    pnl: float
    pnl_r: Optional[float] = None
    hold_duration: Optional[int] = None
    context_session: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class AdjustmentRow:
    """Raw adjustment row from database."""

    adjustment_id: str
    created_at: str
    adjustment_type: str
    parameter: str
    old_value: str
    new_value: str
    reason: str
    status: str
    strategy: Optional[str] = None


@dataclass
class BeliefRow:
    """Raw belief row from semantic_memory."""

    id: str
    proposition: str
    alpha: float
    beta: float
    sample_size: int
    strategy: Optional[str] = None
    regime: Optional[str] = None
    last_confirmed: Optional[str] = None
    last_contradicted: Optional[str] = None
