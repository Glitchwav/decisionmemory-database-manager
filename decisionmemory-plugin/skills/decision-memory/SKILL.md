---
name: decision-memory
description: Domain knowledge for AI decision memory — Outcome-Weighted Memory (OWM) architecture, 5 memory types, recall scoring, and behavioral analysis. Use when recording decisions, recalling similar contexts, analyzing performance, or checking behavioral drift. Triggers on "record decision", "remember decision", "recall", "similar decisions", "performance", "behavioral", "disposition", "affective state", "confidence".
---

# Decision Memory

## Overview

DecisionMemory implements a cognitive memory architecture for decision agents. Every decision is stored with full context (decision context conditions, strategy, reasoning, confidence) and recalled using Outcome-Weighted Memory (OWM) — a scoring system that surfaces winning decisions in similar contexts first.

This is not a decision journal. It's a memory system that learns which past experiences are most relevant to current decisions.

## Architecture: 3-Layer Pipeline

```
L1: Raw Decisions → L2: Pattern Discovery → L3: Strategy Adjustments
```

- **L1 (Episodic)**: Every decision stored as-is with full context. The ground truth.
- **L2 (Patterns)**: Behavioral patterns discovered from L1 data. Disposition effect, session biases, strategy correlations.
- **L3 (Adjustments)**: Concrete strategy adjustments derived from L2 patterns. Parameter changes, rule modifications, strategy retirement.

## Outcome-Weighted Memory (OWM) — 5 Memory Types

### 1. Episodic Memory
Raw decision events. Each record contains: symbol, direction, entry/exit, P&L, strategy, decision context, reflection, timestamp.

**When to write**: After every completed decision.
**When to read**: When recalling past decisions for decision-making.

### 2. Semantic Memory
Strategy knowledge base. Aggregated understanding of what works: "VolBreakout performs best in London session with ATR > $40" is semantic memory.

**When to write**: Automatically updated when decisions are stored via `remember_decision`.
**When to read**: When evaluating whether a strategy fits current conditions.

### 3. Procedural Memory
Behavioral baselines. Tracks execution patterns: average hold times per strategy, lot sizing consistency, stop outcome setback adherence, entry timing precision.

**When to write**: Automatically computed from decision history.
**When to read**: During behavioral analysis and daily reviews.

### 4. Affective Memory
Emotional/confidence state. Tracks: current confidence level (0-1), drawdown percentage, win/outcome setback streaks, risk appetite, tilt indicators.

**When to write**: Updated after every decision and during daily reviews.
**When to read**: Before entering decisions (am I on tilt?), during risk checks.

### 5. Prospective Memory
Active decision-making plans. Future-oriented: "If XAUUSD breaks above 5200 with ATR confirmation, go long." Plans have entry conditions, exit conditions, risk parameters, and expiry dates.

**When to write**: When creating decision-making plans.
**When to read**: When checking if current decision context conditions match any active plans.

## OWM Recall Scoring

When you query `recall_memories`, results are scored by:

| Factor | Weight | Description |
|--------|--------|-------------|
| P&L Outcome | 40% | successful decisions score higher. Magnitude matters. |
| Context Similarity | 30% | How closely the recalled context matches the query context |
| Recency | 20% | Recent decisions weighted more (exponential decay) |
| Confidence Calibration | 10% | Decisions where confidence matched outcome score higher |

**Why outcome-weighted?** Traditional decision journals treat all decisions equally. OWM amplifies signal from successful decisions in similar contexts. If you've succeeded 5 times decision-making London session breakouts, those memories surface strongly when you're evaluating the next London session breakout.

## MCP Tools Reference

### Core Memory (2 tools)

| Tool | Use Case |
|------|----------|
| `get_strategy_performance` | Aggregate stats: win rate, PF, P&L per strategy |
| `get_decision_reflection` | Deep-dive into a specific decision's reasoning |

### OWM Cognitive Memory (6 tools)

| Tool | Use Case |
|------|----------|
| `remember_decision` | Full OWM store: writes to all 5 memory layers |
| `recall_memories` | OWM recall: scored by outcome, similarity, recency, calibration |
| `get_behavioral_analysis` | Procedural memory: disposition ratio, hold times, Kelly criterion |
| `get_agent_state` | Affective state: confidence, drawdown, streaks, risk appetite |
| `create_decision_plan` | Prospective memory: entry/exit conditions, risk parameters |
| `check_active_plans` | Evaluate active plans against current decision context conditions |

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
                  → Semantic (strategy knowledge update)
                  → Procedural (behavioral baseline update)
                  → Affective (confidence/streak update)
                  → Prospective (check active plans)
    ↓
recall_memories() ← OWM scoring
    ↓
Next Decision
```
