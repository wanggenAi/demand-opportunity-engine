"""Two bounded free public API adapters, exact source snapshots, no login/evasion."""
import hashlib
import html
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .models import Opportunity, timestamp
from .signals import SELLER, REQUEST, PAIN, payment_truth, cluster_for, competition, commercial_truth, normalize_intent
from .store import upsert, append_outcome, load_outcomes
from .models import Outcome

def fetch_json(url):
    request = urllib.request.Request(url, headers={
        "User-Agent": "demand-opportunity-engine/0.2 public-demand-research",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)

def text_from_html(value):
    return html.unescape(re.sub(r"<[^>]+>", " ", value or "")).strip()

def identity(url):
    return hashlib.sha256(url.rstrip("/").encode()).hexdigest()[:16]

def snapshot(item, directory, url):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (identity(url) + ".json")
    payload = json.dumps(item, ensure_ascii=False, indent=2) + "\n"
    path.write_text(payload)
    return str(path), hashlib.sha256(payload.encode()).hexdigest()

def relevant_buyer_activity(comments, author):
    # Seller replies and generic OP thanks/edits do not revive a request.
    eligible = [c for c in comments if c["author"] == author and
                re.search(r"still (?:looking|need|seeking)|budget|deadline|contact me|email me|need (?:help|someone)|looking (?:for|to hire)", c["text"], re.I)]
    return max(eligible, key=lambda c: c["at"]) if eligible else None

def make_op(platform, community, url, api_url, title, body, author, profile, published,
            observed, comments, count, complete, source_open, raw, directory):
    source_text = title + "\n" + body
    quote = source_text[:700]  # exact contiguous excerpt, not analyst summary
    cluster = cluster_for(source_text)
    seller = bool(SELLER.search(title) or SELLER.search(body[:300]) or re.search(r"^show hn:|^launch hn:", title, re.I))
    # A repository issue is a problem observation, not automatically a paying buyer.
    buying = bool(re.search(r"\bi need\b|\bwe need\b|\bi(?:'m| am) looking for\b|\bwe(?:'re| are) looking for\b|can anyone|looking to hire|seeking freelancer\b|\[hiring\]", source_text, re.I)) and not seller
    role = "SELLER" if seller else ("BUYER" if buying else "PROBLEM_OBSERVER")
    if not seller and platform == "Hacker News" and not re.match(r"ask(?: hn)?[: ]", title, re.I) and not buying:
        role = "NEWS"
    if "who wants to be hired" in community.lower():
        role = "SELLER"
    activity = relevant_buyer_activity(comments, author)
    sellers = [c for c in comments if c["author"] != author]
    n, pressure, mature, dms, evidence = competition(sellers, complete, source_text, applications=platform == "n8n Community")
    requirements = []
    if re.search(r"on.site|factory visit|warehous|ddp|freight|quality inspection", source_text, re.I):
        requirements.append("PARTNER_REQUIRED: on-site QC, warehouse or freight execution")
    if re.search(r"certification|medical|battery.{0,25}compliance|customs clearance|legal advice", source_text, re.I):
        requirements.append("SPECIALIST_REQUIRED: compliance/customs/category expertise")
    mode = "SPECIALIST_REQUIRED" if any(x.startswith("SPECIALIST") for x in requirements) else ("PARTNER_REQUIRED" if requirements else "REMOTE_NOW")
    sourcing = cluster.startswith("supplier") or cluster in {"sample_comparison", "rfq_translation"}
    offer = "Remote supplier verification / RFQ comparison for one SKU" if sourcing else "Remote diagnosis of one failing workflow, with reproduction and recovery checklist"
    price = "USD 100–250 (proposed discovery pilot; buyer budget unverified)" if sourcing else "USD 100–200 diagnostic; USD 300–600 implementation only after scope agreement (proposal, not budget)"
    angle = ("Which SKU, destination and supplier are you evaluating? I can scope a remote verification memo; physical QC is separate."
             if sourcing else "Is this still blocking your workflow? I can scope a remote reproduction and recovery audit; what is the daily volume and cost of failures?")
    saved, digest = snapshot({"source_api_url": api_url, "collected_at": observed,
                             "source": raw, "comments": comments, "comments_complete": complete}, directory, url)
    op = Opportunity(
        id=identity(url), title=title, source_platform=platform, source_url=url,
        published_at=published, observed_at=observed, raw_evidence_quote=quote,
        source_text=source_text, buyer_id=f"{platform}:{author}", target_profile_url=profile,
        community=community, source_api_url=api_url, source_verified=True,
        source_snapshot=f"{saved}#sha256={digest}", buyer_role=role,
        source_open=source_open, buyer_activity_at=activity["at"] if activity else None,
        buyer_activity_url=activity["url"] if activity else "", buyer_activity_quote=activity["text"] if activity else "",
        buyer_activity_verified=bool(activity), buyer_activity_author_id=f"{platform}:{author}" if activity else "",
        last_activity_at=max([published] + [c["at"] for c in comments]),
        comment_count=count, seller_competition_count=n, comments_complete=complete,
        competition_pressure=pressure, competition_evidence=evidence, mature_quote_present=mature,
        many_dms_reported=dms, fulfillment_mode=mode, required_capabilities=requirements,
        cluster_name=cluster, suggested_offer=offer, suggested_price_range=price,
        first_message=angle, effort="2–4 hours diagnostic; implementation estimate after discovery",
        risk=("Payment and exact scope require confirmation; do not pitch unsolicited on bug reports. " + "; ".join(requirements)).strip(),
        differentiation="One scoped remote diagnostic with evidence and pass/fail checklist; no unowned fulfillment promises.",
        derived_interpretation="Public problem/request observation; commercial willingness must be confirmed.",
        why_now="Recently published problem; only contact if payment, competition and capability gates pass.",
        next_action="Read the exact source and author profile, confirm active need and willingness to pay before delivery.",
        confidence=3, contact_channel=platform,
        contact_path=url,
    )
    # Evaluate primary commercial sentences before assigning a BUYER role.
    # Generic requests/bug reports remain observers, not potential sales targets.
    if role not in {"SELLER", "NEWS"}:
        op.buyer_role = "BUYER"
        if commercial_truth(op)[0] == "NONE":
            op.buyer_role = "PROBLEM_OBSERVER"
    normalize_intent(op)
    if op.buyer_role == "SELLER":
        op.buyer_activity_at = None
        op.buyer_activity_url = op.buyer_activity_quote = op.buyer_activity_author_id = ""
        op.buyer_activity_verified = False
    kind, quote, _ = payment_truth(op)
    op.payment_signal_type, op.payment_evidence_quote = kind, quote
    return op

def hn_adapter(config, now, directory, fetch=fetch_json):
    collected, errors = {}, []
    lower = int((now - timedelta(days=config["lookback_days"])).timestamp())
    queries = [(q, "story") for q in config["hn_queries"]]
    queries += [(q, "comment") for q in config.get("hn_request_queries", [])]
    for query, tags in queries:
        url = "https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode({
            "query": query, "tags": tags, "hitsPerPage": config["per_query"],
            "numericFilters": f"created_at_i>{lower},created_at_i<={int(now.timestamp())}",
        })
        try:
            hits = fetch(url)["hits"]
            for hit in hits:
                body = text_from_html(hit.get("comment_text") if tags == "comment" else hit.get("story_text"))
                title = hit.get("title") or body.split("\n")[0][:150]
                if not PAIN.search(title + " " + body):
                    continue
                oid = hit["objectID"]
                if oid in collected:
                    continue
                api = f"https://hn.algolia.com/api/v1/items/{oid}"
                item = fetch(api)
                comments = []
                def walk(children):
                    for child in children:
                        if child.get("author") and child.get("created_at"):
                            comments.append({"author": child["author"], "text": text_from_html(child.get("text")),
                                             "at": child["created_at"], "url": f"https://news.ycombinator.com/item?id={child['id']}"})
                        walk(child.get("children", []))
                walk(item.get("children", []))
                published = item.get("created_at", hit["created_at"])
                if timestamp(published) > now:
                    continue
                author = item.get("author", hit.get("author")) or ""
                story_url = f"https://news.ycombinator.com/item?id={oid}"
                collected[oid] = make_op("Hacker News", hit.get("story_title") or "Ask/Show HN", story_url, api, title,
                                        text_from_html(item.get("text")) or body, author,
                                        f"https://news.ycombinator.com/user?id={urllib.parse.quote(author)}" if author else "",
                                        published, now.isoformat(), comments, len(comments), True, True, item, directory)
        except Exception as exc:
            errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
    return list(collected.values()), errors

