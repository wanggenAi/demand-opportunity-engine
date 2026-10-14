"""Daily small bets, using existing truth gates and real outcomes. No new sales score."""
from collections import defaultdict
from .board import rank, classify
from .clusters import clusters
from .feedback import grouped_metrics
from .models import age, timestamp
from .scoring import edge_rejections
from .signals import commercial_truth
from .action_reports import tool_decision

WIP = {"CONTACT_TODAY": 5, "FOLLOW_UP": 5, "VALIDATE_FIRST": 5,
       "PRODUCT_VALIDATIONS": 5, "PRESELL": 3, "INFO_EDGE_VALIDATIONS": 5,
       "QUOTED": 5, "ACTIVE_BUILDS": 2, "ACTIVE_DELIVERY": 3, "INFO_EXPLOIT": 3, "VALIDATE_TOTAL": 15}

PRODUCT_TASKS = {
    "workflow_reliability": "Select one execution-status failure in the primary evidence; write five diagnostic acceptance checks. Compare native logs/manual diagnosis with paid support prices. Ask what one failure costs, not whether someone likes a broad tool.",
    "lead_research": "Extract the required lead fields from the primary paid brief. Specify a 20-company research sample with evidence URLs and no spam/private data. Compare manual research with two public-priced alternatives; prepare one question about paying for the sample.",
    "marketing_report_automation": "Specify one weekly Meta Ads/Google Ads/GA4 spreadsheet and error alert, using the buyer's existing template. Compare native exports with public connector prices. Prepare a question about paying for this narrow pilot; no full marketing retainer or fabricated portfolio.",
    "voice_agent_qa": "Draft ten failure-path checks for one existing voice agent and one pass/fail report format. Compare manual QA with vendor test pricing. Prepare a paid-test question for consenting operators; no paid calls, credentials or new agent build.",
}


