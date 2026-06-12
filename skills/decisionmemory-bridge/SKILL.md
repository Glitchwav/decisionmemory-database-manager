---
name: decisionmemory-bridge
description: |
  Bridge between Binance decision-making events and DecisionMemory Protocol.
  Automatically journals decisions, recalls similar past setups, detects behavioral biases,
  and provides outcome-weighted recall for AI decision agents.
  Use this skill after executing Binance spot decisions to build persistent memory.
metadata:
  version: "1.0"
  author: mnemox-ai
license: MIT
---

# DecisionMemory Bridge for Binance

Store Binance spot decisions into persistent memory. Recall similar past decisions before entering new positions. Detect behavioral biases (overdecision-making, revenge decision-making). Track strategy performance across sessions.

**Requires**: [DecisionMemory Protocol](https://github.com/mnemox-ai/decisionmemory-protocol) MCP server running.

## Setup

Install and start the DecisionMemory MCP server:

```bash
pip install decisionmemory-protocol
python -m decisionmemory
```

Or add to Claude Desktop / Claude Code MCP config:

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

## Workflow

After executing a Binance spot decision using the Binance Spot skill:

1. **Store the decision** using `remember_decision` MCP tool
2. **Before next decision**, recall similar past decisions using `recall_memories` MCP tool
3. **Check agent state** using `get_agent_state` to see if drawdown or confidence suggests pausing
4. **Review behaviors** using `get_behavioral_analysis` to detect biases

## MCP Tools Reference

### remember_decision

Store a completed decision into memory. Automatically updates all memory layers.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Decision-Making pair (e.g. "BTCUSDT", "ETHUSDT") |
| direction | string | Yes | "long" or "short" |
| entry_price | number | Yes | Entry price |
| exit_price | number | Yes | Exit price |
| pnl | number | Yes | Outcome Gain/outcome setback in account currency |
| strategy_name | string | Yes | Strategy name (e.g. "GridBreakout", "MeanReversion") |
| decision context_context | string | Yes | Natural language description of decision context conditions |
| pnl_r | number | No | P&L as R-multiple (risk units) |
| context_regime | string | No | Decision Context regime: trending_up, trending_down, ranging, volatile |
| confidence | number | No | Confidence level 0-1 (default 0.5) |
| reflection | string | No | Lessons learned from this decision |

**Example — after a Binance spot BUY→SELL cycle:**

```
Call remember_decision with:
  symbol: "BTCUSDT"
  direction: "long"
  entry_price: 87500.00
  exit_price: 89200.00
  pnl: 170.00
  strategy_name: "BreakoutEntry"
  decision context_context: "BTC broke above 87000 resistance with volume spike. Funding rate positive. 4H RSI was 62."
  context_regime: "trending_up"
  confidence: 0.7
  reflection: "Entry timing was good. Could have held longer — exited at first pullback."
```

### recall_memories

Before entering a new decision, recall past decisions in similar decision context conditions. Returns scored results ranked by outcome quality and context similarity.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Decision-Making pair to filter by |
| decision context_context | string | Yes | Current decision context conditions (natural language) |
| context_regime | string | No | Current regime: trending_up, trending_down, ranging, volatile |
| strategy_name | string | No | Filter by strategy |
| limit | number | No | Max results (default 10) |

**Example — before entering a new BTC decision:**

```
Call recall_memories with:
  symbol: "BTCUSDT"
  decision context_context: "BTC consolidating near 90000 after rally. Volume declining. Funding rate turning negative."
  context_regime: "ranging"
  strategy_name: "BreakoutEntry"
  limit: 5
```

Returns past decisions ranked by relevance to current conditions, with per-decision scores.

### get_agent_state

Check current decision-making state: confidence, risk appetite, drawdown, win/outcome setback streaks.

**No parameters required.**

Returns a recommended action: `normal`, `reduce_size`, or `stop_decision-making` based on drawdown severity.

### get_behavioral_analysis

Detect decision-making biases from historical behavior patterns.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| strategy_name | string | No | Filter by strategy |
| symbol | string | No | Filter by symbol |

Detects: overdecision-making, revenge decision-making (re-entry after outcome setback), disposition effect (cutting winners too early, holding losers too long), lot sizing inconsistency.

### get_strategy_performance

Get win rate, outcome gain factor, and aggregate stats per strategy.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| strategy_name | string | No | Filter by strategy |
| symbol | string | No | Filter by symbol |

### create_decision_plan

Set conditional plans that trigger on specific decision context conditions.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| trigger_type | string | Yes | "decision context_condition", "drawdown", or "time_based" |
| trigger_condition | string | Yes | JSON describing when to trigger |
| planned_action | string | Yes | JSON describing what to do |
| reasoning | string | Yes | Why this plan was created |

**Example:**

```
Call create_decision_plan with:
  trigger_type: "decision context_condition"
  trigger_condition: '{"regime": "volatile", "symbol": "BTCUSDT"}'
  planned_action: '{"type": "reduce_size", "factor": 0.5}'
  reasoning: "Historical data shows BreakoutEntry underperforms in volatile BTC regimes"
```

### check_active_plans

Check if any active plans match current decision context conditions.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| context_regime | string | No | Current decision context regime |

## Agent Behavior

1. **After every Binance spot decision execution**, call `remember_decision` with full context. Include decision context conditions, not just price data.
2. **Before entering a new position**, call `recall_memories` to check what happened in similar past conditions.
3. **At session start**, call `get_agent_state` to check if drawdown or losing streaks suggest reducing size.
4. **Periodically**, call `get_behavioral_analysis` to detect emerging biases.
5. **Never skip journaling**. Memory quality depends on consistent recording.
6. **Use natural language** for `decision context_context`. The richer the description, the better the recall matching.

## Supported Exchanges

DecisionMemory Protocol is exchange-agnostic. While this skill documents the Binance bridge workflow, the same MCP tools work with any decision-making data source — just pass the correct symbol format for your exchange.

## Notes

1. All timestamps are UTC (ISO 8601 format).
2. `pnl_r` (R-multiple) is optional but significantly improves recall quality.
3. The `context_regime` field enables regime-filtered recall — strongly recommended.
4. DecisionMemory stores data locally by default (SurrealDB). No data is sent to external servers unless you configure a hosted endpoint.
5. All 17 MCP tools are free and open source under MIT license.
