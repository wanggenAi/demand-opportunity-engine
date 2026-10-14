"""Bounded public market checks. No login, search snippets or invented timestamps."""
import html
import json
import re
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urljoin
from .discovery import make_op, snapshot, text_from_html
from .signals import normalize_intent, cluster_for


def fetch_public(url):
    req = urllib.request.Request(url, headers={"User-Agent": "demand-opportunity-engine/0.3 public research"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def visible(value):
    value = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", value, flags=re.S | re.I)
    return re.sub(r"\s+", " ", text_from_html(value))


def project_document(page):
    match = re.search(r'<script[^>]*id="webapp-state"[^>]*>(.*?)</script>', page, re.S)
    if not match:
        raise ValueError("No public project document; HTML shell is not primary evidence")
    state = json.loads(match[1])["NGRX_STATE"]["projectsSeo"]
    for domain in state.values():
        for doc in domain.get("documents", {}).values():
            raw = doc.get("rawDocument", {})
            if raw.get("projectId") and raw.get("description") and raw.get("startTime"):
                return raw
    raise ValueError("Missing original body/date; no relative-date inference")


def iso_ms(value):
    return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat()


def advantage(op):
    """Evidence annotations only: never change score weights or infer a portfolio."""
    text = op.source_text
    china = bool(re.search(r"China|Chinese|Mandarin|1688|Alibaba|Guangzhou|Shenzhen", text, re.I))
    language = bool(re.search(r"Mandarin|Chinese.language|simplified Chinese|Chinese supplier", text, re.I))
    technical = bool(re.search(r"API|Python|workflow|integration|automation|stress.test", text, re.I))
    op.operator_advantage = {
        "china_local_advantage": "LOW" if china and op.fulfillment_mode == "REMOTE_NOW" else "NONE",
        "language_advantage": "MEDIUM" if language else "NONE",
        "technical_advantage": "MEDIUM" if technical and op.fulfillment_mode == "REMOTE_NOW" else "NONE",
        "direct_contactability": "MEDIUM" if op.contact_path else "LOW",
        "evidence": "Task explicitly mentions China/Chinese" if china else ("Task explicitly mentions remote software work" if technical else "No structural advantage evidenced"),
        "controlled_scope": "Chinese web research, translation drafts, evidence comparison; authorized remote code/tests only",
        "location_limit": "Desk research only; physical China location, field access and qualifications are not verified",
        "cannot_promise": "Factory inspection, product safety/certification, legal/customs, freight/DDP, warehousing, supplier quality guarantees, or unverified case studies",
    }
    # Narrow jobs only where the original author actually describes that job.
    if re.search(r"(?:voice|Vapi|Twilio|ElevenLabs)", text, re.I) and re.search(r"QA|stress.test", text, re.I):
        op.cluster_name = "voice_agent_qa"
    elif re.search(r"Looker|GA4", text, re.I) and re.search(r"report", text, re.I):
        op.cluster_name = "marketing_report_automation"
    elif op.cluster_name in {"voice_agent_qa", "marketing_report_automation"}:
        op.cluster_name = cluster_for(text)
    return op


def freelancer_op(raw, url, now, directory):
    body = raw["description"]
    # This is a buyer-entered structured source field, not analyst payment prose.
    # Save the full raw document so the normalization is independently checkable.
    budget = raw.get("budget", {})
    if budget.get("min", 0) > 0 and raw.get("formattedBudget"):
        body += "\nBudget: " + raw["formattedBudget"]
    bids = raw.get("bids", [])
    count = raw.get("bidStats", {}).get("bidCount")
    comments = [{"author": b["username"], "text": b["description"],
                 "at": iso_ms(raw["startTime"]), "url": "https://www.freelancer.com/u/" + b["username"]} for b in bids]
    # Bid times are unavailable: never use bids as buyer-activity timestamps.
    op = make_op("Freelancer", "Public commissioned projects", url, url, raw["title"], body,
                 "unresolved-employer", "", iso_ms(raw["startTime"]), now.isoformat(),
                 [], count, False, raw.get("status") == "active" and iso_ms(raw["endTime"]) > now.isoformat(), raw, directory)
    op.buyer_role = "BUYER"
    normalize_intent(op)
    op.observed_budget = {"min": budget.get("min"), "max": budget.get("max"),
                          "currency": raw.get("currencyDetails", {}).get("code"),
                          "display": raw.get("formattedBudget"), "basis": "buyer project budget, not a service pilot commitment"}
    op.comment_count = count
    op.seller_competition_count = len({b["username"] for b in bids})
    op.comments_complete = count is not None and len(bids) == count
    op.competition_evidence = [c["url"] for c in comments]
    op.mature_quote_present = any(b.get("amount") is not None for b in bids)
    op.competition_pressure = "HIGH" if (count is not None and count >= 5) or op.mature_quote_present else ("LOW" if count == 0 else "UNKNOWN")
    op.last_activity_at = iso_ms(raw["latestActivityTime"]) if raw.get("latestActivityTime", 0) > 0 else None
    op.contact_path = url
    op.contact_channel = "Freelancer on-platform bid; human account/eligibility required; no off-platform contact"
    op.source_family = "freelance project marketplace (Freelancer)"
    op.discovery_route = "DIRECT_LEAD"
    op.required_capabilities.append("Employer identity unresolved publicly; required portfolio must be truthful; confirm exact scope and milestone before accepting")
    if re.search(r"inspection|factory audit|ASTM|EN.?71|certif|IPC standards|quality check|firmware|\bIC\b|\bSMT\b", raw["title"] + " " + raw["description"], re.I):
        op.fulfillment_mode = "SPECIALIST_REQUIRED"
    elif raw.get("isLocal") or re.search(r"follow.up calls|phone calls|entire process|full funnel|legacy desktop", raw["description"], re.I):
        op.fulfillment_mode = "PARTNER_REQUIRED"
    op.risk += "; Project budget covers original full scope, not our narrower research. No assumed permission to substitute deliverables."
    op.why_now = "Original server-rendered startTime and endTime retained; latestActivityTime is not proven buyer renewal."
    return advantage(op)


def market_sources(config, now, directory, fetch=fetch_public):
    rows, attempts = [], []
    for source in config.get("market_sources", []):
        a = {"source_family": source["family"], "access_method": "bounded public HTTP/JSON; no authenticated endpoint",
             "url": source["url"], "records_inspected": 0, "primary_pages_opened": 0,
             "verified_buyer_requests": 0, "explicit_commercial_signals": 0, "collected": 0,
             "errors": [], "limitations": [], "evidence_snapshots": [], "records": [], "opportunity_ids": [], "inspected_keys": []}
        def save(data, url):
            path, digest = snapshot({"source_url": url, "collected_at": now.isoformat(), "source": data}, directory, url)
            a["evidence_snapshots"].append(path + "#sha256=" + digest)
            return path + "#sha256=" + digest
        try:
            page = fetch(source["url"])
            kind = source["kind"]
            targets = []
            if kind == "freelancer":
                links = list(dict.fromkeys(re.findall(r'href="(/projects/[^"?#]+)"', page)))
                a["records_inspected"] = len(links)
                a["inspected_keys"] = links
                targets = [urljoin(source["url"], p) for p in links if re.search(source["target_pattern"], p, re.I)][:source["max_pages"]]
                save({"project_links": links, "selected": targets}, source["url"])
            elif kind == "shopify":
                data = json.loads(page)
                topics = data["topic_list"]["topics"]
                a["records_inspected"] = len(topics)
                a["inspected_keys"] = [str(t["id"]) for t in topics]
                targets = [f'https://community.shopify.com/t/{t["id"]}.json' for t in topics if re.search(source["target_pattern"], t["title"], re.I)][:source["max_pages"]]
                save(data, source["url"])
            elif kind == "founder":
                links = list(dict.fromkeys(re.findall(r'href="(/post/[^"?#]+)"', page)))
                a["records_inspected"] = len(links)
                a["inspected_keys"] = links
                targets = [urljoin(source["url"], p) for p in links if re.search(source["target_pattern"], p, re.I)][:source["max_pages"]]
                save({"post_links": links, "selected": targets}, source["url"])
            elif kind == "rfq":
                links = list(dict.fromkeys(u.strip() for u in re.findall(r'href=["\']([^"\']*buyoffer/[^"\']+)["\']', page)))
                a["records_inspected"] = len(links)
                a["inspected_keys"] = links
                targets = links[:source["max_pages"]]
                save({"rfq_links": links, "selected": targets}, source["url"])
            for url in targets:
                try:
                    primary = fetch(url)
                    op = None
                    if kind == "freelancer":
                        raw = project_document(primary)
                        op = freelancer_op(raw, url, now, directory)
                        op.source_snapshot = save(raw, url)
                    elif kind == "shopify":
                        raw = json.loads(primary)
                        posts = raw["post_stream"]["posts"]
                        first = posts[0]
                        canonical = f'https://community.shopify.com/t/{raw["slug"]}/{raw["id"]}'
                        comments = [{"author": p["username"], "text": text_from_html(p["cooked"]), "at": p["created_at"],
                                     "url": canonical + '/' + str(p["post_number"])} for p in posts[1:]]
                        op = make_op("Shopify Community", "Commerce operator forum", canonical, url, raw["title"], text_from_html(first["cooked"]),
                                     first["username"], 'https://community.shopify.com/u/' + first["username"], first["created_at"], now.isoformat(), comments,
                                     raw["posts_count"] - 1, len(posts) == raw["posts_count"], not raw.get("closed", False), raw, directory)
                        op.source_family = source["family"]
                        op.contact_channel = "Shopify forum; permission required; ordinary support question is not a buyer"
                        advantage(op)
                        op.source_snapshot = save(raw, url)
                    else:
                        excerpt = visible(primary)
                        if kind == "founder":
                            body = re.search(r'<div class="post-page__body[^>]*>(.*?)</div>', primary, re.S)
                            excerpt = visible(body[1]) if body else "Author body unresolved; no buyer promotion"
                            schemas = [json.loads(x) for x in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', primary, re.S)]
                            record = {"url": url, "author_body": excerpt, "metadata": schemas, "decision": "Discussion/seller/product research only; no paid buyer or complete competition/contact evidence"}
                        else:
                            start = excerpt.find("Last Updated:")
                            record = {"url": url, "primary_excerpt": excerpt[max(0, start):start+2100], "decision": "Physical goods RFQ; not a commissioned China research service; contact gated and competition unknown"}
                            if "RFQ Details" in excerpt and re.search(r"need|quote|buy", excerpt[start:start+2000], re.I):
                                a["verified_buyer_requests"] += 1
                                a["explicit_commercial_signals"] += 1
                                record["buyer"] = True
                                date = re.search(r"Posted on: (\d{2} \w{3} \d{4})", excerpt)
                                record["published_at"] = datetime.strptime(date[1], "%d %b %Y").replace(tzinfo=timezone.utc).isoformat() if date else None
                                record["date_precision"] = "day; original posted date, not crawl date"
                        a["records"].append(record)
                        save(record, url)
                    a["primary_pages_opened"] += 1
                    if op:
                        if op.published_at > now.isoformat():
                            raise ValueError("Future source date; excluded")
                        rows.append(op)
                        a["opportunity_ids"].append(op.id)
                        a["collected"] += 1
                        if op.buyer_role == "BUYER" and op.commercial_intent_type != "NONE":
                            a["verified_buyer_requests"] += 1
                            a["explicit_commercial_signals"] += 1
                except Exception as exc:
                    a["errors"].append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
            a["limitations"] += source.get("limitations", [])
        except Exception as exc:
            a["errors"].append({"url": source["url"], "error": f"{type(exc).__name__}: {exc}"})
        attempts.append(a)
    return rows, attempts
