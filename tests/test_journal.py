"""
Unit tests for DecisionJournal module.
"""

import pytest
import tempfile
from pathlib import Path

from decisionmemory.journal import DecisionJournal
from decisionmemory.db import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        yield db


@pytest.fixture
def journal(temp_db):
    """Create a DecisionJournal with temp database"""
    return DecisionJournal(db=temp_db)


def test_record_decision(journal):
    """Test recording a decision decision"""
    decision = journal.record_decision(
        decision_id="T-2026-TEST-001",
        symbol="XAUUSD",
        direction="long",
        lot_size=0.05,
        strategy="VolBreakout",
        confidence=0.72,
        reasoning="London session breakout",
        market_context={
            "price": 2891.50,
            "atr": 28.3,
            "session": "london"
        }
    )
    
    assert decision.id == "T-2026-TEST-001"
    assert decision.symbol == "XAUUSD"
    assert decision.confidence == 0.72
    assert decision.exit_timestamp is None


def test_record_outcome(journal):
    """Test recording decision outcome"""
    # First create a decision
    journal.record_decision(
        decision_id="T-2026-TEST-002",
        symbol="XAUUSD",
        direction="long",
        lot_size=0.05,
        strategy="Pullback",
        confidence=0.85,
        reasoning="Test",
        market_context={"price": 2900.00}
    )
    
    # Record outcome
    success = journal.record_outcome(
        decision_id="T-2026-TEST-002",
        exit_price=2905.00,
        pnl=25.00,
        exit_reasoning="Hit 2R target",
        pnl_r=2.0,
        lessons="Good entry"
    )
    
    assert success is True
    
    # Verify outcome was saved
    decision = journal.get_decision("T-2026-TEST-002")
    assert decision.exit_price == 2905.00
    assert decision.pnl == 25.00
    assert decision.pnl_r == 2.0
    assert decision.lessons == "Good entry"


def test_get_decision(journal):
    """Test retrieving a decision by ID"""
    journal.record_decision(
        decision_id="T-2026-TEST-003",
        symbol="XAUUSD",
        direction="short",
        lot_size=0.1,
        strategy="Momentum",
        confidence=0.65,
        reasoning="Test",
        market_context={"price": 2895.00}
    )
    
    decision = journal.get_decision("T-2026-TEST-003")
    
    assert decision is not None
    assert decision.id == "T-2026-TEST-003"
    assert decision.strategy == "Momentum"
    assert decision.direction == "short"


def test_query_history(journal):
    """Test querying decision history"""
    # Create multiple decisions
    for i in range(5):
        journal.record_decision(
            decision_id=f"T-2026-TEST-{i:03d}",
            symbol="XAUUSD",
            direction="long",
            lot_size=0.05,
            strategy="VolBreakout" if i % 2 == 0 else "Pullback",
            confidence=0.7,
            reasoning=f"Test {i}",
            market_context={"price": 2890.00 + i}
        )
    
    # Query all
    all_decisions = journal.query_history(limit=10)
    assert len(all_decisions) == 5
    
    # Query by strategy
    breakout_decisions = journal.query_history(strategy="VolBreakout", limit=10)
    assert len(breakout_decisions) == 3  # 0, 2, 4
    
    pullback_decisions = journal.query_history(strategy="Pullback", limit=10)
    assert len(pullback_decisions) == 2  # 1, 3


def test_get_active_decisions(journal):
    """Test retrieving active (open) decisions"""
    # Create 3 decisions, close 1
    for i in range(3):
        journal.record_decision(
            decision_id=f"T-2026-ACTIVE-{i:03d}",
            symbol="XAUUSD",
            direction="long",
            lot_size=0.05,
            strategy="Test",
            confidence=0.7,
            reasoning="Test",
            market_context={"price": 2890.00}
        )
    
    # Close the first one
    journal.record_outcome(
        decision_id="T-2026-ACTIVE-000",
        exit_price=2895.00,
        pnl=25.00,
        exit_reasoning="Test close"
    )
    
    # Get active decisions
    active = journal.get_active_decisions()
    
    assert len(active) == 2
    assert all(t.exit_timestamp is None for t in active)
    assert "T-2026-ACTIVE-000" not in [t.id for t in active]


def test_invalid_confidence(journal):
    """Test validation of confidence score"""
    with pytest.raises(ValueError):
        journal.record_decision(
            decision_id="T-2026-INVALID-001",
            symbol="XAUUSD",
            direction="long",
            lot_size=0.05,
            strategy="Test",
            confidence=1.5,  # Invalid
            reasoning="Test",
            market_context={"price": 2890.00}
        )


def test_invalid_direction(journal):
    """Test validation of direction"""
    with pytest.raises(ValueError):
        journal.record_decision(
            decision_id="T-2026-INVALID-002",
            symbol="XAUUSD",
            direction="sideways",  # Invalid
            lot_size=0.05,
            strategy="Test",
            confidence=0.7,
            reasoning="Test",
            market_context={"price": 2890.00}
        )
