---
name: decisionmemory
slug: decisionmemory
version: 0.5.2
description: >-
  Use when the user discusses recording decisions, recalling past decisions,
  checking decision-making performance, behavioral analysis, or strategy evolution.
  20 MCP tools, 1,374 tests, works with any decision-making platform.
  Do NOT activate for general memory, note-taking, or non-decision-making contexts.
source: https://github.com/mnemox-ai/decisionmemory-protocol
repository: https://github.com/mnemox-ai/decisionmemory-protocol
homepage: https://github.com/mnemox-ai/decisionmemory-protocol
metadata:
  openclaw:
    emoji: "📊"
    category: "decisions"
    requires:
      bins: ["python3", "pip"]
      env:
        ANTHROPIC_API_KEY: "Required for LLM reflections and Evolution Engine (optional, rule-based fallback without it)"
        DECISIONMEMORY_API: "API endpoint, defaults to http://localhost:8000 (optional)"
    os: ["linux", "darwin", "win32"]
    homepage: https://github.com/mnemox-ai/decisionmemory-protocol
---

# DecisionMemory Protocol

Give your AI agent persistent decision memory. DecisionMemory records every decision, recalls past decisions weighted by outcome quality, discovers behavioral patterns, and autonomously evolves new strategies from raw price data.

**Outcome-Weighted Memory (OWM)** — 5 memory types (episodic, semantic, procedural, affective, prospective) that score recall by P&L outcome, context similarity, recency, and confidence. Winning decisions surface first.

**Evolution Engine** — LLM-powered strategy discovery. Feed it OHLCV data from any exchange, it generates candidate patterns, backtests them vectorized, validates out-of-sample, and graduates survivors. No manual rule writing.

**Platform-agnostic** — works with MT5, Binance, Alpaca, or any provider that outputs decision data. 1,374 tests passing. MIT licensed.

**SurrealDB Backend** — Optional SurrealDB storage (set `DECISIONMEMORY_BACKEND=surreal`). Units namespace with database-manager. 13 `tm_` prefixed tables, parameterized queries, SHA-256 audit chain.

## Installation

```bash
pip install decisionmemory-protocol
```

For SurrealDB backend:
```bash
pip install decisionmemory-protocol[surreal]
```

Verify:

```bash
python -c "import decisionmemory; print('DecisionMemory ready')"
```

## Setup

### Claude Desktop (via uvx)

