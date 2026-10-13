import json
from pathlib import Path
from .models import Opportunity, Outcome

def load_opportunities(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    result = [Opportunity(**row) for row in rows]
    for op in result:
        op.validate()
    if len({o.id for o in result}) != len(result):
        raise ValueError("duplicate opportunity ids")
    return result

def upsert(path, incoming):
    path = Path(path)
    old = load_opportunities(path) if path.exists() else []
    by_url = {o.source_url.rstrip("/"): o for o in old}
    for op in incoming:
        op.validate()
        key = op.source_url.rstrip("/")
        if key in by_url:
            op.id = by_url[key].id
        by_url[key] = op
    path.parent.mkdir(parents=True, exist_ok=True)
    result = sorted(by_url.values(), key=lambda o: o.id)
    path.write_text(json.dumps([o.to_dict() for o in result], ensure_ascii=False, indent=2) + "\n")
    return result

def load_outcomes(path):
    if not Path(path).exists():
        return []
    events = [Outcome(**json.loads(line)) for line in Path(path).read_text().splitlines() if line.strip()]
    ids = set()
    for event in events:
        event.validate()
        if event.event_id in ids:
            raise ValueError("duplicate outcome event")
        ids.add(event.event_id)
    return events

def append_outcome(path, event, opportunities=None):
    event.validate()
    if opportunities is not None and event.opportunity_id not in {o.id for o in opportunities}:
        raise ValueError("unknown opportunity")
    events = load_outcomes(path)
    if event.event_id in {e.event_id for e in events}:
        return False
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
    return True
