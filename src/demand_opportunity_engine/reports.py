import json
from .clusters import clusters
from .feedback import grouped_metrics
from .models import age
from .scoring import edge_rejections

def product_report(opportunities):
    results = clusters(opportunities)
    lines = ["# PRODUCT THESIS", "",
             "Repeated observations are not automatically product opportunities. Promotion requires >=5 independent buyers/problems, >=2 communities, >=2 primary payment signals, a narrow standardized job and a distribution path.",
             "Identity dedup: platform-author plus normalized exact-content fingerprint. Cross-platform identity linkage is unresolved; duplicate records and seller displays cannot increase counts.",
             "No product was implemented.", ""]
    for c in results[:3]:
        lines += [f"## {c['cluster_name']} — {c['status']}", ""]
        for key in ("independent_demand_count", "payment_evidence_count", "platforms", "communities", "repeated_pain",
                    "current_alternatives", "productization_potential", "suggested_product_form", "distribution"):
            lines.append(f"- {key}: {c[key]}")
        lines += [f"- Promotion blockers: {'; '.join(c['gates_failed']) or 'none'}",
                  f"- Pre-build validation: {c['prebuild_validation']}", "- Representative evidence:"]
        lines += [f"  - {url}" for url in c["evidence_urls"][:6]]
        lines.append("")
    if not results:
        lines.append("No independent demand cluster found.")
    return "\n".join(lines).rstrip() + "\n", results

def edge_report(edges, now):
    lines = ["# INFO EDGE BOARD", "", f"Checked: {now.isoformat()}", "",
             "Only current, corroborated changes are candidates. Target-buyer awareness and paid validation are separate requirements; public availability is not scarcity.", ""]
    accepted = []
    for op in edges[:3]:
        reasons = edge_rejections(op, now)
        if not reasons:
            accepted.append(op)
        e = op.info_edge
        lines += [f"## {op.title} — {'VERIFIED EDGE' if not reasons else 'VALIDATION CANDIDATE ONLY'}", "",
                  f"- What changed / novelty: {e.get('novelty')}",
                  f"- Exact event date: {op.published_at}; age: {age(op.published_at, now):.2f} days",
                  f"- information_gap: {e.get('information_gap')}",
                  f"- target_buyer: {e.get('target_buyer')}",
                  f"- monetization_path: {e.get('monetization_path')}",
                  f"- decay_window: {e.get('decay_window')}",
                  f"- Verification / legality: {e.get('legality_check')}",
                  f"- risk: {op.risk}",
                  f"- 24–48h validation: {op.next_action}",
                  f"- Failed promotion gates: {'; '.join(reasons) or 'none'}", "- verification_source:"]
        for s in e.get("verification_sources", []):
            lines.append(f"  - {s['url']} — exact excerpt: {s['quote']}; verified={s['verified']}; independent={s['independent']}; method={s.get('method', 'public source')}")
        lines.append("")
    lines += [f"Promoted current information edges: {len(accepted)}. Old HN launches from V1 are excluded.", ""]
    return "\n".join(lines)

def feedback_report(opportunities, events):
    from .scoring import score_opportunity
    groups = grouped_metrics(events, opportunities)
    non_discovery = [e for e in events if e.event_type != "DISCOVERED"]
    lines = ["# OUTCOME FEEDBACK", "",
             f"Real events read: {len(events)}; human conversion events: {len(non_discovery)}.",
             "DISCOVERED carries zero reply/quote/win weight. No synthetic sales events were appended to the real log.",
             "Rates use distinct CONTACTED opportunities. Average ticket is realized WON+REVENUE by currency; cycle is CONTACTED→WON. Two contacts minimum, Laplace-smoothed rates, bounded relative ticket/cycle correction. Platform/channel/cluster effects are averaged, not added. Hard gates always apply.",
             "", "## Real grouping metrics", "", json.dumps(groups, ensure_ascii=False, indent=2), "",
             "## Score path proof", ""]
    for op in opportunities[:3]:
        s = score_opportunity(op, events=events, opportunities=opportunities)
        lines.append(f"- {op.id}: components.outcome_feedback={s['components']['outcome_feedback']}; consumed groups={list(s['feedback_groups'])}")
    lines += ["", "For a positive/negative controlled demonstration use tests.test_engine feedback tests; those fixtures are never production outcomes.", ""]
    return "\n".join(lines)
