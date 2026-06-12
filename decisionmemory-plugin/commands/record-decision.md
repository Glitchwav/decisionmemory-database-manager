---
description: Record a completed decision into all memory layers with full context
argument-hint: "[symbol] [direction] [entry] [exit] [pnl]"
---

# Record Decision

Store a completed decision into DecisionMemory with full context. This writes to all 5 OWM memory layers (episodic, semantic, procedural, affective, prospective) and updates behavioral baselines.

## Workflow

### Step 1: Gather Decision Details

If decision details are provided in the argument, parse them. Otherwise ask for:
- **Symbol**: e.g., XAUUSD, BTCUSDT, EURUSD
- **Direction**: long or short
- **Entry price** and **Exit price**
- **Lot size** (optional, defaults to strategy default)
- **P&L** in dollars

### Step 2: Gather Context

Ask for or infer:
- **Strategy**: Which strategy triggered this decision (e.g., VolBreakout, IntradayMomentum)
- **Decision Context context**: Session (London/NY/Asian), volatility regime, trend state
- **Reflection**: Why did you enter? What was the signal? Would you take it again?
- **Confidence**: 0.0-1.0, how confident were you at entry?

### Step 3: Store via MCP

Use the `remember_decision` MCP tool to store across all OWM layers:

```
remember_decision({
  symbol, direction, entry_price, exit_price, pnl,
  strategy, lot_size, decision context_context, reflection, confidence
})
```

This automatically:
1. Creates an episodic memory (the raw decision event)
2. Updates semantic memory (strategy knowledge base)
3. Adjusts procedural memory (hold times, lot sizing patterns)
4. Updates affective state (confidence, drawdown, streak tracking)
5. Evaluates active prospective plans

### Step 4: Confirm and Summarize

Report back:
- Decision stored successfully
- Updated affective state (new confidence level, streak)
- Any active decision-making plans that were affected
- Similar past decisions (top 3 by OWM score) for quick comparison

## Example

```
User: /record-decision XAUUSD long 5180 5210 +$150