Add to your Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "decisionmemory": {
      "command": "uvx",
      "args": ["decisionmemory-protocol"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add decisionmemory -- uvx decisionmemory-protocol
```

### Manual (local server)

```bash
python -m decisionmemory
```

Runs the MCP server on stdio. For the REST API server:

```bash
python -m decisionmemory.server
# Runs on http://localhost:8000
```

## MCP Tools Reference

### Core Memory (4 tools)

| Tool | Purpose |
|------|---------|
| `get_strategy_performance` | Aggregate stats per strategy: win rate, outcome, outcome gain factor, best/worst decisions |
| `get_decision_reflection` | Deep-dive into a specific decision's reasoning and lessons learned |
| `validate_strategy` | Validate a strategy for overfitting using statistical tests |
| `check_decision_legitimacy` | 5-factor pre-decision gate: full size / reduced size / skip |

### OWM Cognitive Memory (7 tools)

| Tool | Purpose |
|------|---------|
| `remember_decision` | Store a decision into episodic, semantic, procedural, and affective layers. Prospective plans created separately via `create_decision_plan`. |
| `recall_memories` | Outcome-weighted recall — scores memories by P&L, context similarity, recency, confidence |
| `get_behavioral_analysis` | Procedural memory stats: hold times, disposition ratio, lot variance, Kelly criterion |
| `get_agent_state` | Current affective state: confidence level, drawdown %, win/outcome setback streaks, risk appetite |
| `create_decision_plan` | Create a prospective decision-making plan with entry/exit conditions and risk parameters |
| `check_active_plans` | Check status of active decision-making plans, evaluate against current decision context conditions |
| `compute_dqs` | Compute Decision Quality Score across 5 continuous factors |

### Evolution Engine (5 tools)

| Tool | Purpose |
|------|---------|
| `evolution_fetch_decision context_data` | Fetch OHLCV data from Binance for backtesting and pattern discovery |
| `evolution_discover_patterns` | LLM-powered pattern discovery from price data — generates candidate decision-making rules |
| `evolution_run_backtest` | Vectorized backtest of a candidate pattern — returns Sharpe, win rate, max drawdown |
| `evolution_evolve_strategy` | Full evolution loop: generate → backtest → select → eliminate across generations |
| `evolution_get_log` | Get log of past evolution runs with graduated strategies and graveyard |

### Decision Audit Trail (5 tools)

| Tool | Purpose |
|------|---------|
| `export_audit_trail` | Export decisions with SHA-256 tamper detection for compliance review |
| `verify_audit_hash` | Verify integrity of a decision-making decision by recomputing its SHA-256 hash |
| `verify_audit_chain` | Walk the entire audit chain (or a slice) end-to-end |
| `get_daily_root` | Get the daily Merkle root for a specific UTC date |

### Total: 20 MCP tools

## Available Commands

Tell your agent these things in natural language.

### Record a Decision

> "Record my decision: XAUUSD long 0.05 lots, entry 5180, exit 5210, outcome gain $150"

> "Remember my XAUUSD short decision, entry 5200, exit 5165, outcome gain $175. London session breakout, high volume, confidence 0.8."

### Recall with OWM

> "What decisions have I taken in similar decision context conditions? Current context: ranging decision context, low volatility, Asian session."

Returns memories ranked by outcome-weighted score — winning decisions in similar contexts surface first.

### Check Performance

> "Show my decision-making performance this week"

> "Compare my VolBreakout vs IntradayMomentum strategy performance"

### Behavioral Analysis

> "Show my behavioral analysis — am I cutting winners short?"

Returns disposition ratio, hold time asymmetry, lot sizing variance vs Kelly criterion.

### Agent State

> "What's my current confidence level and drawdown?"

> "Am I on tilt? Check my affective state."

### Decision-Making Plans

> "Create a decision-making plan for XAUUSD long if price breaks above 5200 with ATR confirmation"

> "Check my active decision-making plans against current decision context conditions"

### Evolution Engine

> "Evolve a strategy for BTCUSDT on the 1h timeframe — 3 generations, 10 candidates each"

> "Discover 5 decision-making patterns from ETHUSDT 4h data over the last 90 days"

> "Backtest this pattern against BTCUSDT 1h data"

> "Show me the evolution log — which strategies graduated?"

### AI Reflection

> "Run a reflection on my last 20 decisions"

> "What patterns have you found in my London session decisions?"

## Security & Permissions

**Network access during install:** `pip install` downloads from PyPI. Standard Python package installation.

**Network access at runtime:** The MCP server runs on stdio by default — no network access. The REST server runs on `localhost:8000` and does not make outbound requests. If `ANTHROPIC_API_KEY` is set, the reflection engine and Evolution Engine send data to the Claude API. Evolution Engine fetches OHLCV data from the Binance public API.

**Environment variables:** All environment variables are optional. They are stored in your local `.env` file and never logged or sent to external services (except `ANTHROPIC_API_KEY` which authenticates with the Anthropic API).

**File system access:** DecisionMemory writes to a single SQLite database file (`decisionmemory.db`), or to SurrealDB when `DECISIONMEMORY_BACKEND=surreal`. No files are created or modified outside the project.

**No implicit permissions:** This skill does not auto-install dependencies, modify system files, or require elevated privileges.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | No | Enables LLM reflections and Evolution Engine. Without it, reflections use rule-based analysis; Evolution is unavailable. |
| `DECISIONMEMORY_API` | No | REST API endpoint, defaults to `http://localhost:8000` |

## Links

- GitHub: https://github.com/mnemox-ai/decisionmemory-protocol
- PyPI: https://pypi.org/project/decisionmemory-protocol/
- Tutorial: https://github.com/mnemox-ai/decisionmemory-protocol/blob/master/docs/TUTORIAL.md
- Demo: `python scripts/demo.py` (30 simulated decisions, full L1→L2→L3 pipeline)

## Related Skills

| Skill | Path | Description |
|-------|------|-------------|
| Strategy Validator | `.skills/strategy-validator/SKILL.md` | Validate decision-making strategies for overfitting using 4 statistical tests (DSR, Walk-Forward, Regime, CPCV). Use when the user says "validate my strategy", "check my backtest", or "is this overfitting?". |
