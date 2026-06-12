"""Tests for dashboard API — GET /dashboard/overview."""

import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from decisionmemory.db import Database
from decisionmemory.dashboard_models import OverviewResponse
from decisionmemory.repositories.decision import DecisionRepository
from decisionmemory.services.dashboard import DashboardService


@pytest.fixture
def db(tmp_path):
    """Create a temp SQLite database."""
    return Database(str(tmp_path / "test.db"))


@pytest.fixture
def client(db):
    """TestClient with dashboard_api wired to temp DB."""
    from decisionmemory.server import app
    from decisionmemory.dashboard_api import get_decision_repository

    def override_repo():
        return DecisionRepository(db=db)

    app.dependency_overrides[get_decision_repository] = override_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def _insert_decision(db, decision_id, pnl, strategy="VolBreakout"):
    """Helper to insert a closed decision."""
    conn = db._get_connection()
    try:
        conn.execute(
            """
            INSERT INTO decision_records
            (id, timestamp, symbol, direction, lot_size, strategy,
             confidence, reasoning, market_context, decision_references, pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                "2026-03-01T00:00:00Z",
                "XAUUSD",
                "BUY",
                0.10,
                strategy,
                0.8,
                "test",
                "{}",
                "[]",
                pnl,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_episodic(db, mem_id, confidence=0.7):
    """Helper to insert an episodic memory."""
    conn = db._get_connection()
    try:
        conn.execute(
            """
            INSERT INTO episodic_memory
            (id, timestamp, context_json, strategy, direction, entry_price, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (mem_id, "2026-03-01T00:00:00Z", "{}", "VB", "BUY", 5000.0, confidence, "2026-03-01T00:00:00Z"),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_affective(db, current_score=10000.0, peak_score=11000.0, drawdown=0.09):
    """Helper to insert affective state."""
    conn = db._get_connection()
    try:
        conn.execute(
            """
            INSERT INTO affective_state
            (id, peak_score, current_score, drawdown_state, last_updated)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("default", peak_score, current_score, drawdown, "2026-03-01T00:00:00Z"),
        )
        conn.commit()
    finally:
        conn.close()


class TestOverviewEndpoint:
    """Tests for GET /dashboard/overview."""

    def test_overview_empty_db(self, client):
        """Empty database returns zeros — not an error."""
        resp = client.get("/dashboard/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_decisions"] == 0
        assert data["total_pnl"] == 0.0
        assert data["win_rate"] == 0.0
        assert data["profit_factor"] == 0.0
        assert data["memory_count"] == 0
        assert data["strategies"] == []

    def test_overview_with_decisions(self, client, db):
        """Overview computes correct win_rate and profit_factor."""
        _insert_decision(db, "t1", pnl=100.0, strategy="VolBreakout")
        _insert_decision(db, "t2", pnl=50.0, strategy="VolBreakout")
        _insert_decision(db, "t3", pnl=-30.0, strategy="IntradayMomentum")

        resp = client.get("/dashboard/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_decisions"] == 3
        assert data["total_pnl"] == 120.0
        # 2 wins / 3 total
        assert data["win_rate"] == pytest.approx(2 / 3, abs=0.001)
        # gross_profit=150 / gross_loss=30
        assert data["profit_factor"] == pytest.approx(5.0, abs=0.01)
        assert "VolBreakout" in data["strategies"]
        assert "IntradayMomentum" in data["strategies"]

    def test_overview_with_memory(self, client, db):
        """Memory count and avg confidence are returned."""
        _insert_episodic(db, "m1", confidence=0.8)
        _insert_episodic(db, "m2", confidence=0.6)

        resp = client.get("/dashboard/overview")
        data = resp.json()
        assert data["memory_count"] == 2
        assert data["avg_confidence"] == pytest.approx(0.7, abs=0.01)

    def test_overview_with_score(self, client, db):
        """Score and drawdown from affective_state."""
        _insert_affective(db, current_score=10000.0, peak_score=11000.0, drawdown=0.09)

        resp = client.get("/dashboard/overview")
        data = resp.json()
        assert data["current_score"] == 10000.0
        assert data["max_drawdown_pct"] == 9.0

    def test_overview_response_schema(self, client):
        """Response matches OverviewResponse Pydantic model."""
        resp = client.get("/dashboard/overview")
        assert resp.status_code == 200
        # Validate against Pydantic model — raises if invalid
        OverviewResponse(**resp.json())


class TestCORSHeaders:
    """Tests for CORS middleware."""

    def test_cors_preflight(self, client):
        """OPTIONS request returns CORS headers for allowed origin."""
        resp = client.options(
            "/dashboard/overview",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_on_get(self, client):
        """GET request includes CORS headers for allowed origin."""
        resp = client.get(
            "/dashboard/overview",
            headers={"Origin": "http://localhost:5173"},
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


class TestServiceUnit:
    """Unit tests for DashboardService (no HTTP)."""

    def test_profit_factor_all_wins(self, db):
        """All winning decisions → profit_factor = inf."""
        _insert_decision(db, "t1", pnl=100.0)
        _insert_decision(db, "t2", pnl=50.0)

        repo = DecisionRepository(db=db)
        service = DashboardService(repo=repo)
        result = service.get_overview()
        assert result["profit_factor"] == float("inf")

    def test_no_closed_decisions(self, db):
        """Decisions with pnl=NULL are not counted."""
        conn = db._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO decision_records
                (id, timestamp, symbol, direction, lot_size, strategy,
                 confidence, reasoning, market_context, decision_references)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("open1", "2026-03-01T00:00:00Z", "XAUUSD", "BUY", 0.10,
                 "VB", 0.8, "test", "{}", "[]"),
            )
            conn.commit()
        finally:
            conn.close()

        repo = DecisionRepository(db=db)
        service = DashboardService(repo=repo)
        result = service.get_overview()
        assert result["total_decisions"] == 0
        assert result["total_pnl"] == 0.0
