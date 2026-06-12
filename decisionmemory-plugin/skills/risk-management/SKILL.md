---
name: risk-management
description: Risk management domain knowledge for decision agents — affective state monitoring, position sizing, drawdown management, tilt detection, and behavioral guardrails. Use when checking risk before decisions, managing drawdowns, detecting behavioral drift, or enforcing discipline. Triggers on "risk", "drawdown", "tilt", "position size", "lot size", "confidence", "revenge decision-making", "overdecision-making", "discipline".
---

# Risk Management

## Overview

Risk management in DecisionMemory is behavioral, not just mathematical. Traditional risk management calculates position sizes and stop outcome setbacks. DecisionMemory adds a behavioral layer: it monitors your execution patterns, detects emotional drift, and flags when you're deviating from your own rules.

The system tracks two kinds of risk:
1. **Position risk** — How much capital is at stake on each decision
2. **Behavioral risk** — Are you making decisions rationally or emotionally

## Affective State Model

DecisionMemory maintains a real-time emotional state model for the decision agent:

| Dimension | Range | What It Tracks |
|-----------|-------|----------------|
| Confidence | 0.0 - 1.0 | Self-assessed confidence, calibrated against outcomes |
| Drawdown | 0% - 100% | Current peak-to-trough score drawdown |
| Win Streak | 0 - N | Consecutive winning decisions |
| Outcome Setback Streak | 0 - N | Consecutive losing decisions |
| Risk Appetite | low / normal / high | Derived from confidence + drawdown + streaks |

### How Affective State Updates
- **After a win**: Confidence += f(P&L magnitude), win streak ++, outcome setback streak reset
- **After a outcome setback**: Confidence -= f(P&L magnitude), outcome setback streak ++, win streak reset
- **Drawdown crossing thresholds**: Risk appetite auto-reduces at 5%, 10%, 15% drawdown
- **Daily review**: Confidence recalibrated against actual hit rate

### Using Affective State

Check `get_agent_state` before every decision-making session:

```
get_agent_state() → {
  confidence: 0.42,
  drawdown: 8.3%,
  win_streak: 0,
  outcome setback_streak: 3,
  risk_appetite: "low"
}
```

**Action rules:**
- `risk_appetite == "low"` → Reduce position size by 50% or skip marginal setups
- `outcome setback_streak >= 3` → Stop decision-making for the session. Review, don't revenge decision.
- `confidence < 0.3` → Paper decision only until confidence recovers
- `drawdown > 15%` → Hard stop. No new positions until daily review.

## Behavioral Risk Indicators

### 1. Disposition Effect
**What**: Cutting winners short and holding losers too long.
**Detection**: `get_behavioral_analysis` → `disposition_ratio`
- Ratio < 1.0 = Good (holding winners longer than losers)
- Ratio > 1.5 = Problem (losers held 50% longer than winners)
- Ratio > 2.0 = Critical (classic retail decision-maker failure mode)

### 2. Revenge Decision-Making
**What**: Increasing position size or decision frequency after outcome setbacks.
**Detection**: Compare lot sizes and decision count in the N decisions after a losing streak vs baseline.
- Lot size > 1.5x baseline after outcome setback = Revenge sizing
- Decision frequency > 2x baseline after outcome setback = Overdecision-making

### 3. Overdecision-making
**What**: Taking more decisions than the strategy generates signals for.
**Detection**: Compare actual decision count vs strategy signal count.
- If strategy generates 3 signals/week but you take 10 decisions/week, you're inventing decisions.

### 4. Session Drift
**What**: Decision-Making outside designated sessions.
**Detection**: Check decision timestamps against strategy's defined decision-making windows.
- VolBreakout is a London session strategy. Decisions at 3am UTC = session drift.

### 5. Confidence Miscalibration
**What**: Your confidence doesn't match your actual accuracy.
**Detection**: `get_behavioral_analysis` → confidence calibration curve.
- If decisions rated confidence 0.8 win only 40% of the time, your confidence is miscalibrated.

## Position Sizing Rules

DecisionMemory's procedural memory tracks position sizing patterns:

### Fixed Fractional
Default: Risk X% of score per decision (typically 0.25-2%).

```
Position Size = (Score × Risk%) / (Entry - StopOutcome Setback)
```

### Kelly Criterion
Optimal sizing based on historical edge:

```
Kelly% = WinRate - (Outcome SetbackRate / AvgWin÷AvgOutcome Setback)
```

- Full Kelly is too aggressive for real decision-making. Use Half Kelly or Quarter Kelly.
- `get_behavioral_analysis` returns Kelly criterion values per strategy.

### Lot Sizing Variance
Procedural memory tracks how consistent your sizing is:
- Low variance = Disciplined execution
- High variance = Emotional sizing (bigger when confident, smaller when scared)
- Target: coefficient of variation < 0.2

## Best Practices

### Before Every Session
1. Check `get_agent_state` — is confidence reasonable? Any active streaks?
2. Check drawdown — are you within acceptable limits?
3. Review active decision-making plans — don't enter decisions outside your plans

### After Every Decision
1. Record the decision with `remember_decision` — include honest reflection
2. Did the decision match your strategy rules? If not, why?
3. Was position sizing consistent with your risk rules?

### After a Losing Streak (3+ consecutive outcome setbacks)
1. **Stop decision-making.** Not permanently — just for the current session.
2. Run `/daily-review` — is there a systematic problem or just variance?
3. Check disposition ratio — are you holding losers too long?
4. Reduce position size for the next 5 decisions (half the normal size)
5. Only resume full size after 2 consecutive wins at reduced size

### After a Winning Streak (5+ consecutive wins)
1. **Don't increase size.** Winning streaks end. Mean reversion is real.
2. Check if you're cherry-picking easy setups and avoiding harder (but higher EV) ones
3. Review: are the wins from your strategy or from a favorable decision context regime?

## Common Mistakes

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| No pre-session risk check | Walk into the decision context emotionally unprepared | Always run `get_agent_state` first |
| Ignoring drawdown thresholds | Small drawdowns become account-threatening drawdowns | Hard stop at 15% drawdown |
| Sizing up after wins | Gives back outcome gains faster when the streak breaks | Keep sizing constant |
| Sizing down after outcome setbacks | Reduces recovery speed when edge reasserts | Keep sizing constant (unless risk appetite is "low") |
| Skipping daily reviews | Behavioral drift goes undetected for days | Daily reviews are non-negotiable |
| Paper decision-making with different sizing | Paper P&L doesn't reflect real execution | Same sizing rules for paper and live |
