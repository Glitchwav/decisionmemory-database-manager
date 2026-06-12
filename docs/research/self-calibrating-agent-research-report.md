# Self-Calibrating Decision Agent — Research Report

> Author: Sean Peng (Mnemox AI) | Date: 2026-04-09
> Status: Phase 4 complete, critical decision point

---

## 1. What We're Trying to Build

A decision AI agent that knows when it's making mistakes — not by predicting the decision context, but by detecting when its own behavior has drifted from what historically works.

The core insight comes from poker: the best poker players don't just play good hands — they have systems to detect when they're tilting, when they're deviating from optimal play, and when they should stop. No equivalent exists for AI decision agents.

### The Problem We're Solving

Every AI decision agent today has amnesia. Each session starts fresh. It repeats the same mistakes. It can't detect that its strategy stopped working 50 decisions ago. It doesn't know its own behavioral patterns.

The specific failure modes:
1. **Strategy decay** — a strategy that worked in trending decision contexts keeps decision-making in ranging decision contexts
2. **Behavioral drift** — the agent starts cutting winners early or holding losers too long
3. **Tilt** — after consecutive outcome setbacks, the agent either over-decisions or freezes
4. **No self-awareness** — the agent can't answer "am I performing normally right now?"

### What Already Exists (Competitors)

| System | What It Does | What It Lacks |
|--------|-------------|---------------|
| FinMem (ICLR 2024, 870 stars) | LLM decision agent with 3-layer memory | No behavioral detection, no statistical validation, linear scoring (weaker than our multiplicative OWM) |
| ATLAS (arXiv 2026) | Multi-agent LLM decision-making with adaptive prompt optimization | No persistent memory, no behavioral detection. Key finding: reflection-based feedback FAILS — agents that self-reflect perform WORSE |
| Decision-MakingAgents (48K stars) | Multi-agent research framework | Academic only, no persistent memory |
| Decision-MakerSync ($30/mo) | Manual decision journaling | Passive — records but doesn't intervene. No AI. |
| freqdecision (48K stars) | Automated crypto decision-making | No memory, no self-calibration, no behavioral analysis |

**Gap**: Nobody detects agent behavioral drift. All existing systems monitor the decision context — none monitor the agent itself.

---

## 2. What We Built

### 2.1 DecisionMemory Protocol (Foundation — already shipped)

Open source MCP server. 17 tools, 1360+ tests, PyPI published.

**5-layer cognitive memory** (based on Tulving 1972):
- **Episodic**: raw decision records with full context
- **Semantic**: Bayesian beliefs about strategy performance (Beta-Binomial conjugate prior)
- **Procedural**: behavioral patterns (hold times, position sizing, disposition ratio)
- **Affective**: emotional state (confidence EWMA, drawdown, win/outcome setback streaks)
- **Prospective**: pre-planned rules ("if X then do Y")

**OWM (Outcome-Weighted Memory)** scoring for recall:
- Formula: `Score = Q × Sim × Rec × Conf × Aff`
- Multiplicative (not additive like FinMem) — any zero dimension kills the score
- 5 factors: outcome quality (sigmoid), context similarity (Gaussian kernel), recency (power-law decay), confidence, affective modulation
- Grounded in cognitive science (Tulving 1972) and reinforcement learning (Schaul et al. 2015 prioritized experience replay)

**Layers interconnect** (built in this sprint):
- Semantic reads Episodic: drift detection when recent 20 decisions diverge >15% from Bayesian posterior
- Procedural tracks: hold time, Kelly fraction, disposition ratio
- Affective reads Procedural: if disposition ratio > 2.0, auto-reduce risk appetite

### 2.2 Bayesian Changepoint Detection (Phase 1 — new)

Adams & MacKay 2007 algorithm applied to **agent behavioral sequences** (novel application — existing literature only applies this to decision context regime changes).

Monitors 4 behavioral signals:
- Win/outcome setback (Beta-Bernoulli conjugate model)
- outcome quality / pnl_r (Normal-Inverse-Gamma conjugate model)
- Hold duration (Normal-Inverse-Gamma)
- Position size vs Kelly (Normal-Inverse-Gamma)

Output: probability distribution over "how long since the last behavioral changepoint."

CUSUM complementary detector added for gradual shifts (BOCPD is weak on gradual drift).

### 2.3 Decision Quality Score / DQS (Phase 2 — new)

5-factor pre-decision scoring (0-10):
1. Regime Match — strategy historical win rate in current regime vs overall
2. Position Sizing — proposed lot vs Kelly suggestion
3. Process Adherence — OWM similarity to past successful decisions
4. Risk State — drawdown, consecutive outcome setbacks, confidence level
5. Historical Pattern — average pnl_r of similar past decisions

Adaptive thresholds from IS data distribution:
- skip = mean - 2*std (~worst 2.5% of decisions)
- caution = mean - 1*std (~worst 16%)
- go = everything above (default: decision normally)

