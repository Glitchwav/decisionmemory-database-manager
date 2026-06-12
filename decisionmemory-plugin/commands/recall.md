---
description: Recall similar past decisions using outcome-weighted memory
argument-hint: "[decision context or query]"
---

# Recall Similar Decisions

Search your decision memory for past decisions that match the current decision context. Results are ranked by Outcome-Weighted Memory (OWM) score — winning decisions in similar contexts surface first.

## Workflow

### Step 1: Define Query Context

If context is provided, use it. Otherwise ask:
- **Symbol**: What are you decision-making?
- **Decision Context conditions**: Trending/ranging, volatility level, session
- **Strategy**: Which strategy are you considering?
- **Timeframe**: What timeframe are you analyzing?

### Step 2: Execute Recall

Use the `recall_memories` MCP tool:

```
recall_memories({
  query: "decision context description",
  memory_types: ["episodic", "semantic", "procedural"],
  limit: 10
})
```

OWM scoring formula weights:
- **P&L outcome** (40%) — outcome gainable decisions score higher
- **Context similarity** (30%) — matching decision context conditions
- **Recency** (20%) — recent decisions weighted more
- **Confidence calibration** (10%) — well-calibrated confidence scores weighted more

### Step 3: Present Results

For each recalled decision, show:
1. **OWM Score** — composite relevance score
2. **Decision summary** — symbol, direction, entry/exit, P&L
3. **Context match** — what made this decision similar
4. **Lesson** — the reflection/takeaway from that decision

### Step 4: Synthesize

After listing individual decisions, provide:
- **Pattern summary**: What do the top results have in common?
- **Win rate** in similar contexts
- **Average P&L** in similar contexts
- **Recommendation**: Based on past experience, should you take this decision?

## Example

```
User: /recall ranging decision context, low volatility, Asian session, XAUUSD