---
name: decision-memory
description: Use DecisionMemory Protocol v0.5.2 for persistent decision memory, outcome-weighted recall, behavioral and affective analysis, prospective plans, audit verification, strategy validation, and evolution. Trigger when the user asks to record or remember a completed decision; recall similar decisions or contexts; inspect strategy performance, reflection, behavioral drift, disposition, confidence, drawdown, or agent state; create or check a decision plan; compute decision quality or legitimacy; validate or evolve a strategy; or export or verify an audit trail.
---

# Decision Memory

## Overview

DecisionMemory implements a cognitive memory architecture for decision agents. Every decision is stored with full context (decision context conditions, strategy, reasoning, confidence) and recalled using Outcome-Weighted Memory (OWM) — a scoring system that surfaces winning decisions in similar contexts first.

This is not a decision journal. It's a memory system that learns which past experiences are most relevant to current decisions.

## Architecture

```
Episodic → Semantic → Procedural
              ↘ Affective
Prospective plans are created and checked separately.
```

## Outcome-Weighted Memory (OWM) — 5 Memory Types

### 1. Episodic Memory
Raw decision events. Each record contains: symbol, direction, entry/exit, P&L, strategy, decision context, reflection, timestamp.

**When to write**: After every completed decision.
**When to read**: When recalling past decisions for decision-making.

### 2. Semantic Memory
Strategy knowledge base. Aggregated understanding of what works: "VolBreakout performs best in London session with ATR > $40" is semantic memory.

**When to write**: Automatically updated by `remember_decision`.
**When to read**: When evaluating whether a strategy fits current conditions.

### 3. Procedural Memory
Behavioral baselines. Tracks execution patterns: average hold times per strategy, lot sizing consistency, stop outcome setback adherence, entry timing precision.

**When to write**: Automatically updated by `remember_decision`.
**When to read**: During behavioral analysis and daily reviews.

### 4. Affective Memory
Emotional/confidence state. Tracks: current confidence level (0-1), drawdown percentage, win/outcome setback streaks, risk appetite, tilt indicators.

**When to write**: Automatically updated by `remember_decision`.
**When to read**: Before entering decisions (am I on tilt?), during risk checks.

### 5. Prospective Memory
Active decision-making plans. Future-oriented: "If XAUUSD breaks above 5200 with ATR confirmation, go long." Plans have entry conditions, exit conditions, risk parameters, and expiry dates.

**When to write**: When creating decision-making plans.
**When to read**: When checking if current decision context conditions match any active plans.

## OWM Recall Scoring

Pure OWM recall uses a multiplicative five-factor score:

```
score = Q × Sim × Rec × Conf × Aff
```

| Factor | Implementation |
|--------|----------------|
| `Q` outcome quality | `sigmoid(2 × pnl_r / 1.5)`; falls back to memory confidence when `pnl_r` is absent |
| `Sim` context similarity | Similarity between stored and query `ContextVector` values |
| `Rec` recency | Power law `(1 + age_days / tau)^(-d)`; episodic uses `tau=30, d=0.5`, semantic uses `tau=180, d=0.3` |
| `Conf` confidence | `0.5 + 0.5 × clamp(confidence, 0, 1)` |
| `Aff` affective modulation | Current drawdown/loss-streak modulation, clamped to `[0.7, 1.3]` |

By default, `recall_memories` requests hybrid recall with `hybrid_alpha=0.3`. When embeddings are available, the final hybrid score blends vector similarity and OWM; otherwise it falls back to the pure multiplicative OWM score.

## MCP Tools Reference

DecisionMemory Protocol v0.5.2 registers **20 MCP tools**.

### Memory and State

