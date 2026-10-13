import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from .models import Outcome, Opportunity, timestamp
from .store import load_opportunities, load_outcomes, append_outcome
from .discovery import discover
from .board import build_board, rank
from .quality import quality_report
from .reports import product_report, edge_report, feedback_report
from .clusters import clusters
from .store import upsert

def main():
    parser = argparse.ArgumentParser(description="Public demand discovery, gated ranking and outcome feedback.")
    parser.add_argument("command", nargs="?", choices=["discover", "report", "outcome"], default="report")
    parser.add_argument("--data", default="data/live_opportunities.json")
    parser.add_argument("--config", default="data/discovery_config.json")
    parser.add_argument("--outcomes", default="data/outcomes.jsonl")
    parser.add_argument("--edges", default="data/info_edges.json")
    parser.add_argument("--output", default="reports/TODAY_MONEY_BOARD.md")
    parser.add_argument("--as-of", help="ISO UTC timestamp for reproducible audit; defaults to current time")
    parser.add_argument("--event", help="Path to one real outcome JSON event; used by outcome command")
    args = parser.parse_args()
    now = timestamp(args.as_of) if args.as_of else datetime.now(timezone.utc)
    if args.command == "outcome":
        if not args.event:
            parser.error("outcome requires --event")
        event = Outcome(**json.loads(Path(args.event).read_text()))
        changed = append_outcome(args.outcomes, event, load_opportunities(args.data))
        print("appended" if changed else "already recorded")
        return
    if args.command == "discover":
        opportunities, run = discover(args.config, args.data, args.outcomes, now)
        print(json.dumps({"adapters": run["adapters"], "unique_refreshed": run["unique_refreshed"]}))
    else:
        opportunities = load_opportunities(args.data)
        run = json.loads(Path("data/discovery_run.json").read_text()) if Path("data/discovery_run.json").exists() else None
    cluster_index = {c["cluster_name"]: c for c in clusters(opportunities)}
    for op in opportunities:
        c = cluster_index.get(op.cluster_name)
        if c and c["independent_demand_count"] >= 2 and "PRODUCT_SIGNAL" not in op.routes:
            op.routes.append("PRODUCT_SIGNAL")
    # Preserve route derivation without modifying the historical V1 fixture.
    upsert(args.data, opportunities)
    events = load_outcomes(args.outcomes)
    edges = load_opportunities(args.edges) if Path(args.edges).exists() else []
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_board(opportunities + edges, now.isoformat(), events))
    (output.parent / "SOURCE_QUALITY_CHECK.md").write_text(quality_report(opportunities + edges, now, events, run))
    product, grouped = product_report(opportunities)
    (output.parent / "PRODUCT_THESIS.md").write_text(product)
    (output.parent / "INFO_EDGE_BOARD.md").write_text(edge_report(edges, now))
    (output.parent / "OUTCOME_FEEDBACK.md").write_text(feedback_report(opportunities, events))
    (output.parent / "ranking.json").write_text(json.dumps(
        [{"id": o.id, **s} for o, s in rank(opportunities + edges, now, events)],
        ensure_ascii=False, indent=2) + "\\n")
    print(f"generated reports from {len(opportunities)} live observations, {len(events)} outcome events, {len(grouped)} clusters")

if __name__ == "__main__":
    main()
