"""
DecisionMemory Hosted API Server (MVP).

Multi-tenant FastAPI server with API key authentication and SQLite storage.
Implements core endpoints from docs/hosted-api-spec.md:
  - POST /api/v1/decisions       (store_decision)
  - GET  /api/v1/decisions       (recall_decisions)
  - GET  /api/v1/performance  (get_performance)
  - GET  /api/v1/health       (no auth)

API keys: Bearer tm_live_* / tm_test_*
Storage: SQLite (PostgreSQL migration planned)
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from decisionmemory.mcp_server import mcp

# ========== Configuration ==========

DB_PATH = os.environ.get("TM_HOSTED_DB", "hosted/hosted.db")

# MCP Streamable HTTP sub-app
mcp_http = mcp.http_app(path="/mcp", transport="streamable-http", stateless_http=True)

app = FastAPI(
    title="DecisionMemory Hosted API",
    description="Multi-tenant AI DecisionMaking Memory API",
    version="0.5.0",
    lifespan=mcp_http.lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mnemox.ai",
        "https://mnemox-ai.github.io",
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ========== Database ==========


class HostedDB:
    """SQLite storage for hosted API. Scoped by account_id."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        conn = self._conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'free',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_account
                ON api_keys(account_id)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    strategy TEXT NOT NULL,
                    market_context TEXT NOT NULL,
                    exit_price REAL,
                    pnl REAL,
                    reflection TEXT,
                    PRIMARY KEY (id, account_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_account
                ON decisions(account_id, timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_strategy
                ON decisions(account_id, strategy)
            """)

            # Seed API keys from env if provided (comma-separated key:account:plan)
            seed = os.environ.get("TM_API_KEYS", "")
            if seed:
                for entry in seed.split(","):
                    entry = entry.strip()
                    if not entry:
                        continue
                    parts = entry.split(":")
                    key = parts[0]
                    account_id = parts[1] if len(parts) > 1 else "default"
                    plan = parts[2] if len(parts) > 2 else "free"
                    conn.execute(
                        "INSERT OR IGNORE INTO api_keys VALUES (?, ?, ?, ?)",
                        (key, account_id, plan, datetime.now(timezone.utc).isoformat()),
                    )
                conn.commit()

            # Subscribers table (no-auth, waitlist)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    email TEXT PRIMARY KEY,
                    source TEXT NOT NULL DEFAULT 'waitlist',
                    created_at TEXT NOT NULL
                )
            """)

            conn.commit()
        finally:
            conn.close()

    def save_subscriber(self, email: str, source: str = "waitlist") -> bool:
        """Save waitlist subscriber. Returns True if new, False if already exists."""
        import logging
        conn = self._conn()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO subscribers (email, source, created_at) VALUES (?, ?, ?)",
                (email.lower().strip(), source, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            inserted = conn.execute("SELECT changes()").fetchone()[0]
            if inserted:
                logging.getLogger(__name__).info(f"[SUBSCRIBE] {email} source={source}")
            return bool(inserted)
        finally:
            conn.close()

    def get_subscriber_count(self) -> int:
        conn = self._conn()
        try:
            return conn.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
        finally:
            conn.close()

    def validate_key(self, api_key: str) -> Optional[Dict[str, str]]:
        """Validate API key, return account info or None."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE key = ?", (api_key,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def insert_decision(self, account_id: str, decision: Dict[str, Any]) -> bool:
        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO decisions
                   (id, account_id, timestamp, symbol, direction, entry_price,
                    strategy, market_context, exit_price, pnl, reflection)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    decision["id"],
                    account_id,
                    decision["timestamp"],
                    decision["symbol"],
                    decision["direction"],
                    decision["entry_price"],
                    decision["strategy"],
                    decision["market_context"],
                    decision.get("exit_price"),
                    decision.get("pnl"),
                    decision.get("reflection"),
                ),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail={"error": "conflict", "message": f"Decision '{decision['id']}' already exists"},
            )
        finally:
            conn.close()

    def query_decisions(
        self,
        account_id: str,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Query decisions for an account. Returns (decisions, total_count)."""
        conn = self._conn()
        try:
            where = "WHERE account_id = ?"
            params: list[Any] = [account_id]

            if symbol:
                where += " AND symbol = ?"
                params.append(symbol.upper())
            if strategy:
                where += " AND strategy = ?"
                params.append(strategy)

            total = conn.execute(
                f"SELECT COUNT(*) FROM decisions {where}", params
            ).fetchone()[0]

            rows = conn.execute(
                f"SELECT * FROM decisions {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()

            decisions = []
            for row in rows:
                t = dict(row)
                del t["account_id"]
                decisions.append(t)

            return decisions, total
        finally:
            conn.close()

    def get_performance(
        self,
        account_id: str,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Aggregate performance stats for closed decisions (pnl IS NOT NULL)."""
        conn = self._conn()
        try:
            where = "WHERE account_id = ? AND pnl IS NOT NULL"
            params: list[Any] = [account_id]

            if symbol:
                where += " AND symbol = ?"
                params.append(symbol.upper())
            if strategy:
                where += " AND strategy = ?"
                params.append(strategy)

            rows = conn.execute(
                f"SELECT * FROM decisions {where} ORDER BY timestamp DESC",
                params,
            ).fetchall()

            closed = [dict(r) for r in rows]
            if not closed:
                return {
                    "symbol": symbol or "all",
                    "total_closed_decisions": 0,
                    "strategies": {},
                }

            by_strat: Dict[str, list] = {}
            for t in closed:
                by_strat.setdefault(t["strategy"], []).append(t)

            strategies = {}
            for strat, decisions in by_strat.items():
                pnls = [t["pnl"] for t in decisions]
                winners = [p for p in pnls if p > 0]
                losers = [p for p in pnls if p <= 0]
                total_pnl = sum(pnls)

                best = max(decisions, key=lambda t: t["pnl"])
                worst = min(decisions, key=lambda t: t["pnl"])

                strategies[strat] = {
                    "decision_count": len(decisions),
                    "win_rate": round(len(winners) / len(decisions) * 100, 1),
                    "total_pnl": round(total_pnl, 2),
                    "avg_pnl": round(total_pnl / len(decisions), 2),
                    "avg_winner": round(sum(winners) / len(winners), 2) if winners else 0,
                    "avg_loser": round(sum(losers) / len(losers), 2) if losers else 0,
                    "profit_factor": (
                        round(sum(winners) / abs(sum(losers)), 2)
                        if losers and sum(losers) != 0
                        else float("inf")
                    ),
                    "best_decision": {"id": best["id"], "pnl": best["pnl"]},
                    "worst_decision": {"id": worst["id"], "pnl": worst["pnl"]},
                }

            return {
                "symbol": symbol or "all",
                "total_closed_decisions": len(closed),
                "strategies": strategies,
            }
        finally:
            conn.close()

    def create_api_key(self, account_id: str, plan: str = "free") -> str:
        """Create a new API key for an account."""
        key = f"tm_live_{uuid.uuid4().hex}"
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO api_keys VALUES (?, ?, ?, ?)",
                (key, account_id, plan, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            return key
        finally:
            conn.close()


# Singleton DB — initialized on first use
_db: Optional[HostedDB] = None


def get_db() -> HostedDB:
    global _db
    if _db is None:
        _db = HostedDB(DB_PATH)
    return _db


# ========== Auth Dependency ==========


def require_auth(
    authorization: Optional[str] = Header(None),
    db: HostedDB = Depends(get_db),
) -> Dict[str, str]:
    """Validate Bearer token and return account info."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "Missing Authorization header"},
        )

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "Invalid Authorization format. Use: Bearer <api_key>"},
        )

    api_key = parts[1].strip()
    if not api_key.startswith(("tm_live_", "tm_test_")):
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "Invalid API key format"},
        )

    account = db.validate_key(api_key)
    if not account:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "Invalid API key"},
        )

    return account


