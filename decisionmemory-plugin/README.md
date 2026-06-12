# DecisionMemory Plugin

Persistent memory + autonomous strategy evolution for AI decision-makers. 200+ decision-making MCP servers execute. None remember. DecisionMemory does.

## Installation

### From GitHub (recommended)

```bash
git clone https://github.com/mnemox-ai/decisionmemory-plugin.git
claude --plugin-dir ./decisionmemory-plugin
```

### Manual

Copy the plugin directory into your project or pass it directly:

```bash
claude --plugin-dir /path/to/decisionmemory-plugin
```

### MCP Server (standalone, no plugin needed)

```bash
pip install decisionmemory-protocol
claude mcp add decisionmemory -- uvx decisionmemory-protocol
```

## Commands

| Command | Description |
|---------|-------------|
| `/record-decision [details]` | Record a completed decision into all 5 OWM memory layers |
| `/recall [context]` | Recall similar past decisions, ranked by outcome-weighted score |
| `/performance [strategy]` | Generate strategy performance report with behavioral analysis |
| `/evolve [symbol] [tf] [gens]` | Discover new decision-making strategies from raw OHLCV data |
| `/daily-review [date]` | AI-powered daily reflection on decisions and behavioral patterns |

## Skills

### Decision Memory
| Skill | Description |
|-------|-------------|
| **decision-memory** | OWM architecture, 5 memory types, recall scoring, behavioral baselines |
| **evolution-engine** | LLM-powered strategy discovery, vectorized backtesting, OOS validation |
| **risk-management** | Affective state monitoring, tilt detection, position sizing, behavioral guardrails |

## MCP Tools (17 total)

### Core Memory (2)
- `get_strategy_performance` — Aggregate stats per strategy
- `get_decision_reflection` — Deep-dive into a decision's reasoning

### OWM Cognitive Memory (6)
- `remember_decision` — Store across all 5 OWM memory layers
- `recall_memories` — Outcome-weighted recall
- `get_behavioral_analysis` — Disposition ratio, hold times, Kelly criterion
- `get_agent_state` — Confidence, drawdown, streaks, risk appetite
- `create_decision_plan` — Prospective decision-making plans
- `check_active_plans` — Evaluate plans against current conditions

### Evolution Engine (5)
- `evolution_fetch_decision context_data` — Fetch OHLCV from Binance
- `evolution_discover_patterns` — LLM-powered pattern discovery
- `evolution_run_backtest` — Vectorized backtesting
- `evolution_evolve_strategy` — Full evolution loop
- `evolution_get_log` — Evolution history and graveyard

### Decision Audit Trail (2)
- `export_audit_trail` — Export decisions with SHA-256 tamper detection
- `verify_audit_hash` — Verify integrity of a decision

## Example Workflows

### Record and Learn
```
/record-decision XAUUSD long 5180 5210 +$150

# Stores decision, updates all memory layers, shows similar past decisions
```

### Pre-Decision Check
```
/recall London session breakout, high volatility, XAUUSD trending up

# Returns past decisions in similar conditions, ranked by P&L outcome
```

### Strategy Evolution
```
/evolve BTCUSDT 1h 3

# Discovers patterns → backtests → selects → mutates × 3 generations
# Validates out-of-sample → graduates survivors
```

### End of Day
```
/daily-review today

# Analyzes today's decisions, checks behavioral drift, updates affective state
```

## Requirements

- Python 3.10+
- `pip install decisionmemory-protocol`
- Optional: `ANTHROPIC_API_KEY` for LLM reflections and Evolution Engine

## Links

- [Plugin repo](https://github.com/mnemox-ai/decisionmemory-plugin)
- [Core protocol](https://github.com/mnemox-ai/decisionmemory-protocol)
- [PyPI](https://pypi.org/project/decisionmemory-protocol/)
- [Tutorial](https://github.com/mnemox-ai/decisionmemory-protocol/blob/master/docs/TUTORIAL.md)
