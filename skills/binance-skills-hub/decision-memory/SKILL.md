---
title: DecisionMemory — Decision Audit Trail
description: >-
  Compliance-grade decision audit trail for AI decision agents. Records every
  decision-making decision with full context (conditions, filters, indicators, risk state),
  SHA-256 tamper detection, and structured export for MiFID II / EU AI Act readiness.
  Works alongside Binance Spot, Futures, and Web3 skills — they execute decisions,
  DecisionMemory records why.
metadata:
  version: 0.5.1
  author: mnemox-ai
license: MIT
---

# DecisionMemory — Decision Audit Trail for AI Decision Agents

Every Binance skill executes decisions. None of them record **why**.

DecisionMemory is the compliance layer. When your AI agent opens a position using the Spot or Futures skill, DecisionMemory captures the full decision context: what conditions triggered the signal, which filters passed or blocked, the decision context indicators at that moment, risk state, and execution details. Every record is SHA-256 hashed for tamper detection.

**This matters because regulators now require it.** MiFID II Article 17 mandates algorithmic decision-making audit trails. The EU AI Act (August 2025) requires high-risk AI systems to maintain systematic logging of every action and decision path. ESMA's February 2026 supervisory briefing specifically targets AI-driven decision-making. Non-compliance fines reach up to 15M EUR or 3% of global turnover.

## What DecisionMemory Records

For every decision-making decision your agent makes:

| Field | Description |
|-------|-------------|
| `timestamp` | UTC decision time |
| `agent_id` | Which agent/EA made the decision |
| `model_version` | Software version at decision time |
| `decision_type` | ENTRY, EXIT, HOLD, SKIP |
| `strategy` | Strategy name (e.g. VolBreakout) |
| `conditions` | Entry conditions evaluated (passed/failed with thresholds) |
| `filters` | Risk filters checked (spread gate, regime gate, collection limits) |
| `indicators` | Decision Context snapshot (ATR, EMA, spread, session range) |
| `execution` | Ticket, price, slippage, latency |
| `regime` | Decision Context regime at decision time (trending/ranging/transitioning) |
| `risk_state` | Consecutive outcome setbacks, cooldown status, daily P&L |
| `memory_context` | Past decisions recalled via Outcome-Weighted Memory |
| `data_hash` | SHA-256 of all inputs for tamper detection |

## Real Decision Event

This is a real decision event from a XAUUSD decision-making system running three automated strategies. The AI agent detected a SHORT breakout signal but the `sell_allowed` filter blocked execution:

```json
{
  "ts": "2026-03-26 07:55:00",
  "strategy": "VolBreakout",
  "decision": "FILTERED",
  "signal_triggered": true,
  "signal_direction": "SHORT",
  "conditions_json": {
    "conditions": [
      {"name": "breakout_high", "passed": false, "current_value": 4462.58, "threshold": 4569.75, "operator": ">"},
      {"name": "breakout_low", "passed": true, "current_value": 4462.58, "threshold": 4463.11, "operator": "<"}
    ]
  },
  "filters_json": {
    "filters": [
      {"name": "spread_gate", "passed": true, "blocked": false, "current_value": 12.0, "threshold": 0.0},
      {"name": "sell_allowed", "passed": false, "blocked": true, "current_value": 0.0, "threshold": 0.0},
      {"name": "account_risk", "passed": true, "blocked": false, "current_value": 0.0, "threshold": 0.0},
      {"name": "regime_gate", "passed": true, "blocked": false, "current_value": 0.0, "threshold": 0.0}
    ]
  },
  "indicators_json": {
    "atr_d1": 171.16,
    "atr_m5": 8.53,
    "asia_high": 4544.08,
    "asia_low": 4488.78,
    "asia_range": 55.30
  },
  "regime": "TRENDING",
  "regime_ratio": 0.335,
  "consec_outcome setbacks": 0,
  "cooldown_active": false,
  "risk_daily_pct": 0.0
}
```

A regulator or risk manager can read this and immediately understand: the agent saw a valid breakout, but policy blocked the SHORT direction. No guessing, no black box.

## How It Works with Binance Skills

