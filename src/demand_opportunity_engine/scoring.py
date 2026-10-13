from datetime import datetime, timezone
import re
from urllib.parse import urlparse
from .models import age, https
from .signals import payment_truth, commercial_truth
from .feedback import feedback_adjustment

def source_age(op, now):
    return age(op.published_at, now)

def verified_activity_age(op, now):
    if not (op.buyer_activity_verified and op.buyer_activity_author_id == op.buyer_id
            and https(op.buyer_activity_url) and op.buyer_activity_quote):
        return None
    return age(op.buyer_activity_at, now)

def edge_rejections(op, now):
    edge = op.info_edge
    reasons = []
    a = source_age(op, now)
    if a is None or not 0 <= a <= 14:
        reasons.append("INFO_EDGE event is outside 14-day window")
    sources = edge.get("verification_sources", [])
    domains = {urlparse(s["url"]).netloc for s in sources
               if s.get("verified") and s.get("quote") and s.get("independent")}
    if len(domains) < 2:
        reasons.append("fewer than two independent verified evidence points")
    for key in ("novelty", "information_gap", "monetization_path", "target_buyer", "decay_window", "legality_check"):
        if not edge.get(key):
            reasons.append(f"missing {key}")
    if not edge.get("gap_verified"):
        reasons.append("target-buyer information gap remains unverified")
    return reasons

def do_now_rejections(op, now):
    reasons = []
    a = source_age(op, now)
    activity = verified_activity_age(op, now)
    if not op.source_verified:
        reasons.append("source not verified")
    observed_age = age(op.observed_at, now)
    if observed_age < 0 or observed_age > 7:
        reasons.append("source verification is future-dated or older than 7 days")
    if op.buyer_role != "BUYER":
        reasons.append("not a verified buyer request")
    intent, quote = commercial_truth(op)
    if (op.commercial_intent_type == "NONE" or intent != op.commercial_intent_type
            or not op.commercial_intent_quote or op.commercial_intent_quote != quote):
        reasons.append("commercial-intent gate failed: NONE or unsupported primary quote/type")
    if not https(op.contact_path):
        reasons.append("missing legitimate source contact/application path")
    if not op.source_open:
        reasons.append("source closed/removed")
    if not https(op.target_profile_url) or not op.buyer_id:
        reasons.append("missing concrete target profile")
    if a is None or a < 0 or (a > 14 and not (activity is not None and 0 <= activity <= 7)):
        reasons.append("freshness gate failed: >14 days without verified buyer activity <=7 days")
    if a is not None and 7 < a <= 14 and not (activity is not None and 0 <= activity <= 7):
        reasons.append("7–14-day demand is VALIDATE until buyer activity is renewed")
    if op.fulfillment_mode != "REMOTE_NOW":
        reasons.append("partner/specialist capability not currently controlled")
    if op.competition_pressure in {"HIGH", "UNKNOWN"}:
        reasons.append("competition high or unmeasured")
    kind, _, _ = payment_truth(op)
    if kind == "INFERRED":
        reasons.append("payment intent not verified in buyer's primary words")
    if not all((op.suggested_offer, op.suggested_price_range, op.first_message, op.differentiation, op.next_action)):
        reasons.append("incomplete actionable offer")
    if "INFO_EDGE" in op.routes:
        reasons.extend(edge_rejections(op, now))
    return reasons

def score_opportunity(op, now=None, events=(), opportunities=()):
    op.validate()
    now = now or datetime.now(timezone.utc)
    a = source_age(op, now)
    activity = verified_activity_age(op, now)
    effective = min(a, activity) if activity is not None and 0 <= activity <= 7 else a
    payment_type, payment_quote, payment = payment_truth(op)
    # Components are separate. One payment signal is counted once.
    budget = re.search(r"[$€£]\s*\[?(\d+(?:[,.]\d+)?)", payment_quote) if payment_type == "EXPLICIT_BUDGET" else None
    ticket = min(5, int(float(budget[1].replace(",", "")) / 100)) if budget else 0
    components = {
        "source_authenticity": 15 if op.source_verified and op.raw_evidence_quote in op.source_text else 0,
        "payment_intent": payment,
        "urgency": 5 if re.search(r"\bdeadline\b|\basap\b|\burgent\b", op.source_text, re.I) else 0,
        "reachability": 10 if https(op.target_profile_url) and op.buyer_id else 0,
        "freshness": 18 if 0 <= effective <= 3 else (15 if 3 < effective <= 7 else (7 if 7 < effective <= 14 else 0)),
        "capability": {"REMOTE_NOW": 15, "PARTNER_REQUIRED": 3, "LOCAL_PHYSICAL": 0, "SPECIALIST_REQUIRED": -8}[op.fulfillment_mode],
        "competition": {"LOW": 0, "MEDIUM": -8, "HIGH": -20, "UNKNOWN": -12}[op.competition_pressure],
        "commodity_risk": -4 if op.commodity_market else 0,
        "expected_ticket": ticket,  # primary buyer budget only; NEVER proposal price
        "measurable_cost": 4 if re.search(r"(?:unnoticed|not processed|lost|blocked).{0,80}\d+ (?:days|hours)|\d+ (?:hours|days).{0,80}(?:not processed|manual|lost)", op.source_text, re.I | re.S) else 0,
        "repeatability": 0,  # populated only by verified independent clusters
        "confidence": min(op.confidence, 5),
    }
    events = [e for e in events if age(e.occurred_at, now) >= 0]
    feedback, groups = feedback_adjustment(op, events, opportunities)
    components["outcome_feedback"] = feedback
    closed = any(e.opportunity_id == op.id and e.event_type in {"WON", "LOST"} for e in events)
    contacted = any(e.opportunity_id == op.id and e.event_type == "CONTACTED" for e in events)
    reasons = do_now_rejections(op, now)
    if closed or contacted:
        reasons.append("already contacted or closed: use outcome follow-up")
    return {
        "score": round(sum(components.values()), 2), "components": components,
        "payment_signal_type": payment_type, "payment_evidence_quote": payment_quote,
        "source_age_days": round(a, 2), "buyer_activity_age_days": round(activity, 2) if activity is not None else None,
        "do_now_rejections": reasons, "feedback_groups": groups,
        "info_edge_rejections": edge_rejections(op, now) if "INFO_EDGE" in op.routes else [],
        "evidence_strength": 5 if op.source_verified else 0,
    }
