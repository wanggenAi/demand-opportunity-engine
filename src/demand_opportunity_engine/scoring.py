from __future__ import annotations
from datetime import datetime, timezone
from .models import Opportunity

WEIGHTS = {
    "payment": 5, "reachability": 4, "urgency": 3, "operator_fit": 3,
    "evidence": 4, "repeatability": 2, "competition_gap": 2,
    "decay": 2, "confidence": 2,
}

def evidence_strength(opportunity: Opportunity) -> int:
    text = (opportunity.payment_intent_evidence + " " + opportunity.evidence_text).lower()
    if any(token in text for token in ("budget", "$", "pay", "fee", "commission", "quoted", "hire", "paid")):
        return 5
    if any(token in text for token in ("looking for", "need", "require", "seeking", "help me", "requests", "wants", "want")):
        return 4
    if any(token in text for token in ("bottleneck", "manual", "repeated", "time-consuming")):
        return 3
    if any(token in text for token in ("search", "research", "trend")):
        return 2
    return 1

def freshness_score(observed_at: str, decay_risk: int, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    age_days = max(0, (now - observed).days)
    return max(0, 5 - min(5, age_days // max(1, 8 - decay_risk)))

def score_opportunity(opportunity: Opportunity, now: datetime | None = None) -> dict[str, int]:
    opportunity.validate()
    evidence = evidence_strength(opportunity)
    freshness = freshness_score(opportunity.published_at, opportunity.information_decay_risk, now)
    raw = (
        opportunity.payment_intent_evidence.lower().count("explicit") * 2
        + WEIGHTS["payment"] * min(5, evidence)
        + WEIGHTS["reachability"] * opportunity.reachability
        + WEIGHTS["urgency"] * opportunity.urgency
        + WEIGHTS["operator_fit"] * opportunity.operator_fit
        + WEIGHTS["evidence"] * evidence
        + WEIGHTS["repeatability"] * opportunity.repeatability
        + WEIGHTS["competition_gap"] * opportunity.competition_gap
        + WEIGHTS["decay"] * freshness
        + WEIGHTS["confidence"] * opportunity.confidence
        - WEIGHTS["decay"] * opportunity.information_decay_risk
    )
    return {"score": raw, "evidence_strength": evidence, "freshness": freshness}