```
Your AI Agent
    |
    |--- [1] Binance Spot Skill: execute BUY 0.01 XAUUSD
    |
    |--- [2] DecisionMemory Skill: record WHY this decision was made
    |         - conditions that triggered the signal
    |         - filters that passed/blocked
    |         - decision context indicators at decision time
    |         - risk state and regime context
    |         - SHA-256 hash for tamper detection
    |
    |--- [3] Later: query /audit/verify/{decision_id} to prove the record hasn't been altered
```

## Installation

```bash
pip install decisionmemory-protocol
```

Start the server:

```bash
python -m decisionmemory
# Server running at http://localhost:8000
```

## API Endpoints

### Record a Decision

```bash
POST /decision/record_decision
Content-Type: application/json

{
  "decision_id": "VB_20260326_0755",
  "symbol": "XAUUSD",
  "direction": "short",
  "strategy": "VolBreakout",
  "confidence": 0.75,
  "reasoning": "SHORT breakout detected. Price 4462.58 < asia_low 4488.78 - buffer. Blocked by sell_allowed filter.",
  "decision context_context": {
    "price": 4462.58,
    "session": "london",
    "regime": {"regime": "TRENDING", "atr_h1": 26.66, "atr_d1": 171.16},
    "decision_data": {
      "indicators": {"atr_d1": 171.16, "atr_m5": 8.53, "spread_pts": 12}
    }
  }
}
```

### Audit: Get Decision

```bash
GET /audit/decision-record/{decision_id}
```

Returns a complete Decision (TDR) with:
- Decision context (who, what, when, why)
- Memory context (similar past decisions recalled)
- Decision Context snapshot (indicators, regime, risk)
- SHA-256 data hash

### Audit: Verify Integrity

```bash
GET /audit/verify/{decision_id}
```

```json
{
  "decision_id": "VB_20260326_0755",
  "verified": true,
  "stored_hash": "a3f8c9...",
  "computed_hash": "a3f8c9...",
  "match": true
}
```

Recomputes SHA-256 from stored inputs and compares. If any field was tampered with after recording, `match` will be `false`.

### Audit: Bulk Export

```bash
GET /audit/export?strategy=VolBreakout&start=2026-03-01&end=2026-03-31&format=jsonl
```

Export all TDRs as JSON or JSONL for regulatory submission.

## Security

- **DecisionMemory never touches API keys.** It does not execute decisions, move funds, or access wallets.
- **Read and record only.** The agent calls DecisionMemory after making a decision, passing the context. DecisionMemory stores it.
- **No external network calls.** The server runs locally. No data is sent to third parties.
- **SHA-256 tamper detection.** Every record is hashed at creation time. Verify integrity at any point with `/audit/verify`.
- **1,234 tests passing.** Full test suite with CI.
- **Scale:** 17 MCP tools, 35 REST endpoints, 5-layer memory architecture (episodic, semantic, procedural, affective, prospective).

## Regulatory Alignment

| Regulation | Requirement | DecisionMemory Coverage |
|------------|-------------|---------------------|
| MiFID II Article 17 | Record every algorithmic decision-making decision factor | Full decision chain: conditions, filters, indicators, execution |
| EU AI Act Article 14 | Human oversight of high-risk AI systems | Explainable reasoning + memory context for every decision |
| EU AI Act Logging | Systematic logging of every AI action and decision path | Automatic per-decision TDR with structured JSON |
| ESMA 2026 Briefing | Algorithms must be distinguishable, testable, identifiable | agent_id + model_version + strategy per record |

## MCP Integration

DecisionMemory also runs as an MCP server with 17 tools:

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

Key MCP tools: `store_decision`, `recall_decisions`, `get_performance`, `daily_reflection`, `audit_decision_record`, `audit_verify`.

## Links

- **PyPI**: [decisionmemory-protocol](https://pypi.org/project/decisionmemory-protocol/)
- **GitHub**: [mnemox-ai/decisionmemory-protocol](https://github.com/mnemox-ai/decisionmemory-protocol) (1,234 tests, MIT license)
- **Author**: [mnemox-ai](https://github.com/mnemox-ai)
