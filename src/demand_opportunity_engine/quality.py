from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from .models import age
from .board import selections
from .signals import payment_truth
from .clusters import observation_eligible

def quality_report(opportunities, now=None, events=(), discovery=None):
    now = now or datetime.now(timezone.utc)
    buckets, rejected = selections(opportunities, now, events)
    dates = {"0–7 days": 0, "7–14 days": 0, "14–30 days": 0, ">30 days": 0, "future": 0}
    for op in opportunities:
        a = age(op.published_at, now)
        dates["future" if a < 0 else "0–7 days" if a <= 7 else "7–14 days" if a <= 14 else "14–30 days" if a <= 30 else ">30 days"] += 1
    eligible = [o for o in opportunities if observation_eligible(o)]
    checksums = 0
    api_snapshots = 0
    for op in opportunities:
        if "#sha256=" in op.source_snapshot:
            api_snapshots += 1
            path, digest = op.source_snapshot.split("#sha256=")
            if Path(path).exists() and sha256(Path(path).read_bytes()).hexdigest() == digest:
                checksums += 1
    lines = ["# Source quality report", "", f"Checked at: {now.isoformat()}", "",
             f"- Live observations: {len(opportunities)}; unique URLs: {len({o.source_url for o in opportunities})}",
             f"- Source distribution: {dict(Counter(o.source_platform for o in opportunities))}",
             f"- Published date distribution: {dates}",
             f"- Source roles: {dict(Counter(o.buyer_role for o in opportunities))}",
             f"- Demand/problem observations after noise rejection: {len(eligible)}; rejected: {len(rejected)}",
             f"- Candidate routes (not validated money claims): {dict(Counter(r for o in eligible for r in o.routes))}",
             f"- Primary payment signals among demand observations: {dict(Counter(payment_truth(o)[0] for o in eligible))}",
             f"- Concrete public profiles: {sum(bool(o.target_profile_url) for o in opportunities)}",
             f"- Full competition replies collected: {sum(o.comments_complete for o in opportunities)}",
             f"- API evidence snapshot SHA256 checks: {checksums}/{api_snapshots}; web edge provenance kept separately",
             f"- Verified OP revival evidence: {sum(bool(o.buyer_activity_url and o.buyer_activity_quote) for o in opportunities)}",
             f"- DO NOW / VALIDATE / WATCH: { {k: len(v) for k,v in buckets.items()} }",
             "- V1 seed: data/opportunities.json retained only as historical audit fixture; excluded from live ranking.",
             "- updated_at, seller comments, collection time and vendor launches never revive a buyer request.",
             "- Open bug reports are pain observations, not automatically paying buyers. Public author identity does not verify a business or buying authority.",
             "- Competition counts are observed lower bounds; private DMs and off-platform quotes remain unknown.",
             "", "## Sources refreshed", ""]
    if discovery:
        for item in discovery.get("adapters", []):
            lines.append(f"- {item['source']}: refreshed={item['refreshed']}; records={item['collected']}; errors={len(item['errors'])}")
            for error in item["errors"]:
                lines.append(f"  - {error['url']}: {error['error']}")
        for blocked in discovery.get("blocked_sources", []):
            lines.append(f"- Unavailable: {blocked['source']}: {blocked['reason']}")
    lines += ["", "## Rejections / DO NOW gate failures", ""]
    for op, score in sorted(rejected + [x for v in buckets.values() for x in v], key=lambda p:p[0].id):
        lines.append(f"- {op.id} {op.source_url}: {'; '.join(score['do_now_rejections']) or 'no hard-gate failures'}; eligible_observation={observation_eligible(op)}")
    return "\n".join(lines) + "\n"
