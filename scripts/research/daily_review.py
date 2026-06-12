"""
Daily Review — AI-powered decision review with OWM hybrid retrieval.

Closes the feedback loop: MT5 decisions → decisionmemory DB → OWM recall → Sonnet review → reflection stored back.

Usage:
    python scripts/research/daily_review.py                  # Review today's decisions
    python scripts/research/daily_review.py --date 2026-03-10  # Specific date
    python scripts/research/daily_review.py --days 3           # Last 3 days
    python scripts/research/daily_review.py --strategy VolBreakout  # Filter by strategy

Requires:
    - decisionmemory.db with episodic_memory populated (via mt5_sync)
    - ANTHROPIC_API_KEY in .env
    - Optional: DISCORD_WEBHOOK_URL for notifications
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Reconfigure stdout for Windows UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Setup paths — ensure decisionmemory package is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

load_dotenv(PROJECT_ROOT / ".env", override=True)

from decisionmemory.db import Database
from decisionmemory.owm import ContextVector, outcome_weighted_recall

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DB_PATH = os.getenv("DECISIONMEMORY_DB", str(PROJECT_ROOT / "data" / "decisionmemory.db"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
OUTPUT_DIR = PROJECT_ROOT / "data" / "daily_reviews"

# BATCH-001 baselines (from MEMORY.md)
STRATEGY_BASELINES = {
    "VolBreakout":       {"win_rate": 0.55, "avg_pf": 1.17, "avg_pnl_pct": 29.2},
    "IntradayMomentum":  {"win_rate": 0.58, "avg_pf": 1.78, "avg_pnl_pct": 47.0},
    "Pullback":          {"win_rate": 0.52, "avg_pf": 1.45, "avg_pnl_pct": 40.9},
}


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ---------------------------------------------------------------------------
# Step 1+2: Query today's closed decisions from episodic_memory
# ---------------------------------------------------------------------------
def get_decisions_for_date(
    db: Database,
    target_date: date,
    days: int = 1,
    strategy: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Query episodic_memory for closed decisions within the date range."""
    conn = db._get_connection()
    try:
        start = datetime(target_date.year, target_date.month, target_date.day,
                         tzinfo=timezone.utc)
        end = start + timedelta(days=days)

        query = """
            SELECT * FROM episodic_memory
            WHERE timestamp >= ? AND timestamp < ?
            AND exit_price IS NOT NULL
            AND pnl IS NOT NULL
        """
        params: list = [start.isoformat(), end.isoformat()]

        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)

        query += " ORDER BY timestamp ASC"
        rows = conn.execute(query, params).fetchall()

        results = []
        for row in rows:
            d = dict(row)
            d['context_json'] = json.loads(d['context_json']) if d['context_json'] else {}
            d['tags'] = json.loads(d['tags']) if d['tags'] else []
            results.append(d)

        return results
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Step 3: OWM Hybrid Recall — find similar historical decisions
# ---------------------------------------------------------------------------
def recall_similar(
    db: Database,
    decision: Dict[str, Any],
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Use OWM outcome_weighted_recall to find similar past decisions."""
    ctx = decision.get("context_json", {})

    query_context = ContextVector(
        symbol=ctx.get("symbol", decision.get("strategy", "")),
        price=decision.get("entry_price"),
        atr_d1=ctx.get("atr_d1"),
        atr_h1=ctx.get("atr_h1"),
        regime=decision.get("context_regime"),
        volatility_regime=decision.get("context_volatility_regime"),
        session=decision.get("context_session"),
    )

    # Get all episodic memories for this strategy (exclude the decision itself)
    all_memories = db.query_episodic(strategy=decision.get("strategy"), limit=200)
    candidates = [m for m in all_memories if m["id"] != decision["id"]]

    # Format for OWM: needs 'id', 'memory_type', 'timestamp', 'confidence', 'context', 'pnl_r'
    formatted = []
    for m in candidates:
        formatted.append({
            "id": m["id"],
            "memory_type": "episodic",
            "timestamp": m["timestamp"],
            "confidence": m.get("confidence", 0.5),
            "context": m.get("context_json", {}),
            "pnl_r": m.get("pnl_r"),
        })

    # Load affective state for modulation
    aff = db.load_affective() or {}
    aff_state = {
        "drawdown_state": aff.get("drawdown_state", 0.0),
        "consecutive_losses": aff.get("consecutive_losses", 0),
    }

    scored = outcome_weighted_recall(
        query_context=query_context,
        memories=formatted,
        affective_state=aff_state,
        limit=limit,
    )

    # Enrich with full data
    results = []
    for sm in scored:
        full = next((m for m in candidates if m["id"] == sm.memory_id), None)
        if full:
            results.append({
                "id": sm.memory_id,
                "score": round(sm.score, 4),
                "components": {k: round(v, 3) for k, v in sm.components.items()},
                "strategy": full.get("strategy"),
                "direction": full.get("direction"),
                "entry_price": full.get("entry_price"),
                "exit_price": full.get("exit_price"),
                "pnl": full.get("pnl"),
                "pnl_r": full.get("pnl_r"),
                "reflection": full.get("reflection"),
                "timestamp": full.get("timestamp"),
                "context_regime": full.get("context_regime"),
                "context_session": full.get("context_session"),
            })

    return results


# ---------------------------------------------------------------------------
# Step 4: Sonnet Review — AI-powered decision analysis
# ---------------------------------------------------------------------------
def build_review_prompt(
    decisions: List[Dict[str, Any]],
    similar_decisions: Dict[str, List[Dict[str, Any]]],
    target_date: date,
) -> str:
    """Build the prompt for Sonnet to review decisions."""
    lines = []
    lines.append(f"# Daily Decision Review — {target_date.isoformat()}")
    lines.append("")
    lines.append("You are a quantitative decision_making analyst reviewing today's closed decisions.")
    lines.append("For each decision, provide:")
    lines.append("1. **Grade** (A/B/C/D/F) — how well was the decision executed vs strategy rules?")
    lines.append("2. **What went right** — specific observations, not generic praise")
    lines.append("3. **What went wrong** — be direct, no sugar-coating")
    lines.append("4. **Pattern match** — compare with similar historical decisions (provided below)")
    lines.append("5. **Actionable lesson** — one concrete thing to remember for next time")
    lines.append("")
    lines.append("Context: XAUUSD gold decision_making on FXTM MT5. Strategies: VolBreakout (breakout), "
                 "IntradayMomentum (trend following), Pullback (pullback entry).")
    lines.append("")

    # Baselines
    lines.append("## Strategy Baselines (BATCH-001, 2024.01-2026.02)")
    for strat, bl in STRATEGY_BASELINES.items():
        lines.append(f"- {strat}: WR={bl['win_rate']:.0%}, PF={bl['avg_pf']:.2f}")
    lines.append("")

    # Today's decisions
    lines.append(f"## Today's Decisions ({len(decisions)} total)")
    lines.append("")

    total_pnl = 0.0
    for i, t in enumerate(decisions, 1):
        pnl = t.get("pnl", 0) or 0
        total_pnl += pnl
        emoji = "🟢" if pnl >= 0 else "🔴"

        lines.append(f"### Decision {i}: {t.get('strategy', '?')} {t.get('direction', '?').upper()} {emoji}")
        lines.append(f"- Entry: ${t.get('entry_price', 0):.2f} → Exit: ${t.get('exit_price', 0):.2f}")
        lines.append(f"- P&L: ${pnl:+.2f} | R-multiple: {t.get('pnl_r', 'N/A')}")

        hold_secs = t.get("hold_duration_seconds")
        if hold_secs:
            hold_min = hold_secs / 60
            lines.append(f"- Hold: {hold_min:.0f} min")

        lines.append(f"- Regime: {t.get('context_regime', 'N/A')} | Session: {t.get('context_session', 'N/A')}")

        if t.get("reflection"):
            lines.append(f"- Previous reflection: {t['reflection']}")
        lines.append("")

        # Similar historical decisions
        decision_id = t["id"]
        if decision_id in similar_decisions and similar_decisions[decision_id]:
            lines.append(f"**Similar historical decisions (OWM recall):**")
            for j, s in enumerate(similar_decisions[decision_id], 1):
                s_pnl = s.get("pnl", 0) or 0
                s_emoji = "🟢" if s_pnl >= 0 else "🔴"
                lines.append(
                    f"  {j}. [{s.get('timestamp', '?')[:10]}] {s.get('strategy')} "
                    f"{s.get('direction', '').upper()} ${s.get('entry_price', 0):.2f}→"
                    f"${s.get('exit_price', 0):.2f} P&L=${s_pnl:+.2f} {s_emoji} "
                    f"(OWM={s.get('score', 0):.3f})"
                )
                if s.get("reflection"):
                    lines.append(f"     Lesson: {s['reflection']}")
            lines.append("")

    lines.append(f"## Summary: {len(decisions)} decisions, total P&L: ${total_pnl:+.2f}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Now write your review. Use Markdown. Be specific and data-driven.")
    lines.append("End each decision review with a `**Reflection:**` line — this gets saved back to memory.")

    return "\n".join(lines)


def call_sonnet(prompt: str) -> Optional[str]:
    """Call Anthropic Sonnet API for decision review."""
    if not ANTHROPIC_API_KEY:
        log("ERROR: ANTHROPIC_API_KEY not set. Cannot call Sonnet.")
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    except ImportError:
        log("ERROR: anthropic package not installed. Run: pip install anthropic")
        return None
    except Exception as e:
        log(f"ERROR: Sonnet API call failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Step 5: Remember — write reflections back to episodic_memory
# ---------------------------------------------------------------------------
def extract_reflections(review_text: str, decisions: List[Dict[str, Any]]) -> Dict[str, str]:
    """Extract per-decision reflections from Sonnet's review.

    Looks for **Reflection:** lines and maps them to decision IDs by order.
    """
    reflections = {}
    import re

    # Find all reflection lines
    pattern = r'\*\*Reflection:\*\*\s*(.+?)(?:\n|$)'
    matches = re.findall(pattern, review_text, re.IGNORECASE)

    # Map by decision order
    for i, match in enumerate(matches):
        if i < len(decisions):
            reflections[decisions[i]["id"]] = match.strip()

    return reflections


def save_reflections(db: Database, reflections: Dict[str, str]):
    """Write reflections back to episodic_memory."""
    conn = db._get_connection()
    try:
        for decision_id, reflection in reflections.items():
            conn.execute(
                "UPDATE episodic_memory SET reflection = ? WHERE id = ?",
                (reflection, decision_id),
            )
        conn.commit()
        log(f"Saved {len(reflections)} reflections to episodic_memory")
    except Exception as e:
        log(f"ERROR saving reflections: {e}")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Step 6: Report — output markdown + optional Discord
# ---------------------------------------------------------------------------
def save_report(
    target_date: date,
    decisions: List[Dict[str, Any]],
    review_text: str,
    similar_decisions: Dict[str, List[Dict[str, Any]]],
):
    """Save markdown report to data/daily_reviews/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / f"{target_date.isoformat()}.md"

    total_pnl = sum((t.get("pnl") or 0) for t in decisions)
    wins = sum(1 for t in decisions if (t.get("pnl") or 0) > 0)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Daily Review — {target_date.isoformat()}\n\n")
        f.write(f"**Decisions:** {len(decisions)} | **Wins:** {wins} | **P&L:** ${total_pnl:+.2f}\n\n")
        f.write("---\n\n")
        f.write(review_text)
        f.write("\n\n---\n\n")
        f.write("## OWM Recall Summary\n\n")
        for decision_id, sims in similar_decisions.items():
            if sims:
                f.write(f"### {decision_id}\n")
                for s in sims:
                    f.write(
                        f"- {s['timestamp'][:10]} {s['strategy']} "
                        f"{s['direction']} P&L=${s.get('pnl', 0):+.2f} "
                        f"OWM={s['score']:.3f} "
                        f"(Q={s['components'].get('Q', 0):.2f} "
                        f"Sim={s['components'].get('Sim', 0):.2f} "
                        f"Rec={s['components'].get('Rec', 0):.2f})\n"
                    )
                f.write("\n")

        f.write(f"\n*Generated by daily_review.py at {datetime.now(timezone.utc).isoformat()}*\n")

    log(f"Report saved: {filepath}")
    return filepath


def send_discord(title: str, message: str, color: int = 0x9B59B6):
    """Send Discord notification. Silently fails if no webhook."""
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        import requests
        if len(message) > 4000:
            message = message[:3997] + "..."
        payload = {
            "embeds": [{
                "title": f"DecisionMemory — {title}",
                "description": message,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }]
        }
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Daily Decision Review with OWM + Sonnet")
    parser.add_argument("--date", type=str, help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--days", type=int, default=1, help="Number of days to review (default: 1)")
    parser.add_argument("--strategy", type=str, help="Filter by strategy name")
    parser.add_argument("--dry-run", action="store_true", help="Show prompt without calling Sonnet")
    parser.add_argument("--no-save", action="store_true", help="Don't save reflections back to DB")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else date.today()

    print("=" * 60)
    print("DecisionMemory Daily Review")
    print("=" * 60)
    print(f"Date: {target.isoformat()} ({args.days} day{'s' if args.days > 1 else ''})")
    print(f"DB: {DB_PATH}")
    if args.strategy:
        print(f"Strategy filter: {args.strategy}")
    print("=" * 60)
    print()

    # Init DB
    db = Database(DB_PATH)

    # Step 1+2: Get today's closed decisions
    log("Step 1: Querying decisions...")
    decisions = get_decisions_for_date(db, target, days=args.days, strategy=args.strategy)

    if not decisions:
        log(f"No closed decisions found for {target.isoformat()}. Nothing to review.")
        print("\n💤 No decisions today. EA is waiting for conditions.")
        return

    log(f"Found {len(decisions)} closed decision(s)")
    for t in decisions:
        pnl = t.get("pnl", 0) or 0
        log(f"  - {t['id']}: {t['strategy']} {t['direction']} P&L=${pnl:+.2f}")

    # Step 3: OWM Recall for each decision
    log("Step 2: OWM hybrid recall...")
    similar_decisions: Dict[str, List[Dict[str, Any]]] = {}
    for t in decisions:
        sims = recall_similar(db, t, limit=3)
        similar_decisions[t["id"]] = sims
        log(f"  - {t['id']}: {len(sims)} similar decisions recalled")

    # Step 4: Build prompt & call Sonnet
    log("Step 3: Building review prompt...")
    prompt = build_review_prompt(decisions, similar_decisions, target)

    if args.dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN — Prompt (not sent to Sonnet):")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        print(f"\nPrompt length: {len(prompt)} chars")
        return

    log("Step 4: Calling Sonnet for review...")
    review = call_sonnet(prompt)

    if not review:
        log("FAILED: Could not get Sonnet review. Aborting.")
        return

    log(f"Got review ({len(review)} chars)")

    # Step 5: Extract & save reflections
    if not args.no_save:
        log("Step 5: Extracting and saving reflections...")
        reflections = extract_reflections(review, decisions)
        if reflections:
            save_reflections(db, reflections)
        else:
            log("No reflections extracted (Sonnet may not have used the expected format)")
    else:
        log("Step 5: Skipped (--no-save)")

    # Step 6: Save report
    log("Step 6: Saving report...")
    filepath = save_report(target, decisions, review, similar_decisions)

    # Print review
    print("\n" + "=" * 60)
    print("DAILY REVIEW")
    print("=" * 60)
    print(review)
    print("=" * 60)

    # Discord notification
    total_pnl = sum((t.get("pnl") or 0) for t in decisions)
    wins = sum(1 for t in decisions if (t.get("pnl") or 0) > 0)
    emoji = "🟢" if total_pnl >= 0 else "🔴"
    send_discord(
        f"📝 Daily Review {target.isoformat()}",
        f"{emoji} **{len(decisions)} decisions** | Wins: {wins} | P&L: **${total_pnl:+.2f}**\n\n"
        f"Report: `data/daily_reviews/{target.isoformat()}.md`",
    )
    log("Done ✓")


if __name__ == "__main__":
    main()
