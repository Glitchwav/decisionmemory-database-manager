# Before/After: The Difference Memory Makes

> **Note:** All data below is from a simulation (`demo.py`). These are projected improvements based on simulated decisions, not real decision-making results. Real performance data will be added as the project matures.

This document shows the difference between an AI decision agent **without** persistent memory versus **with** DecisionMemory Protocol, using 30 simulated XAUUSD decisions.

---

## Side-by-Side Comparison

### Decision 1 — First Decision

| Without DecisionMemory | With DecisionMemory |
|---|---|
| AI analyzes the chart and gives a recommendation based solely on current price action. | Same — no history yet, so behavior is identical. |
| **"XAUUSD showing bullish momentum above 2845. Recommend long, 0.05 lots."** | **"XAUUSD showing bullish momentum above 2845. Recommend long, 0.05 lots."** |

> No difference yet. Memory needs data to work with.

---

### Decision 5 — Early Pattern Emerges

| Without DecisionMemory | With DecisionMemory |
|---|---|
| AI starts fresh. No memory of Decisions 1-4. Analyzes the chart as if it's the first time. | AI recalls: 4 prior decisions — 3 Asian session outcome setbacks, 1 London win. |
| **"Asian session pullback setup. Recommend long, 0.05 lots."** | **"Warning: Past 4 decisions show 3 outcome setbacks in Asian session (75% outcome setback rate). Reducing lot size to 0.025."** |

> The agent with memory already starts protecting capital.

---

### Decision 10 — Pattern Confirmed

| Without DecisionMemory | With DecisionMemory |
|---|---|
| AI has analyzed 9 charts independently. Each one from scratch. No idea it has a 100% win rate in London. | AI has full context: London 5W/0L (100% WR), Asian 1W/4L (20% WR). |
| **"London breakout forming. Standard lot size 0.05."** | **"London VolBreakout: 5/5 wins, avg +2.1R. High-confidence setup. Increasing lot to 0.08."** |

> Same decision context signal, completely different position sizing.

---

### Decision 20 — Strategy Divergence

| Without DecisionMemory | With DecisionMemory |
|---|---|
| AI continues making the same errors. Takes full-size positions in weak sessions. No learning from past outcome setbacks. | Reflection engine has run. Identified 6 patterns. 3 strategy adjustments active. |
| **"Asian session setup. 0.05 lots."** (proceeds to lose again) | **"Asian session — auto-reduced to 0.025 lots (risk constraint active). Confidence 0.50 is below threshold 0.55 — SKIP this decision."** |

> The memory-equipped agent actively avoids a losing decision.

---

### Decision 30 — Accumulated Wisdom

| Without DecisionMemory | With DecisionMemory |
|---|---|
| 30 independent analyses. Same mistakes repeated throughout. No concept of "my win rate" or "my best session". | Full decision memory loaded. Agent knows its strengths and weaknesses. |
| **"Here's my analysis of the current chart..."** (generic, stateless) | **"Session performance: London 100% WR → full size. Asian 10% WR → half size or skip. VolBreakout avg +1.44R → preferred strategy. Pullback avg +0.23R → secondary. Min confidence: 0.55."** |

> After 30 decisions, one agent learned nothing. The other built a personalized strategy.

---

## Quantified Impact

Based on 30-decision XAUUSD simulation:

| Metric | Without DecisionMemory | With DecisionMemory | Improvement |
|--------|-------------------|------------------|-------------|
| Overall Win Rate | 63% | 67%+ (projected) | +4% |
| Asian Session Outcome Setbacks | $-156.00 | $-78.00 (est.) | **-50%** |
| London Session Capture | Standard sizing | +60% position size | **+60% upside** |
| Low-Confidence Decisions Taken | 7 decisions (all outcome setbacks) | 0 decisions (filtered) | **7 losing decisions avoided** |
| Net P&L (30 decisions) | $+499.50 | $+650+ (projected) | **+30%** |
| Max Drawdown | Uncontrolled | Bounded by session rules | Reduced |

### Key Improvements

1. **Asian session outcome setbacks reduced 50%** — Auto position sizing based on poor win rate
2. **London breakout capture improved 60%** — Earned larger lot size from track record
3. **7 low-confidence losing decisions eliminated** — Confidence threshold auto-raised to 0.55
4. **Cross-session learning** — Patterns persist across restarts, no knowledge lost

---

## How It Works

```
Decision 1-3:   Record decisions + outcomes → L1 (Hot Memory)
                    ↓
Decision 3:     Reflection engine runs → Discovers patterns → L2 (Warm Memory)
                    ↓
Decision 4+:    Agent loads state → Checks constraints → Adjusts behavior
                    ↓
Decision 10+:   Enough data → Strategy adjustments generated → L3 (Cold Archive)
                    ↓
Decision 30:    Agent has personalized, data-driven decision-making strategy
```

---

## Try It Yourself

```bash
python scripts/demo.py
```

No API key needed. See the full L1 → L2 → L3 pipeline in under 2 minutes.

---

## 中文摘要

### 前後對比：記憶帶來的差異

| 階段 | 沒有記憶 | 有記憶 |
|------|---------|--------|
| 第 1 筆 | 正常分析，沒有差別 | 一樣 |
| 第 5 筆 | 從零開始分析，不記得前 4 筆 | 「過去 4 筆亞洲盤交易，3 筆虧損。倉位減半。」 |
| 第 10 筆 | 不知道倫敦盤勝率 100% | 「倫敦突破 5/5 全勝，加倉到 0.08。」 |
| 第 20 筆 | 繼續在弱勢時段全倉交易 | 「亞洲盤信心度 0.50 低於門檻 0.55 — 跳過。」 |
| 第 30 筆 | 重複犯錯，沒學到東西 | 完整策略：依時段調倉位、過濾低信心交易 |

### 量化改善

- 亞洲盤虧損減少 **50%**
- 倫敦盤倉位提升 **60%**
- 避開 **7 筆** 注定虧損的低信心交易
- 整體淨利潤提升約 **30%**

---

Built with [DecisionMemory Protocol](https://github.com/mnemox-ai/decisionmemory-protocol) by [Mnemox](https://mnemox.ai).
