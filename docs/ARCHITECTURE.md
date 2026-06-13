# Architecture Overview

Internal architecture of DecisionMemory Protocol: module structure, data flow, SQLite schema, and the 3-layer memory model.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    External Data Sources                         │
│   MT5 Terminal    Binance API    Alpaca API    Manual Input      │
└───────┬──────────────┬──────────────┬──────────────┬────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────┐
│  Adapter Layer                                                   │
│  scripts/decision_adapter.py / scripts/mt5_sync.py                  │
│  Converts platform-specific data → standardized DecisionRecord      │
└──────────────────────────┬───────────────────────────────────────┘
                           │ DecisionRecord (Pydantic model)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  DecisionMemory Protocol Server (FastAPI)                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ DecisionJournal │  │ ReflectionEngine │  │  StateManager    │   │
│  │              │  │                  │  │                  │   │
│  │ record_      │  │ generate_daily_  │  │ load_state()     │   │
│  │  decision()  │──│  summary()       │  │ save_state()     │   │
│  │ record_      │  │ _validate_llm_   │  │ update_warm_     │   │
│  │  outcome()   │  │  output()        │  │  memory()        │   │
│  │ query_       │  │ _calculate_      │  │ update_risk_     │   │
│  │  history()   │  │  daily_metrics() │  │  constraints()   │   │
│  └──────┬───────┘  └────────┬─────────┘  └────────┬─────────┘   │
│         │                   │                      │             │
│         ▼                   ▼                      ▼             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              3-Layer Memory Architecture                  │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │   │
│  │  │ L1 (Hot) │  │  L2 (Warm)   │  │    L3 (Cold)      │  │   │
│  │  │ RAM      │  │  JSON in DB  │  │    SQLite          │  │   │
│  │  └──────────┘  └──────────────┘  └───────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────┐                                            │
│  │ MT5Connector     │  Optional: bridges MT5 → DecisionJournal      │
│  │ connect()        │  Guarded import (MT5=None if unavailable)  │
│  │ sync_decisions()    │                                            │
│  └──────────────────┘                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Module Reference

| Module | File | Responsibility |
|--------|------|---------------|
| **Models** | `src/decisionmemory/models.py` | Pydantic schemas: `DecisionRecord`, `Decision ContextContext`, `SessionState`, enums |
| **Database** | `src/decisionmemory/db.py` | SQLite CRUD, schema initialization, JSON serialization |
| **DecisionJournal** | `src/decisionmemory/journal.py` | Decision recording with validation, querying, active decision tracking |
| **StateManager** | `src/decisionmemory/state.py` | Cross-session persistence, warm memory, risk constraints |
| **ReflectionEngine** | `src/decisionmemory/reflection.py` | Daily summary generation, LLM integration, output validation |
| **MT5Connector** | `src/decisionmemory/mt5_connector.py` | MT5 decision sync (guarded import, graceful degradation) |
| **Server** | `src/decisionmemory/server.py` | FastAPI endpoints exposing all modules as HTTP tools |
| **Decision Adapter** | `scripts/decision_adapter.py` | MT5 deal → DecisionRecord conversion (standalone script) |
| **MT5 Sync** | `scripts/mt5_sync.py` | Standalone MT5 polling service (60s interval) |
| **Daily Reflection** | `scripts/daily_reflection.py` | Scheduled reflection runner (cron/Task Scheduler) |
| **Dashboard** | `scripts/research/dashboard.py` | Streamlit monitoring UI |

---

## 3-Layer Memory Architecture

DecisionMemory uses a tiered memory model. Recent events stay in RAM (L1), learned patterns are curated as structured insights (L2), and the full history is archived for deep analysis (L3).

### L1 — Hot Memory (RAM)

| Property | Value |
|----------|-------|
| **Storage** | In-process Python objects |
| **Lifetime** | Current session only |
| **Access speed** | Instant (no I/O) |
| **Contents** | Active positions, current session state, pending decisions |

When an agent calls `state.load`, the StateManager reads from L3 (SQLite) into L1. Changes are flushed back to L3 on `state.save`.

### L2 — Warm Memory (JSON in DB)

| Property | Value |
|----------|-------|
| **Storage** | `warm_memory` field in `session_state` table (JSON) |
| **Lifetime** | Persists across sessions |
| **Access speed** | Single DB read |
| **Contents** | Curated insights, discovered patterns, risk adjustments |

L2 is the agent's learned knowledge. The ReflectionEngine writes here after daily analysis. LLM output is validated before reaching L2 — invalid output triggers a rule-based fallback.