`calibrate()` method: logistic regression on historical DQS factors vs win/outcome setback outcomes to learn optimal weights. Pure Python, no external dependencies.

### 2.4 Simulation Framework (Phase 3 — new)

Agent A (baseline) vs Agent B (self-calibrating) controlled experiment:
- Same strategy, same context data, same initial capital
- Walk-forward: 67% IS (training) / 33% OOS (evaluation)
- Warm-start: Agent B seeded with Agent A's IS decisions (simulates "turning on calibration after decision-making history exists")
- 4-variant ablation: remove DQS / changepoint / Kelly / regime filter one at a time
- 3 preset strategies: TrendFollow, Breakout, MeanReversion
- Metrics: Sharpe ratio, score-adjusted outcome (lot-weighted), score max drawdown, Calmar ratio, DQS-outcome correlation, Welch's t-test

---

## 3. Experiment Results

### 3.1 Phase 4a — First Run (FAILED)

12 experiments: BTCUSDT + ETHUSDT × 1h + 4h × 3 strategies.

**Result**: 11/12 Agent A = Agent B (identical). 1/12 Agent B skipped ALL decisions (Sharpe → 0).

**Root causes found**:
1. Cold-start: Agent B had empty DB → DQS returned neutral scores for everything → no calibration effect
2. CUSUM threshold hardcoded at target_wr=0.5 → 100% alert rate on 10/12 experiments (useless)
3. Sharpe ratio is invariant to position sizing (ratio metric) → couldn't measure lot adjustments
4. Max drawdown calculated incorrectly (showing >100%)

### 3.2 Phase 4b — With Fixes

**Fixes applied**:
1. Warm-start: seed Agent B's DB with Agent A's IS decisions
2. CUSUM: adaptive target_wr from observed win rate
3. Score-based metrics: lot-adjusted outcome and drawdown ($ not %)
4. Adaptive DQS thresholds from IS distribution

**Results on ETHUSDT 4h (positive Sharpe strategies)**:

| Strategy | Sharpe A | Sharpe B | Eq outcome A | Eq outcome B | Eq DD A | Eq DD B | DD Reduction | Skipped |
|----------|----------|----------|----------|----------|---------|---------|-------------|---------|
| TrendFollow | +6.77 | +6.77 | +2,210 | +1,867 | 1,175 | 1,288 | **-10%** (worse) | 0 |
| **Breakout** | **+6.16** | **+15.28** | +956 | +861 | **1,022** | **355** | **+65%** | 99 |
| MeanReversion | +9.91 | -30.53 | +779 | -114 | 310 | 129 | +58% (but outcome destroyed) | 81 |

**Breakout is the only genuinely positive result**: Sharpe 2.5x improvement, drawdown reduced 65%, outcome only decreased 10%. The system correctly identified and skipped 99 low-quality decision setups.

MeanReversion was over-filtered: skipped 81 decisions, only took 6, and those 6 happened to lose. The skip mechanism was too aggressive.

TrendFollow showed no difference: DQS never triggered any skip or reduction.

### 3.3 Critical Diagnostic — DQS Cannot Separate Winners from Losers

We ran a focused test: for each strategy, compute DQS retroactively on every OOS decision, then compare DQS scores for winning decisions vs losing decisions.

| Strategy | DQS Winners | DQS Losers | Separation |
|----------|------------|------------|------------|
| TrendFollow | 4.90 | 4.90 | 0.000 |
| Breakout | 6.16 | 6.16 | 0.000 |
| MeanReversion | 5.67 | 5.67 | 0.000 |

**DQS gives identical scores to winners and losers.** Zero separation across all strategies.

**Root cause**: DQS factors use session-level information (overall strategy win rate, overall Kelly, overall drawdown). Every decision from the same strategy in the same session sees the same history → gets the same score. DQS can distinguish between strategies (Breakout scores 6.16, TrendFollow scores 4.90) but cannot distinguish between good and bad decisions within the same strategy.

---

## 4. What Works and What Doesn't

### Confirmed Working
- **OWM multiplicative recall** — theoretically superior to FinMem's linear scoring, 1360+ tests
- **Bayesian Changepoint Detection on agent behavior** — novel application, detects sharp behavioral shifts
- **Strategy-level health monitoring** — the system CAN detect when a strategy is degrading overall
- **Drawdown reduction via changepoint** — Breakout showed 65% DD reduction when changepoint + CUSUM triggered position reduction
- **Memory layer interconnection** — Semantic ↔ Episodic drift, Procedural → Affective risk adjustment

### Not Working
- **Decision-level DQS** — cannot distinguish good from bad individual decisions (separation = 0)
- **CUSUM on stable strategies** — still alerts too frequently on some configurations
- **Generalization** — results inconsistent across 3 strategies (1 improved, 1 damaged, 1 unchanged)

