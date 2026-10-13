from __future__ import annotations
from datetime import datetime, timezone
from .models import Opportunity
from .scoring import score_opportunity

def rank(opportunities: list[Opportunity], now: datetime | None = None) -> list[tuple[Opportunity, dict]]:
    scored = [(op, score_opportunity(op, now)) for op in opportunities]
    return sorted(scored, key=lambda pair: (-pair[1]["score"], pair[0].id))

def classify(score: int, evidence: int, reachability: int) -> str:
    if score >= 105 and evidence >= 4 and reachability >= 4:
        return "DO NOW"
    if score >= 78 and evidence >= 3:
        return "VALIDATE"
    return "WATCH"

def build_board(opportunities: list[Opportunity], generated_at: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    ranked = rank(opportunities, now)
    buckets = {"DO NOW": [], "VALIDATE": [], "WATCH": []}
    for op, score in ranked:
        bucket = classify(int(score["score"]), int(score["evidence_strength"]), op.reachability)
        if len(buckets[bucket]) < {"DO NOW": 3, "VALIDATE": 3, "WATCH": 5}[bucket]:
            buckets[bucket].append((op, score))
    generated_at = generated_at or now.isoformat()
    lines = [
        "# TODAY MONEY BOARD", "",
        f"Generated: {generated_at}", "",
        "Scoring: payment/evidence, reachability, urgency, fit, repeatability, competition gap, freshness and confidence; stale information edges are penalized.", "",
    ]
    for bucket in ("DO NOW", "VALIDATE", "WATCH"):
        lines += [f"## {bucket}", ""]
        if not buckets[bucket]:
            lines += ["_None._", ""]
            continue
        for index, (op, score) in enumerate(buckets[bucket], 1):
            lines += [
                f"### {index}. {op.title} ({op.id}) — score {score['score']}",
                f"- Route(s): {', '.join(op.routes)}",
                f"- Buyer/problem: {op.problem}",
                f"- Source: [{op.source_platform}]({op.source_url}) (published {op.published_at}; observed {op.observed_at})",
                f"- Evidence: “{op.evidence_text}”",
                f"- Why payment is plausible: {op.payment_intent_evidence}",
                f"- Reach / validation: {op.contact_path}; next action: {op.suggested_next_action}",
                f"- Suggested offer: {op.suggested_offer}",
                f"- Effort / risk: {op.estimated_effort}; {op.risk}",
                f"- Why this rank: evidence strength {score['evidence_strength']}/5, freshness {score['freshness']}/5, reachability {op.reachability}/5. It outranks lower items because it has a clearer buyer request and a nearer validation step.",
                "",
            ]
    lines += [
        "## Outcome feedback", "",
        "Append contact, reply, qualification, quote, win/loss and revenue events to data/outcomes.jsonl; the next run can use these aggregates when prioritizing.", "",
    ]
    return "\n".join(lines)