def github_adapter(config, now, directory, fetch=fetch_json):
    collected, errors = {}, []
    start = (now - timedelta(days=config["lookback_days"])).date().isoformat()
    end = now.date().isoformat()
    for base in config["github_queries"]:
        url = "https://api.github.com/search/issues?" + urllib.parse.urlencode({
            "q": f"is:issue {base} created:{start}..{end}",
            "sort": "created", "order": "desc", "per_page": config["per_query"],
        })
        try:
            for item in fetch(url).get("items", []):
                key = item["html_url"]
                if key in collected or "pull_request" in item or timestamp(item["created_at"]) > now:
                    continue
                author = item["user"]["login"]
                comments, complete = [], item["comments"] == 0
                if item["comments"]:
                    try:
                        rows = fetch(item["comments_url"] + "?per_page=100")
                        comments = [{"author": r["user"]["login"], "text": r.get("body") or "",
                                     "at": r["created_at"], "url": r["html_url"]} for r in rows]
                        complete = len(comments) == item["comments"]
                    except Exception as exc:
                        errors.append({"url": item["comments_url"], "error": str(exc)})
                collected[key] = make_op("GitHub", "/".join(key.split("/")[3:5]), key, item["url"],
                                         item["title"], item.get("body") or "", author, item["user"]["html_url"],
                                         item["created_at"], now.isoformat(), comments, item["comments"],
                                         complete, item["state"] == "open" and not item.get("locked", False),
                                         item, directory)
        except Exception as exc:
            errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
    return list(collected.values()), errors

def discover(config_path, store_path, outcomes_path, now):
    config = json.loads(Path(config_path).read_text())
    summary = {"observed_at": now.isoformat(), "config": str(config_path), "adapters": [], "blocked_sources": config.get("blocked_sources", [])}
    results = []
    for name, adapter in (("Hacker News", hn_adapter), ("GitHub", github_adapter)):
        rows, errors = adapter(config, now, "data/evidence")
        results.extend(rows)
        summary["adapters"].append({"source": name, "refreshed": bool(rows), "collected": len(rows), "errors": errors})
    from .buyer_discovery import buyer_sources
    buyer_rows, attempts = buyer_sources(config, now, "data/evidence")
    results.extend(buyer_rows)
    summary["buyer_sources"] = attempts
    # Retained for audit, but unrefreshed records cannot get freshness from this run.
    result = upsert(store_path, results)
    known = {e.opportunity_id for e in load_outcomes(outcomes_path) if e.event_type == "DISCOVERED"}
    for op in results:
        if op.id not in known:
            append_outcome(outcomes_path, Outcome(f"discovered-{op.id}", op.id, "DISCOVERED", now.isoformat(), op.source_platform))
            known.add(op.id)
    summary["unique_refreshed"] = len({o.id for o in results})
    Path("data/discovery_run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return result, summary
