"""
Data models for DecisionMemory Protocol.
Based on Blueprint Section 5: Decision Journal Data Schema
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DecisionDirection(str, Enum):
    """Decision direction"""
    LONG = "long"
    SHORT = "short"


class DecisionGrade(str, Enum):
    """Quality grade for decision decision (not result)"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class MarketContext(BaseModel):
    """Market context at decision time"""
    price: float
    atr: Optional[float] = None
    session: Optional[str] = None  # asian/london/newyork
    indicators: Dict[str, Any] = Field(default_factory=dict)
    news_sentiment: Optional[float] = None  # -1.0 to 1.0


class DecisionRecord(BaseModel):
    """
    Complete decision record with decision context and outcome.
    Matches Blueprint Section 5 schema exactly.
    """

    # Core identification
    id: str = Field(..., description="Unique decision ID (T-YYYY-NNNN)")
    timestamp: datetime = Field(..., description="Decision timestamp (UTC)")
    symbol: str = Field(..., description="DecisionMaking instrument (XAUUSD, BTCUSDT, etc.)")
    direction: DecisionDirection
    lot_size: float
    strategy: str = Field(..., description="Strategy tag (VolBreakout, Pullback, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent confidence score")

    # Decision context
    reasoning: str = Field(..., description="Natural language explanation of WHY")
    market_context: MarketContext
    references: List[str] = Field(
        default_factory=list,
        description="References to past decisions that informed decision"
    )

    # Outcome (filled after decision closes)
    exit_timestamp: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None  # Realized P&L in account currency
    pnl_r: Optional[float] = None  # P&L in R-multiples
    hold_duration: Optional[int] = None  # Minutes held
    exit_reasoning: Optional[str] = None
    slippage: Optional[float] = None  # Entry slippage in pips
    execution_quality: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="0.0 - 1.0 score"
    )

    # Post-decision reflection (filled by ReflectionEngine)
    lessons: Optional[str] = None
    tags: List[str] = Field(default_factory=list, description="Auto-generated pattern tags")
    grade: Optional[DecisionGrade] = None  # Quality of decision, not result

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "T-2026-0001",
            "timestamp": "2026-02-23T10:30:00Z",
            "symbol": "XAUUSD",
            "direction": "long",
            "lot_size": 0.05,
            "strategy": "VolBreakout",
            "confidence": 0.72,
            "reasoning": "London session open with strong momentum above 20-period high",
            "market_context": {
                "price": 2891.50,
                "atr": 28.3,
                "session": "london"
            },
            "references": []
        }
    })


class SessionState(BaseModel):
    """Agent session state for cross-session persistence"""
    agent_id: str
    last_active: datetime
    warm_memory: Dict[str, Any] = Field(
        default_factory=dict,
        description="L2 curated insights and patterns"
    )
    active_positions: List[str] = Field(
        default_factory=list,
        description="List of open decision IDs"
    )
    risk_constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current dynamic risk parameters"
    )


# ========== Adaptive Risk Models ==========

class RiskStatus(str, Enum):
    """Risk management status level"""
    ACTIVE = "active"
    REDUCED = "reduced"
    STOPPED = "stopped"


class RiskConstraints(BaseModel):
    """Dynamic risk parameters calculated from decision history"""
    max_lot_size: float = Field(default=0.1, description="Maximum allowed lot size")
    risk_per_decision_pct: float = Field(default=2.0, ge=0.5, le=5.0, description="Risk per decision as % of score")
    daily_loss_limit: float = Field(default=500.0, description="Maximum daily loss in account currency")
    scale_factor: float = Field(default=1.0, ge=0.0, le=1.0, description="Global position scale factor")
    session_adjustments: Dict[str, float] = Field(
        default_factory=lambda: {"asian": 1.0, "london": 1.0, "newyork": 1.0},
        description="Per-session lot multipliers"
    )
    consecutive_loss_limit: int = Field(default=5, description="Max consecutive losses before stop")
    kelly_fraction: float = Field(default=0.0, ge=0.0, le=0.25, description="Quarter-Kelly fraction")
    status: RiskStatus = Field(default=RiskStatus.ACTIVE)
    reason: str = Field(default="Default constraints - insufficient decision history")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DecisionProposal(BaseModel):
    """A proposed decision to be checked against risk constraints"""
    symbol: str
    direction: DecisionDirection
    lot_size: float = Field(gt=0)
    strategy: str
    confidence: float = Field(ge=0.0, le=1.0)
    session: Optional[str] = None  # asian/london/newyork


class DecisionCheckResult(BaseModel):
    """Result of checking a decision proposal against risk constraints"""
    approved: bool
    adjusted_lot_size: float
    reasons: List[str] = Field(default_factory=list)
    constraints_applied: RiskConstraints
