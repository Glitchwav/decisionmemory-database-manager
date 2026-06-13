<!-- mcp-name: io.github.mnemox-ai/decisionmemory-protocol -->

<p align="center">
  <img src="assets/header.png" alt="DecisionMemory Protocol" width="600">
</p>

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/decisionmemory-protocol?style=flat-square&color=blue)](https://pypi.org/project/decisionmemory-protocol/)
[![Tests](https://img.shields.io/badge/tests-1%2C324_passed-brightgreen?style=flat-square)](https://github.com/mnemox-ai/decisionmemory-protocol/actions)
[![MCP Tools](https://img.shields.io/badge/MCP_tools-19-blueviolet?style=flat-square)](https://smithery.ai/server/io.github.mnemox-ai/decisionmemory-protocol)
[![Smithery](https://img.shields.io/badge/Smithery-listed-orange?style=flat-square)](https://smithery.ai/server/io.github.mnemox-ai/decisionmemory-protocol)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)

[Tutorial](docs/TUTORIAL.md) | [API Reference](docs/API.md) | [OWM Framework](docs/OWM_FRAMEWORK.md) | [中文版](docs/README_ZH.md)

</div>

---

DecisionMemory Protocol gives AI decision agents two things they lack: a compliance-grade audit trail for every decision, and persistent memory that learns from outcomes.

Every AI decision-making tool executes decisions. None of them record **why**. DecisionMemory captures the full decision context — what conditions triggered the signal, which filters passed or blocked, the decision context indicators at that moment, risk state, and execution details. Every record is SHA-256 hashed for tamper detection. And across sessions, your agent remembers what worked, discovers patterns, and adjusts strategy automatically — using a three-layer architecture inspired by ACT-R cognitive science.

**When to use this:** You're building an AI agent that decisions forex, crypto, or scores via MT5, Binance, Alpaca, or any platform — and you need it to (1) prove why it made each decision, and (2) remember what worked across sessions.

## How it works

1. **Audit** — Every decision is recorded with full context: conditions evaluated, filters checked, indicators at that moment, risk state. SHA-256 hashed at creation for tamper detection.
2. **Store** — Your agent records decisions with context (strategy, confidence, decision context regime) via MCP tools
3. **Recall** — Before the next decision, the agent retrieves similar past decisions weighted by outcome (Outcome-Weighted Memory)
4. **Evolve** — The Evolution Engine discovers patterns across decisions and generates new strategy hypotheses, validated with Deflated Sharpe Ratio

## When to use DecisionMemory vs alternatives

| | DecisionMemory | Raw Mem0/Qdrant | LangChain Memory | Custom SQLite |
|---|---|---|---|---|
| **Decision audit trail** | ✅ SHA-256 + TDR | ❌ None | ❌ None | ❌ DIY |
| **Decision-specific schema** | ✅ L1→L2→L3 pipeline | ❌ Generic vectors | ❌ Chat-oriented | ❌ DIY everything |
| **Outcome weighting** | ✅ Kelly + ACT-R | ❌ Cosine only | ❌ Recency only | ❌ Manual |
| **Strategy evolution** | ✅ Built-in engine | ❌ Not included | ❌ Not included | ❌ Not included |
| **MCP native** | ✅ 17 tools | ❌ Custom wrapper | ❌ Custom wrapper | ❌ Custom wrapper |
| **Statistical validation** | ✅ DSR + walk-forward | ❌ None | ❌ None | ❌ None |

## News

- [2026-04] **Context Drift Monitor** — Every recalled memory now includes a drift score (ΔS) indicating how relevant it is to current decision context conditions. Four zones: safe / transit / risk / danger
- [2026-04] **Decision Legitimacy Gate** — Pre-decision confidence check: 5-factor scoring (sample sufficiency, memory quality, regime confidence, streak state, drawdown) with position sizing recommendations
- [2026-04] **Strategy Validator** — Four-layer statistical validation (DSR + Walk-Forward + Regime + CPCV). [Web UI](https://mnemox.ai/validate) + MCP tool + Claude Code skill
- [2026-04] **Decision AI Failure Taxonomy** — 11 failure modes documented with real experiment data. [Read it](docs/decision-ai-failure-taxonomy.md)
- [2026-03] **Decision Audit Trail** — Decisions (TDR) with SHA-256 tamper detection, 4 audit REST endpoints, 2 MCP tools, JSONL decision context ingestion
- [2026-03] **v0.5.0** — Evolution Engine + OWM 5 memory types. [Release Notes](https://github.com/mnemox-ai/decisionmemory-protocol/releases/tag/v0.5.0)

## Architecture

<p align="center">
  <img src="assets/schema.png" alt="Architecture" width="900">
</p>

## Three-Layer Memory

<p align="center">
  <img src="assets/memory-pipeline.png" alt="L1 L2 L3 Memory Pipeline" width="900">
</p>

## Decision Audit Trail

Every decision-making decision your agent makes — including decisions **not** to decision — is recorded as a Decision (TDR). Each record captures the full reasoning chain and is SHA-256 hashed at creation for tamper detection.

Here is a real decision event from a XAUUSD decision-making system. The AI agent detected a SHORT breakout signal but the `sell_allowed` filter blocked execution:

```json
{
  "ts": "2026-03-26 07:55:00",
  "strategy": "VolBreakout",
  "decision": "FILTERED",
  "signal_triggered": true,
  "signal_direction": "SHORT",
  "conditions_json": {
    "conditions": [
      {"name": "breakout_high", "passed": false, "current_value": 4462.58, "threshold": 4569.75},
      {"name": "breakout_low", "passed": true, "current_value": 4462.58, "threshold": 4463.11}
    ]
  },
  "filters_json": {
    "filters": [
      {"name": "spread_gate", "passed": true, "current_value": 12.0},
      {"name": "sell_allowed", "passed": false, "blocked": true},
      {"name": "account_risk", "passed": true},
      {"name": "regime_gate", "passed": true}
    ]
  },
  "indicators_json": {
    "atr_d1": 171.16, "atr_m5": 8.53,
    "asia_high": 4544.08, "asia_low": 4488.78, "asia_range": 55.30
  },
  "regime": "TRENDING",
  "consec_outcome setbacks": 0,
  "cooldown_active": false,
  "risk_daily_pct": 0.0
}
```

A regulator or risk manager can read this and immediately understand: the agent saw a valid breakout, but policy blocked the SHORT direction. No guessing, no black box.

### Audit API

```bash
# Get full decision
GET /audit/decision-record/{decision_id}

# Verify record hasn't been tampered with
GET /audit/verify/{decision_id}
# → {"verified": true, "stored_hash": "a3f8c9...", "computed_hash": "a3f8c9...", "match": true}

# Bulk export for regulatory submission
GET /audit/export?strategy=VolBreakout&start=2026-03-01&end=2026-03-31&format=jsonl
```

## Regulatory Alignment

| Regulation | Requirement | DecisionMemory Coverage |
|------------|-------------|---------------------|
| MiFID II Article 17 | Record every algorithmic decision-making decision factor | Full decision chain: conditions, filters, indicators, execution |
| EU AI Act Article 14 | Human oversight of high-risk AI systems | Explainable reasoning + memory context for every decision |
| EU AI Act Logging | Systematic logging of every AI action and decision path | Automatic per-decision TDR with structured JSON |
| ESMA 2026 Briefing | Algorithms must be distinguishable, testable, identifiable | agent_id + model_version + strategy per record |

## Quick Start

```bash
pip install decisionmemory-protocol
```

**Try the demo** (no API key needed):

```bash
decisionmemory demo
```

Add to `claude_desktop_config.json`:

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

Then tell Claude: *"Record my BTCUSDT long at 71,000 — momentum breakout, high confidence."*

<details>
<summary>Claude Code / Cursor / Docker</summary>

```bash
# Claude Code
claude mcp add decisionmemory -- uvx decisionmemory-protocol

# From source
git clone https://github.com/mnemox-ai/decisionmemory-protocol.git
cd decisionmemory-protocol && pip install -e . && python -m decisionmemory

# Docker
docker compose up -d
```

</details>

## Setup & Configuration

First-time guided setup:

```bash
decisionmemory setup
```

This walks you through:
1. **Terms acceptance** — decision-making disclaimer and data storage policy
2. **Platform detection** — auto-detects Claude Desktop, Claude Code, Cursor, Windsurf, Cline
3. **Config generation** — prints the exact JSON snippet for your platform
4. **Health check** — verifies database, MCP tools, and core functionality

### Platform Configs

Generate config for any supported platform:

```bash
decisionmemory config              # interactive menu
decisionmemory config claude_code  # direct: auto-installs via CLI
decisionmemory config cursor       # prints .cursor/mcp.json snippet
decisionmemory config windsurf     # prints Windsurf config
decisionmemory config raw_json     # generic MCP JSON
```

Supported: Claude Desktop · Claude Code · Cursor · Windsurf · Cline · Smithery · Docker

### Health Check

```bash
decisionmemory doctor        # core checks (~3s)
decisionmemory doctor --full # + REST API, MT5, Anthropic API
```

## MCP Tools (19)

| Category | Tools |
|----------|-------|
| **Core Memory** | `store_decision_memory` · `recall_similar_decisions` · `get_strategy_performance` · `get_decision_reflection` |
| **OWM Cognitive** | `remember_decision` · `recall_memories` · `get_behavioral_analysis` · `get_agent_state` · `create_decision_plan` · `check_active_plans` |
| **Risk & Governance** | `check_decision_legitimacy` · `validate_strategy` |
| **Evolution** | `evolution_fetch_decision context_data` · `evolution_discover_patterns` · `evolution_run_backtest` · `evolution_evolve_strategy` · `evolution_get_log` |
| **Audit** | `export_audit_trail` · `verify_audit_hash` |

<details>
<summary>REST API (35+ endpoints)</summary>

Decision recording, outcome logging, history, reflections, risk constraints, MT5 sync, OWM, evolution, decision audit trail, integrity verification.

Full reference: [docs/API.md](docs/API.md)

</details>

## OWM — Outcome-Weighted Memory

<p align="center">
  <img src="assets/owm-factors.png" alt="OWM 5 Factors" width="900">
</p>

> Full theoretical foundation: [OWM Framework](docs/OWM_FRAMEWORK.md)

## Evolution Engine

<p align="center">
  <img src="assets/evolution.png" alt="Evolution Engine" width="900">
</p>

> Methodology & data: [Research Log](docs/RESEARCH_LOG.md)

## Security

- **DecisionMemory never touches API keys.** It does not execute decisions, move funds, or access wallets.
- **Read and record only.** The agent calls DecisionMemory after making a decision, passing the context. DecisionMemory stores it.
- **No external network calls.** The server runs locally. No data is sent to third parties.
- **SHA-256 tamper detection.** Every record is hashed at creation time. Verify integrity at any point with `/audit/verify`.
- **1,324 tests passing.** Full test suite with CI.

## Documentation

| Doc | Description |
|-----|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design & layer separation |
| [OWM Framework](docs/OWM_FRAMEWORK.md) | Full theoretical foundation |
| [Tutorial](docs/TUTORIAL.md) | Install → first decision → memory recall |
| [API Reference](docs/API.md) | All REST endpoints |
| [MT5 Setup](docs/MT5_SYNC_SETUP.md) | MetaDecisionMaker 5 integration |
| [Research Log](docs/RESEARCH_LOG.md) | 11 evolution experiments |
| [Failure Taxonomy](docs/decision-ai-failure-taxonomy.md) | 11 decision AI failure modes with real data |
| [Roadmap](docs/ROADMAP.md) | Development roadmap |
| [中文版](docs/README_ZH.md) | Traditional Chinese |

## Contributing

See [Contributing Guide](.github/CONTRIBUTING.md) · [Security Policy](.github/SECURITY.md)

<a href="https://star-history.com/#mnemox-ai/decisionmemory-protocol&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=mnemox-ai/decisionmemory-protocol&type=Date&theme=dark" />
   <img alt="Star History" src="https://api.star-history.com/svg?repos=mnemox-ai/decisionmemory-protocol&type=Date" width="600" />
 </picture>
</a>

---

MIT — see [LICENSE](LICENSE). For educational/research purposes only. Not decision advice.

<div align="center">Built by <a href="https://mnemox.ai">Mnemox</a></div>