### L3 — Cold Memory (SQLite)

| Property | Value |
|----------|-------|
| **Storage** | SQLite database (`data/decisionmemory.db`) |
| **Lifetime** | Permanent |
| **Access speed** | Standard DB query |
| **Contents** | Every decision record, full history, session state snapshots, strategy adjustments |

Every `record_decision` and `record_outcome` call writes to L3. The ReflectionEngine queries L3 to discover L2 patterns and generate L3 strategy adjustments. Strategy adjustments follow a lifecycle: proposed → approved → applied (or rejected). In production, L3 can be swapped for PostgreSQL without changing the application layer.

### Memory Lifecycle

```
Session Start
    │
    ▼
state.load(agent_id)
    │  Reads from L3 (session_state table)
    │  Populates L1 (RAM) with warm_memory, active_positions, risk_constraints
    ▼
Decision-Making Loop
    │
    ├── record_decision()  →  Write to L3 (decision_records)
    │                          Add to L1 (active_positions)
    │
    ├── record_outcome()   →  Update L3 (decision_records)
    │                          Remove from L1 (active_positions)
    │
    ├── state.save()       →  Flush L1 to L3 (session_state)
    │
    ▼
End of Day (23:55)
    │
    ├── ReflectionEngine reads today's decisions from L3
    ├── Calculates metrics (win rate, avg R, by session/strategy)
    ├── Calls Claude API for pattern analysis (or rule-based fallback)
    ├── Validates LLM output (template check)
    ├── Writes reflection report to L2 (warm_memory via StateManager)
    ▼
Next Session
    │
    └── state.load() picks up updated L2 insights
        Agent decisions informed by accumulated patterns
```

---

## SQLite Schema

### `decision_records` table

```sql
CREATE TABLE decision_records (
    id                TEXT PRIMARY KEY,      -- T-YYYY-NNNN
    timestamp         TEXT NOT NULL,         -- ISO 8601 UTC
    symbol            TEXT NOT NULL,         -- XAUUSD, BTCUSDT, etc.
    direction         TEXT NOT NULL,         -- long / short
    lot_size          REAL NOT NULL,
    strategy          TEXT NOT NULL,
    confidence        REAL NOT NULL,         -- 0.0 - 1.0
    reasoning         TEXT NOT NULL,
    decision context_context    TEXT NOT NULL,         -- JSON object
    decision_references  TEXT NOT NULL,         -- JSON array of decision IDs

    -- Outcome fields (NULL until decision closes)
    exit_timestamp    TEXT,
    exit_price        REAL,
    pnl               REAL,                 -- Account currency
    pnl_r             REAL,                 -- R-multiples
    hold_duration     INTEGER,              -- Minutes
    exit_reasoning    TEXT,
    slippage          REAL,                 -- Pips
    execution_quality REAL,                 -- 0.0 - 1.0

    -- Post-decision reflection
    lessons           TEXT,
    tags              TEXT,                  -- JSON array
    grade             TEXT                   -- A/B/C/D/F
);

CREATE INDEX idx_timestamp ON decision_records(timestamp DESC);
CREATE INDEX idx_strategy ON decision_records(strategy);
```

### `session_state` table

```sql
CREATE TABLE session_state (
    agent_id          TEXT PRIMARY KEY,
    last_active       TEXT NOT NULL,         -- ISO 8601 UTC
    warm_memory       TEXT NOT NULL,         -- JSON object (L2 insights)
    active_positions  TEXT NOT NULL,         -- JSON array of decision IDs
    risk_constraints  TEXT NOT NULL          -- JSON object
);
```

### `strategy_adjustments` table

```sql
CREATE TABLE strategy_adjustments (
    adjustment_id     TEXT PRIMARY KEY,      -- ADJ-{rule}-{seq}
    adjustment_type   TEXT NOT NULL,         -- strategy_disable, strategy_prefer, session_reduce, session_increase, direction_restrict
    parameter         TEXT NOT NULL,         -- e.g. "MeanReversion.enabled", "IM.XAUUSD.max_lot"
    old_value         TEXT NOT NULL,
    new_value         TEXT NOT NULL,
    reason            TEXT NOT NULL,         -- Human-readable explanation with data
    source_pattern_id TEXT,                  -- FK → patterns.pattern_id
    confidence        REAL NOT NULL,         -- Inherited from source pattern
    status            TEXT NOT NULL DEFAULT 'proposed',  -- proposed → approved → applied | rejected
    created_at        TEXT NOT NULL,         -- ISO 8601 UTC
    applied_at        TEXT                   -- Set when status = 'applied'
);

CREATE INDEX idx_adjustments_status ON strategy_adjustments(status);
CREATE INDEX idx_adjustments_type ON strategy_adjustments(adjustment_type);
```

