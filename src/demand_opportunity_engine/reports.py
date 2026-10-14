import json
from .clusters import clusters
from .feedback import grouped_metrics
from .models import age
from .scoring import edge_rejections

def refresh_known_edges(edges, now, fetch=None):
    """Recheck existing primary URLs; never invent new events, gaps or buyers."""
    from .markets import fetch_public, visible
    from .discovery import snapshot
    import hashlib
    fetch = fetch or fetch_public
    audits = []
    for op in edges:
        audit = {"id": op.id, "url": op.source_url, "checked_at": now.isoformat(), "refreshed": False}
        if not 0 <= age(op.published_at, now) <= 14:
            audit["reason"] = "event expired; no publication rejuvenation"
        else:
            try:
                body = visible(fetch(op.source_url))
                if visible(op.raw_evidence_quote) not in body:
                    raise ValueError("known primary quote absent; no fresh verification")
                path, digest = snapshot({"url": op.source_url, "checked_at": now.isoformat(),
                                         "matched_quote": op.raw_evidence_quote,
                                         "primary_text_sha256": hashlib.sha256(body.encode()).hexdigest()}, "data/evidence/info-rechecks", op.source_url)
                op.observed_at = now.isoformat()
                op.info_edge["primary_rechecked_at"] = now.isoformat()
                op.info_edge["primary_recheck_snapshot"] = path + "#sha256=" + digest
                audit.update(refreshed=True, snapshot=op.info_edge["primary_recheck_snapshot"])
            except Exception as exc:
                audit["error"] = str(exc)  # Preserve last verification time; no bypass/retry loop.
        audits.append(audit)
    return audits

def product_report(opportunities):
    results = clusters(opportunities)
    lines = ["# PRODUCT THESIS", "",
             "Repeated observations are not automatically product opportunities. Promotion requires >=5 independent buyers/problems, >=2 communities, >=2 primary payment signals, a narrow standardized job and a distribution path.",
             "Identity dedup: platform-author plus normalized exact-content fingerprint. Cross-platform identity linkage is unresolved; duplicate records and seller displays cannot increase counts.",
             "Anonymous marketplace employers are excluded from independent demand/payment cluster counts; seven project pages do not prove seven independent buyers.",
             "Small desk/interview validations run in parallel in DAILY_MONEY_PORTFOLIO.md, even while product promotion remains blocked. A cluster score never grants BUILD; verified competitor prices and a willing tester/preorder are required. No product was implemented.", ""]
    for c in results:
        lines += [f"## {c['cluster_name']} — {c['status']}", ""]
        for key in ("independent_demand_count", "payment_evidence_count", "platforms", "communities", "repeated_pain",
                    "current_alternatives", "productization_potential", "suggested_product_form", "distribution"):
            lines.append(f"- {key}: {c[key]}")
        lines += [f"- Promotion blockers: {'; '.join(c['gates_failed']) or 'none'}",
                  f"- Action: {'VALIDATE (paid pilot first; build/distribution assumptions remain unverified)' if not c['gates_failed'] else 'WATCH (no standardized product build authorized by evidence)'}",
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
    for op in edges:
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


def buyer_report(opportunities, now, discovery):
    from collections import Counter
    from .signals import commercial_truth
    from .scoring import do_now_rejections
    buyers = [o for o in opportunities if o.source_verified and commercial_truth(o)[0] != 'NONE']
    fresh = [o for o in buyers if 0 <= age(o.published_at, now) <= 7]
    lines = ['# BUYER INTENT DISCOVERY', '', f'Checked: {now.isoformat()}', '',
             f'Verified explicit commercial buyers: {len(buyers)}; published within 7 days: {len(fresh)}.',
             f'Intent types: {dict(Counter(o.commercial_intent_type for o in buyers))}',
             'Commercial intent is not a verified budget or a promise of purchase. Exact buyer-authored sentences and legitimate source paths are mandatory. No outbound messages sent.', '',
             '## Independent source strategies', '',
             '- DIRECT_LEAD: public jobs/requests, sourcing/procurement, bounties, Reddit request pages and HN hiring comments. Exact primary commercial gate required.',
             '- PRODUCT_SIGNAL: GitHub bugs, HN pain discussions and independently repeated commercial needs. Observers are excluded from sales recommendations.',
             '- INFO_EDGE: official event announcements plus corroboration; separately maintained verified edge evidence. No launch automatically promotes.', '',
             '## Additional public source families', '']
    attempts = (discovery or {}).get('buyer_sources', [])
    lines.append(f'Additional families attempted this run: {len({a["source_family"] for a in attempts})}.')
    for a in attempts:
        lines += ['', f'### {a["source_family"]}', '', f'- Access: {a["access_method"]}; {a["url"]}',
                  f'- Records inspected: {a["records_inspected"]}; primary pages opened: {a["primary_pages_opened"]}; collected observations: {a["collected"]}',
                  f'- Verified buyer requests: {a["verified_buyer_requests"]}; explicit commercial signals: {a["explicit_commercial_signals"]}',
                  f'- Limitations: {"; ".join(a["limitations"]) or "none reported"}',
                  f'- Errors: {json.dumps(a["errors"], ensure_ascii=False)}',
                  f'- Audit snapshots: {", ".join(a["evidence_snapshots"])}']
    lines += ['', '## Primary commercial evidence (distinct source URLs)', '']
    for op in sorted(buyers, key=lambda o:o.published_at, reverse=True):
        lines += [f'### {op.title}', '', f'- Source: {op.source_url}',
                  f'- Buyer: {op.buyer_id}; published_at: {op.published_at}; last_activity_at: {op.last_activity_at}',
                  f'- Intent: {op.commercial_intent_type}; exact quote: {op.commercial_intent_quote}',
                  f'- Need (primary text): {op.raw_evidence_quote}',
                  f'- Contact/application: {op.contact_path}; public profile: {op.target_profile_url}',
                  f'- Competition: {op.competition_pressure}; replies={op.comment_count}; providers={op.seller_competition_count}; complete={op.comments_complete}',
                  f'- REMOTE_NOW scope: {op.suggested_offer}; proposed price: {op.suggested_price_range}',
                  f'- Dependencies: {op.required_capabilities}; effort: {op.effort}; risk: {op.risk}',
                  f'- First-message angle: {op.first_message}',
                  f'- DO NOW gate failures: {"; ".join(do_now_rejections(op,now)) or "none"}', '']
    if not buyers:
        lines.append('No verified explicit commercial buyer. Do not substitute pain observers.')
    from pathlib import Path
    supplement = Path('data/search_discovery_audit.json')
    if supplement.exists():
        audit = json.loads(supplement.read_text())
        lines += ['', '## Search-index fallback (separate audit, not live qualified counts)', '',
                  f'- Method: {audit["method"]}; checked: {audit["observed_at"]}',
                  f'- Queries: {json.dumps(audit["queries"],ensure_ascii=False)}',
                  f'- Limitations: {"; ".join(audit["limitations"])}']
        for row in audit['records']:
            lines += [f'- {row["url"]}: {row["verification"]}; original date from index={row["published_date_from_index"]}; primary snippet={row["exact_quote"]}; decision={row["decision"]}']
    return '\n'.join(line.rstrip() for line in '\n'.join(lines).splitlines()).rstrip()+'\n'
