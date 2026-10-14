"""Source budget and tool decisions, separate from unchanged sales scoring."""
from collections import defaultdict
from .models import age
from .scoring import do_now_rejections
from .feedback import grouped_metrics


def source_yield_report(opportunities, now, run, events=()):
    index = {o.id: o for o in opportunities}
    families = defaultdict(list)
    for a in (run or {}).get("buyer_sources", []):
        families[a["source_family"]].append(a)
    lines = ["# SOURCE YIELD", "", f"Observed: {(run or {}).get('observed_at', 'unknown')}; evaluated: {now.isoformat()}", "",
             "Four NEW independent ecosystems: Freelancer project marketplace, Shopify commerce operators, Indie Hackers founders, TradeKey RFQs. Two Freelancer categories count as one family. Existing n8n/Remotive/procurement/Reddit/Algora paths remain separately audited.",
             "Inspected = distinct listing records where keys are available; otherwise adapter listing inspections. Resolved buyer pages = primary pages with explicit commercial buyers, including physical-goods RFQs. Fresh column is original publication <=7 days, not recent seller replies. All yields are from this run only; retained old observations do not inflate them.", "",
             "| Source family | Inspected | Primary buyer pages | Commercial buyers | <=7d | LOW/MEDIUM | Capability fit | Contactable | DO NOW gates passed | Buyer/100 | Actionable/100 | Limitations |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    groups = grouped_metrics(events, opportunities)
    total_actionable = 0
    for family, audits in families.items():
        keys = {k for a in audits for k in a.get("inspected_keys", [])}
        n = len(keys) if keys else sum(a["records_inspected"] for a in audits)
        ids = {i for a in audits for i in a.get("opportunity_ids", [])}
        # Legacy adapters do not retain IDs; restrict to observations fetched this run.
        ops = [index[i] for i in ids if i in index]
        if not ids:
            ops = [o for o in opportunities if o.source_family == family and o.observed_at == (run or {}).get("observed_at")]
        buyers = [o for o in ops if o.buyer_role == "BUYER" and o.commercial_intent_type != "NONE"]
        raw_buyers = [r for a in audits for r in a.get("records", []) if r.get("buyer")]
        commercial = len(buyers) + len(raw_buyers)
        if not ids and not raw_buyers:
            commercial = sum(a["verified_buyer_requests"] for a in audits)
        fresh = sum(0 <= age(o.published_at, now) <= 7 for o in buyers) + sum(r.get("published_at") is not None and 0 <= age(r["published_at"], now) <= 7 for r in raw_buyers)
        low = sum(o.competition_pressure in {"LOW", "MEDIUM"} for o in buyers)
        fit = sum(o.fulfillment_mode == "REMOTE_NOW" for o in buyers)
        contact = sum(bool(o.contact_path and o.source_open) for o in buyers)
        actionable = sum(not do_now_rejections(o, now) for o in buyers)
        total_actionable += actionable
        limitations = list(dict.fromkeys(x for a in audits for x in a["limitations"]))
        limitations += [e["error"] for a in audits for e in a["errors"]]
        lines.append(f"| {family} | {n} | {commercial} | {commercial} | {fresh} | {low} | {fit} | {contact} | {actionable} | {100*commercial/n if n else 0:.1f} | {100*actionable/n if n else 0:.1f} | {'; '.join(dict.fromkeys(limitations)) or 'none reported'} |")
    lines += ["", "## Tomorrow's budget", "",
              ("Use up to five qualified ZERO-COST CONTACT_TODAY candidates, with real follow-ups and independent product/edge validations. No source expansion needed." if total_actionable else "Current acquisition budget = 0. No newly tested buyer passed current hard gates. Do not lower gates or buy acquisition access. Use the portfolio's bounded product/edge validation tasks; no invented outreach or automatic source expansion."),
              "", "## Actual outcome learning", "",
              "No sales history means neutral source/offer/price assumptions. After real contacts, source-family/type/cluster/offer cohort reply/quote/win rates and realized tickets should decide tomorrow's allocation; no fake revenue-based priority."]
    for name, metric in groups.items():
        if name.startswith(("source:", "offer:", "type:")) and metric["contacted"]:
            lines.append(f"- {name}: {metric}")
    return "\n".join(lines) + "\n"


TOOL_GATES = ("real_demand", "manageable_competition", "clear_differentiator", "buildable_by_us",
              "monetization_path", "distribution_path", "low_initial_cost", "controlled_dependencies")


def tool_decision(candidate, now):
    failures = [key for key in TOOL_GATES if candidate.get("gates", {}).get(key) is not True]
    evidence = candidate.get("demand_evidence", [])
    independent = {e["author_key"] for e in evidence if e.get("primary_verified") and e.get("author_key")}
    if not independent:
        failures.append("no independently attributable primary demand")
    # Repeated paid pains are required by the Brain; keyword candidates cannot bypass them.
    if len(independent) < 2:
        failures.append("repeated independent demand unproven")
    if len(independent) < 5:
        failures.append("BUILD requires five independent demands")
    verified = [e for e in evidence if e.get("primary_verified") and e.get("author_key")]
    if len({e.get("platform") for e in verified if e.get("platform")}) < 2:
        failures.append("BUILD requires cross-platform demand")
    if len({e["author_key"] for e in verified if e.get("payment_quote") and e.get("payment_primary_verified")}) < 2:
        failures.append("BUILD requires two primary paying demands")
    proof = candidate.get("build_evidence", {})
    for key in ("competitor_prices", "tester_commitment"):
        item = proof.get(key, {})
        if not (item.get("verified") and item.get("source_url", "").startswith("https://") and item.get("exact_quote")):
            failures.append("BUILD missing verified " + key)
    if not proof.get("standardized_delivery"):
        failures.append("BUILD missing standardized delivery")
    checked = candidate.get("checked_at")
    if not checked or not 0 <= age(checked, now) <= 7:
        failures.append("current supply assessment missing/stale")
    if not failures:
        return "BUILD NOW", []
    if candidate.get("reject_reason"):
        return "REJECT", failures
    return ("VALIDATE" if len(independent) >= 2 and candidate.get("gates", {}).get("manageable_competition") else "WATCH"), failures


def tool_report(candidates, now):
    lines = ["# TOOL / MICRO-SAAS OPPORTUNITIES (PRODUCT_SIGNAL)", "", f"Evaluated: {now.isoformat()}", "",
             "Keyword/demand phrases are hypotheses, not search-volume measurements. No fabricated CPC, traffic or Trends volume. Public SERPs discover alternatives; primary user posts prove pain separately. No paid SEO API required.", ""]
    counts = {key: 0 for key in ("BUILD NOW", "VALIDATE", "WATCH", "REJECT")}
    for c in candidates:
        decision, failures = tool_decision(c, now)
        counts[decision] += 1
        lines += [f"## {c['name']} — {decision}", "", f"- Checked at: {c['checked_at']}"]
        for key in ("demand_phrase", "search_intent", "frequency", "target_user", "direct_competitors", "platform_dominance",
                    "observed_gap", "why_switch", "one_day_mvp", "api_cost", "legal_policy_risk", "monetization", "first_dollar",
                    "distribution", "pricing_hypothesis", "validation_24h", "kill_7d"):
            lines.append(f"- {key}: {c[key]}")
        lines += [f"- Failed BUILD gates: {'; '.join(failures) or 'none'}", f"- Rejection reason: {c.get('reject_reason') or 'not rejected; assumptions unresolved'}", "- Demand evidence:"]
        for e in c["demand_evidence"]:
            quote = ' '.join(e['quote'].split())
            lines.append(f"  - {e['url']} — {quote}; primary={e['primary_verified']}; published={e.get('published_at', 'unknown')}; paid tool evidence={e.get('paid_tool_evidence', False)}")
        lines += ["- Supply verification:"] + [f"  - {e['url']} — {e['finding']}; snapshot={e['snapshot']}" for e in c.get("supply_evidence", [])]
        lines.append("")
    lines += [f"Decisions: {counts}", "", "Google Trends/autocomplete: not retrieved in this bounded run; no stable lawful numeric feed established. This limitation does not authorize pretending search volume exists. No MVP built unless BUILD NOW passes."]
    return "\n".join(lines) + "\n"