| Tool | Signature |
|------|-----------|
| `get_strategy_performance` | `(strategy_name=None, symbol=None)` |
| `get_decision_reflection` | `(decision_id)` |
| `remember_decision` | `(symbol, direction, entry_price, exit_price, pnl, strategy_name, market_context, pnl_r=None, context_regime=None, context_atr_d1=None, confidence=0.5, reflection=None, max_adverse_excursion=None, decision_id=None, timestamp=None, entry_timestamp=None, exit_timestamp=None)` |
| `recall_memories` | `(symbol, market_context, context_regime=None, context_atr_d1=None, strategy_name=None, memory_types=None, limit=10, use_hybrid=True, hybrid_alpha=0.3)` |
| `get_behavioral_analysis` | `(strategy_name=None, symbol=None)` |
| `get_agent_state` | `()` |
| `create_decision_making_plan` | `(trigger_type, trigger_condition, planned_action, reasoning, expiry_days=30, priority=0.5)` |
| `check_active_plans` | `(context_regime=None, context_atr_d1=None)` |

### Evolution, Audit, and Validation

| Tool | Signature |
|------|-----------|
| `evolution_fetch_market_data` | `(symbol, timeframe="1h", days=90)` |
| `evolution_discover_patterns` | `(symbol, timeframe="1h", count=5, temperature=0.7, days=90)` |
| `evolution_run_backtest` | `(pattern_dict, symbol="BTCUSDT", timeframe="1h", days=90)` |
| `evolution_evolve_strategy` | `(symbol, timeframe="1h", generations=3, population_size=10, days=90)` |
| `evolution_get_log` | `()` |
| `export_audit_trail` | `(decision_id=None, strategy=None, start=None, end=None, limit=50)` |
| `verify_audit_hash` | `(decision_id)` |
| `verify_audit_chain` | `(from_seq=None, to_seq=None)` |
| `get_daily_root` | `(date, rebuild=False, request_tsa=False, include_token=False)` |
| `validate_strategy` | `(file_path, format="quantconnect", strategy_name="", num_strategies=1)` |
| `check_decision_legitimacy` | `(strategy_name, symbol="XAUUSD", current_regime=None, current_atr_d1=None)` |
| `compute_dqs` | `(symbol, strategy_name, direction, proposed_lot_size=0.1, market_context="", context_regime=None, context_atr_d1=None)` |

## Best Practices

### When to Record
- **Always** record after a decision closes, not while it's open
- Include the full decision context — session, volatility, trend state
- Write an honest reflection — why you entered, what you expected, what happened
- Set confidence before seeing the result (not after)

### When to Recall
- **Before entering a decision**: "Have I been in this situation before? What happened?"
- **During daily review**: "What patterns emerge from this week's decisions?"
- **After a outcome setback**: "Have I seen this failure mode before?"

### When NOT to Recall
- Don't recall mid-decision to justify holding a loser
- Don't recall to confirm a decision you've already made (confirmation bias)
- Don't over-query — if you're recalling 20 times a day, you're procrastinating, not decision-making

## Common Mistakes

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| Recording without context | Useless for recall — can't match future situations | Always include session, volatility, trend state |
| Setting confidence after seeing P&L | Destroys calibration scoring | Set confidence at entry, before outcome is known |
| Ignoring affective state | Decision-Making on tilt leads to revenge decisions | Check `get_agent_state` before every session |
| Never running daily reviews | Behavioral drift goes undetected | Run `/daily-review` at end of each decision-making day |
| Storing paper decisions as real decisions | Pollutes performance metrics | Tag paper decisions separately or use a different database |

## Data Flow

```
Decision Closes
    ↓
remember_decision() → Episodic (raw event)
                  → Semantic (Bayesian strategy knowledge)
                  → Procedural (running behavior statistics)
                  → Affective (EWMA confidence/streak state)
                  → decision_records (backward compatibility)
    ↓
recall_memories() ← OWM scoring
    ↓
Next Decision
```

`remember_decision` does **not** write prospective memory. Use
`create_decision_making_plan` to create prospective plans and
`check_active_plans` to evaluate them.