### Unknown
- Whether the Breakout result is robust or an artifact of this specific data window
- Whether DQS with bar-level features could achieve decision-level separation
- Whether the approach works in non-crypto decision contexts (forex, records)

---

## 5. The Decision Point

### Option A: Strategy-Level Calibration (Pivot DQS to session-level)

Accept that DQS works at the strategy level, not decision level. Redesign it as a "strategy health dashboard" — not "should I take this decision" but "should I be decision-making this strategy right now."

This is closer to the original DecisionMemory positioning: a discipline system that warns when a strategy is decaying.

**Pros**: Honest, achievable, aligns with what the data shows
**Cons**: Less exciting product story, harder to differentiate from a simple moving-average-of-win-rate

### Option B: Decision-Level Feature Engineering

Make DQS work at the decision level by adding bar-specific features: local volatility patterns, volume anomalies, price action relative to recent bars. This would give each decision a unique context fingerprint.

**Pros**: If it works, genuinely novel — a pre-decision quality check that actually predicts outcomes
**Cons**: Becomes indistinguishable from "building a better strategy." May require ML (neural nets) not just statistics. Months of research with uncertain outcome.

### Option C: Focus on Changepoint Detection (Strongest Result)

Double down on the one thing that clearly works: behavioral changepoint detection for position sizing. The Breakout DD -65% result came from changepoint, not from DQS.

Publish a paper specifically on "Bayesian Changepoint Detection for Agent Behavioral Drift" — this IS novel (no prior work applies BOCPD to agent behavior rather than decision context regime).

**Pros**: Clear result, publishable, differentiable
**Cons**: Narrow scope — position sizing adjustment only, not a full "decision quality" system

### Option D: Hybrid (A + C)

Strategy-level health monitoring (A) + changepoint-based position adjustment (C). Drop decision-level DQS claims.

Product narrative: "DecisionMemory monitors your decision agent's behavioral health. When it detects degradation, it automatically reduces position sizes to protect capital. Like a circuit breaker, but intelligent."

**Pros**: Honest, supported by data, combines two working systems
**Cons**: Less ambitious than the original "Decision Quality Score" vision

---

## 6. Technical Depth Assessment

### What's Research-Grade
- OWM 5-factor multiplicative recall (original design, beats FinMem's linear approach)
- Bayesian Online Changepoint Detection on agent behavior (novel application of Adams & MacKay 2007)
- CUSUM complementary detection for gradual shifts
- DSR (Deflated Sharpe Ratio) integration from Bailey-de Prado 2014
- Walk-forward experimental methodology with warm-start

### What Needs Depth for Funding / Paper
- No formal POMDP framework (discussed but not implemented)
- No regret bounds (mathematical guarantee on max outcome setback)
- Changepoint detection uses default priors (not domain-optimized)
- No cross-decision context validation (crypto only)
- Only 1/3 strategies showed positive results
- Need ablation study specifically on changepoint component (not DQS)

### What an Investor Would Ask
1. "What's your moat?" → The combination of persistent memory + behavioral changepoint is unique. But the individual components are reproducible in 2-3 weeks.
2. "Show me the data." → Breakout: Sharpe 6→15, DD -65%. But only 1/3 strategies. Need more experiments.
3. "What's the path to revenue?" → Strategy-level monitoring as SaaS ($29/mo) or consulting service ($2K-5K/engagement). First paying user (Hevin) confirmed "her decision-making improved."

---

## 7. Codebase Status

| Component | Files | Tests | Status |
|-----------|-------|-------|--------|
| OWM Core | 11 files in `owm/` | 1360+ total | Production-ready |
| Changepoint | `owm/changepoint.py` | 8 tests | Working, needs prior tuning |
| DQS | `owm/dqs.py` | 10 tests | Strategy-level OK, decision-level FAILS |
| Simulation | 6 files in `simulation/` | 10 tests | Working, needs more strategies |
| ADR | 4 docs in `docs/adr/` | — | Complete |
| OWM Article | `docs/research/owm-technical-article.md` | — | Draft complete |

Git: 17 commits in this sprint, all on master, pushed.

---

## 8. Questions I Need Help Answering

1. **Is Option D (Strategy Health + Changepoint) a strong enough product thesis?** Or does the decision context need decision-level decision quality to care?

2. **Is 1/3 strategy positive result enough to publish?** Academic papers often show mixed results honestly. But is it enough for a startup?

3. **Should we pursue decision-level feature engineering (Option B)?** This is the highest-risk, highest-reward path. It could take months and may not work. But if it does, it's genuinely novel.

4. **Is there a way to make DQS work at decision level without building a strategy?** The fundamental challenge: any feature that predicts individual decision outcomes IS a decision-making signal. Is there a middle ground?

5. **For fundraising: is the research approach (paper + experiments) the right path? Or should we focus on building a polished product with Hevin's testimonial?** These are different paths with different timelines.
