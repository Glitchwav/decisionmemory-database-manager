"""
Pydantic response models for dashboard API.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel


class OverviewResponse(BaseModel):
    """Response model for GET /dashboard/overview."""

    total_decisions: int
    total_pnl: float
    win_rate: float
    profit_factor: float
    current_score: float
    max_drawdown_pct: float
    memory_count: int
    avg_confidence: float
    last_decision_date: Optional[str] = None
    strategies: List[str] = []


class ScorePoint(BaseModel):
    """Single point on the score curve."""

    date: str
    cumulative_pnl: float
    drawdown_pct: float
    decision_count: int


class RollingMetricPoint(BaseModel):
    """Single point of rolling performance metrics."""

    date: str
    rolling_pf: float
    rolling_wr: float
    rolling_avg_r: float
    window_size: int


class MemoryGrowthPoint(BaseModel):
    """Single day of memory growth by regime."""

    date: str
    total_memories: int
    trending_up: int
    trending_down: int
    ranging: int
    volatile: int
    unknown: int


class OWMScorePoint(BaseModel):
    """Single day of OWM recall score trend."""

    date: str
    avg_total: float
    avg_q: float
    avg_sim: float
    avg_rec: float
    avg_conf: float
    avg_aff: float
    query_count: int


class CalibrationPoint(BaseModel):
    """Single decision's entry confidence vs actual outcome."""

    decision_id: str
    entry_confidence: float
    actual_pnl_r: float
    strategy: str


class StrategyDetailResponse(BaseModel):
    """Detailed strategy performance response."""

    name: str
    total_decisions: int
    win_rate: float
    profit_factor: float
    avg_pnl_r: float
    avg_hold_seconds: int
    best_session: str
    worst_session: str
    baseline_pf: float
    baseline_wr: float
    decisions: List[Dict]
    session_heatmap: List[Dict]


class ReflectionSummary(BaseModel):
    """Summary of a daily review markdown file."""

    date: str
    type: str
    grade: Optional[str] = None
    strategy: Optional[str] = None
    summary: str
    full_path: str


class AdjustmentEvent(BaseModel):
    """A strategy adjustment from L3 layer."""

    id: str
    timestamp: str
    adjustment_type: str
    parameter: str
    old_value: str
    new_value: str
    reason: str
    status: str
    strategy: Optional[str] = None


class BeliefState(BaseModel):
    """A Bayesian belief from semantic memory."""

    id: str
    proposition: str
    alpha: float
    beta: float
    confidence: float
    strategy: Optional[str] = None
    regime: Optional[str] = None
    sample_size: int
    trend: str


class DreamSession(BaseModel):
    """A decision dreaming simulation session."""

    id: str
    timestamp: str
    condition: str
    decisions: int
    pf: float
    pnl: float
    wr: float
    has_memory: bool
    memory_type: Optional[str] = None
    resonance_detected: bool