# ========== Request/Response Models ==========


class StoreDecisionRequest(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    strategy_name: str
    market_context: str
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    reflection: Optional[str] = None
    decision_id: Optional[str] = None
    timestamp: Optional[str] = None


class StoreDecisionResponse(BaseModel):
    memory_id: str
    symbol: str
    direction: str
    strategy: str
    stored_at: str
    has_outcome: bool
    status: str = "stored"
    credits_used: int = 1


class RecallDecisionsResponse(BaseModel):
    decisions: List[Dict[str, Any]]
    count: int
    total: int
    limit: int
    offset: int


# ========== Endpoints ==========


@app.get("/api/v1/health")
async def health():
    """Health check — no auth required."""
    return {"status": "healthy", "version": "0.5.0"}


@app.post("/api/v1/decisions", status_code=201, response_model=StoreDecisionResponse)
async def store_decision(
    req: StoreDecisionRequest,
    account: Dict = Depends(require_auth),
    db: HostedDB = Depends(get_db),
):
    """Store a decision decision with full context."""
    direction = req.direction.lower()
    if direction not in ("long", "short"):
        raise HTTPException(
            status_code=422,
            detail={"error": "validation_error", "message": "direction must be 'long' or 'short'"},
        )

    decision_id = req.decision_id or f"tm-{uuid.uuid4().hex[:12]}"
    ts = req.timestamp or datetime.now(timezone.utc).isoformat()

    decision_data = {
        "id": decision_id,
        "timestamp": ts,
        "symbol": req.symbol.upper(),
        "direction": direction,
        "entry_price": req.entry_price,
        "strategy": req.strategy_name,
        "market_context": req.market_context,
        "exit_price": req.exit_price,
        "pnl": req.pnl,
        "reflection": req.reflection,
    }

    db.insert_decision(account["account_id"], decision_data)

    return StoreDecisionResponse(
        memory_id=decision_id,
        symbol=req.symbol.upper(),
        direction=direction,
        strategy=req.strategy_name,
        stored_at=ts,
        has_outcome=req.exit_price is not None,
    )


@app.get("/api/v1/decisions")
async def recall_decisions(
    symbol: Optional[str] = Query(None),
    strategy: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    account: Dict = Depends(require_auth),
    db: HostedDB = Depends(get_db),
):
    """Query past decisions with filters."""
    decisions, total = db.query_decisions(
        account_id=account["account_id"],
        symbol=symbol,
        strategy=strategy,
        limit=limit,
        offset=offset,
    )
    return {
        "decisions": decisions,
        "count": len(decisions),
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/performance")
async def get_performance(
    symbol: Optional[str] = Query(None),
    strategy: Optional[str] = Query(None),
    account: Dict = Depends(require_auth),
    db: HostedDB = Depends(get_db),
):
    """Aggregate performance stats per strategy."""
    return db.get_performance(
        account_id=account["account_id"],
        symbol=symbol,
        strategy=strategy,
    )


# ========== Waitlist / Subscribe (no auth) ==========


class SubscribeRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    source: str = Field(default="waitlist", max_length=64)


@app.post("/api/subscribe", status_code=201)
async def subscribe(req: SubscribeRequest, db: HostedDB = Depends(get_db)):
    """Add email to waitlist. No auth required."""
    import re
    if not re.match(r"[^@]+@[^@]+\.[^@]+", req.email):
        raise HTTPException(status_code=422, detail={"error": "invalid_email"})
    is_new = db.save_subscriber(req.email, req.source)
    return {"status": "subscribed", "new": is_new}


@app.get("/api/subscribers/count")
async def subscriber_count(db: HostedDB = Depends(get_db)):
    """Public subscriber count."""
    return {"count": db.get_subscriber_count()}


# ========== MCP Streamable HTTP ==========


app.mount("/", mcp_http)


# ========== Entry Point ==========


def main():
    """Run hosted API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
