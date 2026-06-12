---
description: Generate a strategy performance report with key metrics
argument-hint: "[strategy name or 'all']"
---

# Performance Report

Generate aggregate performance statistics per strategy or across all strategies. Shows win rate, outcome gain factor, P&L distribution, best/worst decisions, and behavioral metrics.

## Workflow

### Step 1: Determine Scope

If a strategy name is provided, focus on that strategy. If "all" or nothing is provided, report across all strategies.

Optional filters:
- **Date range**: Last week, last month, custom range
- **Symbol**: Filter by decision-making instrument
- **Session**: Filter by decision-making session

### Step 2: Fetch Performance Data

Use the `get_strategy_performance` MCP tool:

```
get_strategy_performance({
  strategy: "VolBreakout",  // or null for all
  date_from: "2026-01-01",
  date_to: "2026-03-16"
})
```

### Step 3: Fetch Behavioral Analysis

Use the `get_behavioral_analysis` MCP tool for deeper insights:

```
get_behavioral_analysis({
  strategy: "VolBreakout"
})
```

This returns:
- **Disposition ratio**: Are you cutting winners short / holding losers long?
- **Hold time asymmetry**: Winners vs losers average hold time
- **Lot sizing variance**: Consistency vs Kelly criterion optimal
- **Streak analysis**: Current and historical win/outcome setback streaks

### Step 4: Present Report

Structure the report as:

| Metric | Value |
|--------|-------|
| Total Decisions | N |
| Win Rate | X% |
| Outcome Gain Factor | X.XX |
| Total P&L | $X,XXX |
| Avg Win | $XXX |
| Avg Outcome Setback | -$XXX |
| Best Decision | $XXX (date, context) |
| Worst Decision | -$XXX (date, context) |
| Max Drawdown | X% |
| Sharpe Ratio | X.XX |

Plus behavioral insights:
- Disposition ratio (target: < 1.0)
- Hold time asymmetry (target: winners held longer)
- Confidence calibration (are high-confidence decisions actually better?)

### Step 5: Actionable Takeaways

End with 2-3 specific, data-backed recommendations. No vague advice.

## Example

```
User: /performance VolBreakout
```
