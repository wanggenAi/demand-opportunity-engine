from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .models import timestamp
from .scoring import score_opportunity
from .clusters import clusters, observation_eligible

CAPS = {"DO NOW": 5, "VALIDATE": 5, "WATCH": 50}

def rank(opportunities, now=None, events=()):
    scored = []
    cs = {c["cluster_name"]: c for c in clusters(opportunities)}
    for op in opportunities:
        score = score_opportunity(op, now, events, opportunities)
        c = cs.get(op.cluster_name)
        bonus = min(5, max(0, c["independent_demand_count"] - 1)) if c else 0
        score["components"]["repeatability"] = bonus
        score["score"] += bonus
        scored.append((op, score))
    return sorted(scored, key=lambda pair: (-pair[1]["score"], pair[0].id))

def classify(op, score):
    if score["source_age_days"] < 0:
        return "REJECTED"
    if "INFO_EDGE" in op.routes:
        if not score["info_edge_rejections"] and op.fulfillment_mode == "REMOTE_NOW":
            return "VALIDATE"
        return "WATCH" if 0 <= score["source_age_days"] <= 14 else "REJECTED"
    if not observation_eligible(op):
        return "REJECTED"
    if op.buyer_role != "BUYER" or op.commercial_intent_type == "NONE":
        return "REJECTED"  # Observers belong in PRODUCT_THESIS, never sales actions.
    if op.acquisition_cost == "REQUIRED_PAID":
        return "WATCH"  # Market intelligence only; never ask the human to buy access.
    if not score["do_now_rejections"] and score["score"] >= 65:
        return "DO NOW"
    # Current problem observations may be validated, but do not get an outreach recommendation.
    if score["source_age_days"] <= 14 and op.fulfillment_mode == "REMOTE_NOW" and score["score"] >= 40:
        return "VALIDATE"
    return "WATCH"

def selections(opportunities, now=None, events=()):
    buckets = {key: [] for key in CAPS}
    rejected = []
    for op, score in rank(opportunities, now, events):
        section = classify(op, score)
        if section == "REJECTED":
            rejected.append((op, score))
        elif len(buckets[section]) < CAPS[section]:
            buckets[section].append((op, score))
    return buckets, rejected

def build_board(opportunities, generated_at=None, events=()):
    now = timestamp(generated_at) if generated_at else datetime.now(timezone.utc)
    buckets, rejected = selections(opportunities, now, events)
    lines = [
        "# TODAY MONEY BOARD", "",
        f"Generated: {now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat()} (Asia/Shanghai)", "",
        "Current acquisition budget = 0. Only evidenced ZERO-cost contact can enter DO NOW / PRIMARY OUTREACH. Paid application channels are not primary execution channels.",
        "Decision rule: 0–7-day buyer demand first. 7–14-day demand is VALIDATE without renewed buyer activity. Older leads require verified OP activity <=7 days. Payment must be buyer-authored; unknown/high competition and uncontrolled fulfillment block DO NOW.",
        "Amounts below are suggested test prices, never observed buyer budgets. VALIDATE means confirm need/payment first; it does not authorize pitching bug reporters.",
        f"Live store: {len(opportunities)} observations; {len(rejected)} seller/news/pain-only/unqualified records excluded from sales. V1 seeds excluded.", "",
    ]
    for section, entries in buckets.items():
        lines += [f"## {section}", ""]
        if not entries:
            lines += ["None. No candidate passed the hard gates; do not backfill with stale leads.", ""]
        for i, (op, score) in enumerate(entries, 1):
            lines += [
                f"### {i}. {op.title} ({op.id})", "",
                f"- Source URL: {op.source_url}",
                f"- published_at: {op.published_at}; last_activity_at: {op.last_activity_at or 'unknown'}",
                f"- Buyer activity: {op.buyer_activity_at or 'no verified buyer follow-up'}; source age {score['source_age_days']} days; buyer activity age {score['buyer_activity_age_days']}",
                f"- Buyer/problem: {op.buyer_id} ({op.buyer_role}); {op.derived_interpretation}",
                "- Exact evidence:\n\n> " + op.raw_evidence_quote.replace("\n", "\n> "),
                f"- Payment evidence: {score['payment_signal_type']} — {score['payment_evidence_quote'] or 'no verified willingness-to-pay statement'}",
                f"- Commercial intent: {op.commercial_intent_type} — {op.commercial_intent_quote or 'NONE'}",
                f"- Competition pressure: {op.competition_pressure}; comments={op.comment_count}, distinct service providers={op.seller_competition_count}, complete={op.comments_complete}; mature quote={op.mature_quote_present}; many DMs={op.many_dms_reported}; commodity market={op.commodity_market}",
                f"- Competition evidence: {', '.join(op.competition_evidence) or 'no service pitch detected in collected replies; off-platform DMs unknown'}",
                f"- Delivery capability: {op.fulfillment_mode}; dependencies: {'; '.join(op.required_capabilities) or 'remote only; access and exact scope still require consent'}",
                f"- Contact path: {op.contact_path or 'not verified'}; profile: {op.target_profile_url}",
                f"- acquisition_cost: {op.acquisition_cost}; evidence: {op.acquisition_cost_evidence or 'free contact not verified'}",
                f"- Contact channel/rules: {op.contact_channel}",
                f"- First message angle/draft (human review): {op.first_message}",
                f"- Suggested offer: {op.suggested_offer}",
                f"- Suggested price range: {op.suggested_price_range}",
                f"- Effort: {op.effort}; risk: {op.risk}",
                f"- Freshness / why now: {op.why_now or 'current change; target-buyer demand still unverified'}",
                f"- Why us: {op.differentiation or 'no verified advantage yet; measure before offering'}",
                f"- Grounded operator advantage: {op.operator_advantage}",
                f"- Observed source budget: {op.observed_budget or 'not stated/verified; proposed offer price is separate'}",
                f"- Score {score['score']}; components: {score['components']}",
                f"- Why this rank: deterministic component total, then ID for ties. Failed DO NOW gates: {'; '.join(score['do_now_rejections']) or 'none'}.",
                f"- Next action: {op.next_action}", "",
            ]
    lines += ["## Human action portfolio", ""]
    if buckets["DO NOW"]:
        for op, _ in buckets["DO NOW"]:
            lines += [f"CONTACT_TODAY: Contact {op.buyer_id} via {op.contact_path}. Test {op.suggested_offer}; {op.suggested_price_range}.", ""]
    elif buckets["VALIDATE"]:
        lines += ["No qualified ZERO-COST contact today. Use DAILY_MONEY_PORTFOLIO.md for bounded product/edge validations and real follow-ups. Do not buy application access or lower gates.", ""]
    else:
        lines += ["No verified buyer to contact today. Seek one current, buyer-authored paid request; do not spend human outreach time on stale/seller records.", ""]
    lines += ["## PRODUCT_SIGNAL tool decisions", "",
              "See TOOL_OPPORTUNITIES.md for BUILD NOW / VALIDATE / WATCH / REJECT and the twelve demand, competition, delivery and monetization checks. A keyword hypothesis is not measured traffic or payment evidence.", ""]
    lines += ["## Outcome feedback", "",
              f"Read {len(events)} append-only events from data/outcomes.jsonl. DISCOVERED has zero conversion weight; no invented contact/reply/win/revenue events.",
              "Scoring consumes platform, planned contact channel and cluster outcomes; details: OUTCOME_FEEDBACK.md.", ""]
    return "\n".join(line.rstrip() for line in "\n".join(lines).splitlines()) + "\n"