def priority(op, groups, repeat_count=1, human_minutes=10):
    """Relative allocation index. Unknown financial value stays null, not fake revenue."""
    keys = ("offer:" + op.suggested_offer, "cluster:" + op.cluster_name,
            "source:" + op.source_family, "platform:" + op.source_platform)
    chosen = {k: groups[k] for k in keys if k in groups and groups[k]["contacted"] >= 2}
    def mean(values):
        values = [v for v in values if v is not None]
        return sum(values) / len(values) if values else None
    ticket = mean(m["average_ticket_by_currency"].get("USD") for m in chosen.values())
    probability = mean((m["win_rate"] * m["contacted"] + 1) / (m["contacted"] + 2) for m in chosen.values())
    cycle = mean(m["average_cycle_days"] for m in chosen.values())
    advantages = op.operator_advantage
    advantage = max(({"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}.get(advantages.get(k), 0)
                     for k in ("china_local_advantage", "language_advantage", "technical_advantage")), default=0)
    competition = {"LOW": .2, "MEDIUM": .6, "HIGH": 2, "UNKNOWN": 1.5}[op.competition_pressure]
    risk = .5 if op.fulfillment_mode == "REMOTE_NOW" else 3
    # Neutral factors mean no historical financial claim. USD only; currencies never mixed.
    value_factor = min(5, max(.2, ticket / 100)) if ticket is not None else 1
    conversion_factor = probability * 2 if probability is not None else 1
    speed = 1 / (1 + cycle / 7) if cycle is not None else 1
    repeatability = 1 + min(4, max(0, repeat_count - 1)) / 4
    index = 100 * value_factor * conversion_factor * speed * (1 + advantage / 3) * repeatability / (human_minutes + risk + competition)
    return {"human_minutes_required": human_minutes, "cash_cost": 0 if op.acquisition_cost == "ZERO" else None,
            "speed_to_cash": {"observed_average_days": cycle, "basis": "real CONTACTED→WON cohort" if cycle is not None else "UNKNOWN; neutral factor"},
            "expected_value": {"currency": "USD", "amount": round(ticket * probability, 2) if ticket is not None else None,
                               "basis": "real realized ticket × smoothed cohort win rate" if ticket is not None else "UNKNOWN; no realized USD sales history"},
            "probability_of_conversion": probability, "structural_advantage": advantages,
            "repeatability": repeat_count, "portfolio_priority": round(index, 3),
            "priority_basis": "relative allocation index, not promised revenue; neutral financial factors without history",
            "learned_quote_ranges": {k: m.get("quoted_range_by_currency", {}) for k, m in chosen.items()},
            "consumed_outcome_cohorts": list(chosen)}  # Average overlapping cohorts; don't add the same success four times.


def daily_portfolio(opportunities, now, events=(), tool_candidates=(), state=None):
    state = state or {}
    events = [e for e in events if age(e.occurred_at, now) >= 0]
    index = {o.id: o for o in opportunities}
    history = defaultdict(list)
    for e in events:
        history[e.opportunity_id].append(e)
    groups = grouped_metrics(events, opportunities)
    cs = clusters([o for o in opportunities if "INFO_EDGE" not in o.routes])
    counts = {c["cluster_name"]: c["independent_demand_count"] for c in cs}
    p = {k: [] for k in ("CONTACT_TODAY", "FOLLOW_UP", "VALIDATE_FIRST", "SKIP", "PRODUCT_VALIDATIONS",
                        "PRODUCT_WATCH", "INFO_EDGE_VALIDATIONS", "INFO_EDGE_WATCH", "ACTIVE_BUILDS", "ACTIVE_DELIVERY")}
    quoted = 0
    for op, score in rank(opportunities, now, events):
        if "DIRECT_LEAD" not in op.routes or "INFO_EDGE" in op.routes:
            continue
        past = history[op.id]
        kinds = {e.event_type for e in past}
        if "CONTACTED" in kinds:
            if kinds & {"WON", "LOST"}:
                continue
            last = max((e for e in past if e.event_type != "DISCOVERED"), key=lambda e: timestamp(e.occurred_at))
            phase = next(k for k in ("QUOTED", "QUALIFIED", "REPLIED", "CONTACTED") if k in kinds)
            quoted += phase == "QUOTED"
            wait_days = 2 if phase in {"CONTACTED", "QUOTED"} else 1
            if age(last.occurred_at, now) >= wait_days:
                action = {"CONTACTED": "One polite scope/availability follow-up; honor opt-outs.",
                          "REPLIED": "Answer the buyer and confirm deliverable, budget and deadline.",
                          "QUALIFIED": "Prepare one fixed-scope quote and acceptance criteria.",
                          "QUOTED": "Ask whether the proposed scope/price fits; do not discount blindly."}[phase]
                p["FOLLOW_UP"].append({"id": op.id, "buyer": op.buyer_id, "source": op.source_url,
                                       "channel": last.channel, "phase": phase, "last_event_at": last.occurred_at,
                                       "next_action": action, "human_minutes_required": 10})
            continue
        if kinds & {"WON", "LOST"}:
            continue
        row = {"id": op.id, "title": op.title, "buyer": op.buyer_id, "source": op.source_url,
               "commercial_evidence": op.commercial_intent_quote, "payment_signal": score["payment_signal_type"],
               "payment_evidence": score["payment_evidence_quote"], "published_at": op.published_at,
               "buyer_activity_at": op.buyer_activity_at, "freshness_days": score["source_age_days"],
               "competition": op.competition_pressure, "competition_evidence": op.competition_evidence,
               "fit": op.fulfillment_mode, "offer": op.suggested_offer, "suggested_price": op.suggested_price_range,
               "observed_budget": op.observed_budget, "first_message_angle": op.first_message,
               "contact_channel": op.contact_channel, "contact_path": op.contact_path,
               "acquisition_cost": op.acquisition_cost, "risk": op.risk, "gate_failures": score["do_now_rejections"],
               **priority(op, groups, counts.get(op.cluster_name, 1))}
        if classify(op, score) == "DO NOW":
            p["CONTACT_TODAY"].append(row)
        elif (op.source_open and op.source_verified and op.buyer_role == "BUYER" and commercial_truth(op)[0] != "NONE"
              and 0 <= score["source_age_days"] <= 14 and op.fulfillment_mode == "REMOTE_NOW"
              and op.competition_pressure != "HIGH" and op.acquisition_cost != "REQUIRED_PAID"):
            # Desk verification only. Unknown contact/competition is never permission to pitch.
            row.update(priority(op, groups, counts.get(op.cluster_name, 1), human_minutes=20))
            row["next_action"] = "Desk-check the failed gates in 20 minutes; SKIP if unresolved. No sales message yet."
            p["VALIDATE_FIRST"].append(row)
        else:
            p["SKIP"].append(row)
    for key in ("CONTACT_TODAY", "VALIDATE_FIRST"):
        p[key].sort(key=lambda r: (-r["portfolio_priority"], r["id"]))
    p["FOLLOW_UP"].sort(key=lambda r: (r["last_event_at"], r["id"]))
    for c in cs:
        current = [o for o in opportunities if o.cluster_name == c["cluster_name"] and o.source_url in c["evidence_urls"]
                   and 0 <= age(o.published_at, now) <= 30]
        row = {**c, "build_status": "NO BUILD", "competitor_prices": "NOT VERIFIED",
               "monetization_hypothesis": "Fixed-price standardized research/diagnostic pilot only after demand confirmation.",
               "human_minutes_required": 30,
               "validation_task_today": PRODUCT_TASKS.get(c["cluster_name"], "Compare two public-priced alternatives; define one narrow deliverable and one consent-based interview question. Record unknowns, not assumed buyers."),
               "interview_presell_status": "No confirmed tester/preorder recorded"}
        if current and len(p["PRODUCT_VALIDATIONS"]) < WIP["PRODUCT_VALIDATIONS"]:
            p["PRODUCT_VALIDATIONS"].append(row)
        else:
            p["PRODUCT_WATCH"].append(row)
    for op in opportunities:
        if "INFO_EDGE" not in op.routes:
            continue
        e = op.info_edge
        reasons = edge_rejections(op, now)
        sources = e.get("verification_sources", [])
        row = {"id": op.id, "information_edge": op.title, "source": op.source_url,
               "event_date": op.published_at, "novelty": e.get("novelty"), "information_gap": e.get("information_gap"),
               "target_buyer": e.get("target_buyer"), "economic_value": "Potential cost/time savings; not yet measured in buyer workloads.",
               "monetization_route": e.get("monetization_path"), "expiry_decay": e.get("decay_window"),
               "competition": op.competition_pressure, "verification_sources": sources, "legal_compliance_risk": e.get("legality_check"),
               "risk": op.risk, "gate_failures": reasons, "promotion": "EXPLOIT" if not reasons and op.competition_pressure in {"LOW", "MEDIUM"} else "VALIDATE",
               "human_minutes_required": 25,
               "validation_task_today": e.get("validation_action", "Read current official limits/pricing, prepare one awareness/cost question for consenting users. Do not buy credits or run paid tests; do not claim savings.")}
        if (op.source_verified and op.source_open and 0 <= age(op.published_at, now) <= 14
                and 0 <= age(op.observed_at, now) <= 7 and any(s.get("verified") for s in sources)):
            p["INFO_EDGE_VALIDATIONS"].append(row)
        else:
            row["promotion"] = "WATCH"
            p["INFO_EDGE_WATCH"].append(row)
    p["INFO_EDGE_VALIDATIONS"].sort(key=lambda r: (r["event_date"], r["id"]))
    exploit_count = 0
    for row in p["INFO_EDGE_VALIDATIONS"]:
        if row["promotion"] == "EXPLOIT":
            exploit_count += 1
            if exploit_count > WIP["INFO_EXPLOIT"]:
                row["promotion"] = "VALIDATE"
                row["gate_failures"].append("EXPLOIT WIP full; no new heavy commitment")
    p["PRESELL"] = [{"id": op.id, "cluster": op.cluster_name, "status": "Real quoted product conversation"}
                    for op in opportunities if "PRODUCT_SIGNAL" in op.routes
                    and {"CONTACTED", "QUOTED"} <= {e.event_type for e in history[op.id]}
                    and not {"WON", "LOST"} & {e.event_type for e in history[op.id]}]
    tools = {t.get("id") or t.get("name"): t for t in tool_candidates}
    for oid in dict.fromkeys(state.get("active_builds", [])):
        if oid in tools and tool_decision(tools[oid], now)[0] == "BUILD NOW":
            p["ACTIVE_BUILDS"].append({"id": oid, "title": tools[oid].get("title") or tools[oid].get("name"), "status": "Human-confirmed active build; all demand/commitment gates passed"})
    for oid in dict.fromkeys(state.get("active_deliveries", [])):
        kinds = {e.event_type for e in history[oid]}
        if oid in index and "WON" in kinds and "LOST" not in kinds:
            p["ACTIVE_DELIVERY"].append({"id": oid, "title": index[oid].title, "status": "Real WON + human-confirmed active delivery"})
    p["wip_overflow"] = {k: len(p[k]) - cap for k, cap in WIP.items() if k in p and len(p[k]) > cap}
    p["quoted_open_count"] = quoted
    if quoted > WIP["QUOTED"]:
        p["wip_overflow"]["QUOTED"] = quoted - WIP["QUOTED"]
    p["unconfirmed_won_commitments"] = [oid for oid, es in history.items() if any(e.event_type == "WON" for e in es)
                                       and oid not in state.get("active_deliveries", []) and not any(e.event_type == "LOST" for e in es)]
    for k, cap in WIP.items():
        if k in p:
            p[k] = p[k][:cap]
    # Heavy WIP overflow pauses new commitments; never hides that the real portfolio exceeded a cap.
    if any(k in p["wip_overflow"] for k in ("ACTIVE_BUILDS", "ACTIVE_DELIVERY", "QUOTED")):
        p["CONTACT_TODAY"] = []
    tasks = []
    for r in p["CONTACT_TODAY"]:
        tasks.append({"action": f"Contact {r['buyer']} via {r['contact_path']}: {r['offer']}; {r['suggested_price']}", "minutes": 10, "id": r["id"]})
    for r in p["FOLLOW_UP"]:
        tasks.append({"action": f"Follow up {r['buyer']}: {r['next_action']}", "minutes": 10, "id": r["id"]})
    for r in p["VALIDATE_FIRST"]:
        tasks.append({"action": f"Verify {r['source']}: {'; '.join(r['gate_failures'])}. Stop after 20 minutes; no pitch unless all contact gates pass.", "minutes": 20, "id": r["id"]})
    for r in p["PRODUCT_VALIDATIONS"]:
        tasks.append({"action": f"Validate {r['cluster_name']}: {r['validation_task_today']} Evidence: {r['evidence_urls'][0]}", "minutes": 30, "id": r["cluster_name"]})
    for r in p["INFO_EDGE_VALIDATIONS"]:
        tasks.append({"action": f"Validate {r['information_edge']}: {r['validation_task_today']} Source: {r['source']}", "minutes": 25, "id": r["id"]})
    # Keep an executable daily combination, rather than promising every WIP item today.
    queues = [tasks[:len(p["CONTACT_TODAY"])]]
    cursor = len(p["CONTACT_TODAY"])
    for size in (len(p["FOLLOW_UP"]), len(p["VALIDATE_FIRST"]), len(p["PRODUCT_VALIDATIONS"]), len(p["INFO_EDGE_VALIDATIONS"])):
        queues.append(tasks[cursor:cursor + size])
        cursor += size
    tasks = []
    while any(queues) and len(tasks) < 9:
        for q in queues:
            if q and len(tasks) < 9:
                tasks.append(q.pop(0))
    tasks.append({"action": "Record only real messages/replies/quotes/wins/payments and actual human minutes; close failed assumptions. No invented outcomes.", "minutes": 10, "id": "outcome-review"})
    p.update({"generated_at": now.isoformat(), "policy": "MANY VALIDATIONS, FEW HEAVY COMMITMENTS",
              "wip_limits": WIP, "today_action_plan": tasks, "total_estimated_human_minutes": sum(t["minutes"] for t in tasks),
              "expected_revenue_exposure": "UNKNOWN; proposals are not revenue. No dollar forecast without real sales history.",
              "outcome_metrics": groups})
    return p


def render_portfolio(p):
    import json
    lines = ["# DAILY MONEY PORTFOLIO", "", f"Generated: {p['generated_at']}", "",
             p["policy"], "Current acquisition budget = 0. No quota filling. Only verified free-contact qualified buyers enter CONTACT_TODAY.",
             "Time estimates are planning defaults; expected_value stays UNKNOWN without real USD sales. Portfolio priority changes allocation, never truth gates.", ""]
    sections = (("A. DIRECT LEADS — CONTACT TODAY", "CONTACT_TODAY"), ("B. FOLLOW UPS", "FOLLOW_UP"),
                ("C. PRODUCT VALIDATIONS", "PRODUCT_VALIDATIONS"), ("D. INFO EDGE VALIDATIONS", "INFO_EDGE_VALIDATIONS"),
                ("E. ACTIVE BUILDS", "ACTIVE_BUILDS"), ("F. ACTIVE DELIVERY", "ACTIVE_DELIVERY"),
                ("DIRECT LEADS — VALIDATE FIRST (desk checks only)", "VALIDATE_FIRST"))
    for title, key in sections:
        lines += ["## " + title, ""]
        if not p[key]:
            lines += ["None. No verified qualifying record; no invented action.", ""]
        for row in p[key]:
            lines += ["### " + str(row.get("title", row.get("cluster_name", row.get("information_edge", row.get("buyer", row["id"] if "id" in row else "candidate"))))), ""]
            for k, v in row.items():
                if k == "evidence_urls":
                    v = v[:4]
                if k == "gate_failures" and not v:
                    v = "none"
                lines.append(f"- {k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}")
            lines.append("")
    lines += ["## SKIP / WATCH", "", f"Direct SKIP: {len(p['SKIP'])}; product WATCH: {len(p['PRODUCT_WATCH'])}; info WATCH: {len(p['INFO_EDGE_WATCH'])}.",
              "Full records and rejection reasons: DAILY_PORTFOLIO.json. WATCH has no forced quota and consumes no active validation time.", "",
              "## G. TODAY ACTION PLAN", ""]
    for i, task in enumerate(p["today_action_plan"], 1):
        lines.append(f"{i}. {task['action']} ({task['minutes']} min)")
    lines += ["", f"Total estimated human time: {p['total_estimated_human_minutes']} minutes.",
              f"Expected revenue exposure: {p['expected_revenue_exposure']}",
              "Highest priority: qualified free buyer contacts, then due follow-ups, then bounded product/edge validations. Empty contacts mean no qualified buyer, not permission to invent one.",
              f"Open quotes: {p['quoted_open_count']}; WIP overflow: {p['wip_overflow'] or 'none'}.",
              f"Real WON with delivery status unreported: {p['unconfirmed_won_commitments']}.",
              "Active builds require verified tester commitment, prices, repeated cross-platform paying demand and explicit human active state. Active deliveries require real WON and explicit active state.", ""]
    return "\n".join(lines)