### Storage notes

- Timestamps stored as ISO 8601 text strings, always UTC.
- JSON fields (`decision context_context`, `warm_memory`, etc.) stored as text, deserialized on read.
- `decision_references` is `"[]"` by default (empty JSON array).
- No ORM — the `Database` class uses raw `sqlite3` for transparency.

---

## Data Flow

### Single Decision Lifecycle

```
1. LOAD       Agent calls state.load(agent_id)
              ← Returns: warm_memory, active_positions, risk_constraints

2. DECIDE     Agent calls decision.record_decision(...)
              → Validates confidence (0.0-1.0) and direction (long/short)
              → Writes DecisionRecord to L3

3. MONITOR    Agent tracks open positions via decision.get_active()

4. CLOSE      Agent calls decision.record_outcome(decision_id, ...)
              → Updates DecisionRecord in L3 with exit data

5. REFLECT    ReflectionEngine runs (daily at 23:55 or on demand)
              → Reads today's decisions from L3
              → Calculates metrics (win rate, avg R, session/strategy breakdown)
              → Calls Claude API for pattern analysis (optional)
              → Validates LLM output against template
              → Falls back to rule-based summary if validation fails
              → Writes report to reflections/ directory

6. PERSIST    state.save() flushes current session to L3
              → Next session loads updated patterns via state.load()
```

### MT5 Auto-Sync Flow

```
MT5 Terminal (running EA)
    │
    │  MetaDecision-Maker5 Python API (guarded import)
    ▼
scripts/mt5_sync.py / MT5Connector.sync_decisions()
    │  Polls every 60s for closed positions
    │  Groups MT5 deals by position_id
    │  Extracts entry/exit, calculates P&L
    │  Detects session from timestamp:
    │    00:00-08:00 UTC → asian
    │    08:00-16:00 UTC → london
    │    16:00-24:00 UTC → newyork
    ▼
DecisionJournal
    │  record_decision() + record_outcome() for each position
    ▼
L3 (SQLite)
```

### Daily Reflection Flow

```
scripts/daily_reflection.py (Task Scheduler / cron at 23:55)
    │
    ▼
ReflectionEngine.generate_daily_summary(target_date)
    │
    ├── _get_decisions_for_date()       ← queries L3 by UTC date
    ├── _calculate_daily_metrics()   ← {total, winners, losers, win_rate, avg_r, ...}
    │
    ├── [If ANTHROPIC_API_KEY is set]
    │   ├── _generate_llm_summary()  ← Claude API call (claude-sonnet-4-5)
    │   └── _validate_llm_output()   ← checks template structure
    │       ├── Valid   → use LLM output
    │       └── Invalid → fall back to rule-based
    │
    └── [If no API key or fallback triggered]
        └── _generate_rule_based_summary()
    │
    ▼
Returns markdown string
Saved to reflections/YYYY-MM-DD.md by the caller
```

---

## Design Principles

1. **Platform-agnostic core.** MT5 code is isolated in `scripts/decision_adapter.py`, `scripts/mt5_sync.py`, and `mt5_connector.py`. Core modules (`journal`, `state`, `reflection`) know nothing about providers. Adding a new provider means writing a new adapter.

2. **LLM outputs are validated before L2 storage.** Every LLM response passes through `_validate_llm_output()`. Invalid output triggers a deterministic rule-based fallback. This prevents garbage from entering the agent's learned knowledge.

3. **All timestamps in UTC.** No local timezone handling inside the protocol. Adapters convert to UTC at ingestion.

4. **No ORM.** Direct SQLite with raw SQL via the `Database` class. This keeps the data layer transparent and debuggable.

5. **Graceful degradation.** If MT5 is unavailable, the import is guarded (`MT5 = None`). If the LLM API fails, rule-based reflection runs. If no decisions exist for a day, the system returns "insufficient data" rather than crashing.

---

## See Also

- [SCHEMA.md](SCHEMA.md) — Full data structure reference with JSON examples
- [API.md](API.md) — HTTP endpoint documentation
- [REFLECTION_FORMAT.md](REFLECTION_FORMAT.md) — Reflection report template
