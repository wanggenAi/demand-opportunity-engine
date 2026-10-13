from __future__ import annotations
import json
from pathlib import Path
from .models import Opportunity, Outcome

def load_opportunities(path: str | Path) -> list[Opportunity]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    opportunities = [Opportunity(**row) for row in rows]
    for opportunity in opportunities:
        opportunity.validate()
    return opportunities

def append_outcome(path: str | Path, outcome: Outcome) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(outcome.to_dict(), ensure_ascii=False) + "\n")
