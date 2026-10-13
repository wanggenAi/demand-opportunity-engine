from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import urlparse
from .models import Opportunity

def quality_report(opportunities: list[Opportunity], now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    unique_urls = len({op.source_url for op in opportunities})
    https_urls = sum(urlparse(op.source_url).scheme == "https" for op in opportunities)
    evidence = sum(bool(op.evidence_text.strip()) for op in opportunities)
    payment = sum(bool(op.payment_intent_evidence.strip()) for op in opportunities)
    reachable = sum(bool(op.contact_path.strip()) and op.reachability >= 3 for op in opportunities)
    observed_dates = [datetime.fromisoformat(op.observed_at.replace("Z", "+00:00")) for op in opportunities]
    published_dates = [datetime.fromisoformat(op.published_at.replace("Z", "+00:00")) for op in opportunities]
    published_dates = [date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date for date in published_dates]
    ages = [(now - published).days for published in published_dates]
    fresh_7d = sum(age <= 7 for age in ages)
    lines = [
        "# Source and evidence quality check", "",
        f"Checked at: {now.isoformat()}",
        f"- Candidates: {len(opportunities)}; unique source URLs: {unique_urls}/{len(opportunities)}",
        f"- HTTPS provenance present: {https_urls}/{len(opportunities)}",
        f"- Evidence text present: {evidence}/{len(opportunities)}",
        f"- Payment-intent statement present: {payment}/{len(opportunities)}",
        f"- Reachable contact/validation path present (reachability >= 3): {reachable}/{len(opportunities)}",
        f"- Observed timestamps parseable: {len(observed_dates)}/{len(opportunities)}",
        f"- Fresh evidence published within 7 days: {fresh_7d}/{len(opportunities)}",
        "",
        "Authenticity note: URLs are public Reddit/Hacker News source pages captured from search results; the report preserves the exact URL and quoted evidence for manual click-through. A URL alone is not treated as proof of payment.",
        "Time note: published_at is the source date returned by discovery; observed_at is the collection timestamp. Older items are demoted by information-decay scoring.",
        "Payment note: explicit fee/budget/hire/payment language receives the strongest deterministic evidence score; product launches and generic discussion remain lower-confidence signals.",
        "Reachability note: only records with a public reply, DM, email or product contact path can enter the board; human verification is still required before outreach.",
        "",
    ]
    return "\n".join(lines)
