import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from .models import Outcome, Opportunity, timestamp
from .store import load_opportunities, load_outcomes, append_outcome
from .discovery import discover
from .board import rank
from .quality import quality_report
from .reports import product_report, edge_report, feedback_report, buyer_report
from .signals import normalize_intent
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
    parser.add_argument("--portfolio-state", default="data/portfolio_state.json", help="Optional human-reported active build/delivery IDs")
    args = parser.parse_args()
    now = timestamp(args.as_of) if args.as_of else datetime.now(timezone.utc)
    if args.command == "outcome":
        if not args.event:
            parser.error("outcome requires --event")
        event = Outcome(**json.loads(Path(args.event).read_text()))
        known = load_opportunities(args.data)
        if Path(args.edges).exists():
            known += load_opportunities(args.edges)
        changed = append_outcome(args.outcomes, event, known)
        print("appended" if changed else "already recorded")
        return
    if args.command == "discover":
        opportunities, run = discover(args.config, args.data, args.outcomes, now)
        print(json.dumps({"adapters": run["adapters"], "unique_refreshed": run["unique_refreshed"]}))
    else:
        opportunities = load_opportunities(args.data)
        run = json.loads(Path("data/discovery_run.json").read_text()) if Path("data/discovery_run.json").exists() else None
    for op in opportunities:
        if op.source_platform == "n8n Community":
            op.buyer_role = "BUYER"  # recompute, then conservatively reject supply/NONE
        normalize_intent(op)
        if op.source_platform == "n8n Community":
            if op.commercial_intent_type == "NONE" and op.buyer_role != "SELLER":
                op.buyer_role = "PROBLEM_OBSERVER"
            from .buyer_discovery import fit_job
            fit_job(op)
        from .markets import advantage
        advantage(op)
    cluster_index = {c["cluster_name"]: c for c in clusters(opportunities)}
    for op in opportunities:
        c = cluster_index.get(op.cluster_name)
        if c and c["independent_demand_count"] >= 2 and "PRODUCT_SIGNAL" not in op.routes:
            op.routes.append("PRODUCT_SIGNAL")
    # Preserve route derivation without modifying the historical V1 fixture.
    upsert(args.data, opportunities)
    events = load_outcomes(args.outcomes)
    edges = load_opportunities(args.edges) if Path(args.edges).exists() else []
    if args.command == "discover":
        from .reports import refresh_known_edges
        run["info_edge_refresh"] = refresh_known_edges(edges, now)
        Path("data/discovery_run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n")
        if edges:
            upsert(args.edges, edges)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    from .portfolio import daily_portfolio, render_portfolio
    tools_path = Path("data/tool_opportunities.json")
    tools = json.loads(tools_path.read_text()) if tools_path.exists() else []
    state_path = Path(args.portfolio_state)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    portfolio = daily_portfolio(opportunities + edges, now, events, tools, state)
    document = render_portfolio(portfolio)
    output.write_text(document)
    (output.parent / "DAILY_MONEY_PORTFOLIO.md").write_text(document)
    (output.parent / "DAILY_PORTFOLIO.json").write_text(json.dumps(portfolio, ensure_ascii=False, indent=2) + "\n")
    (output.parent / "SOURCE_QUALITY_CHECK.md").write_text(quality_report(opportunities + edges, now, events, run))
    product, grouped = product_report(opportunities)
    (output.parent / "PRODUCT_THESIS.md").write_text(product)
    (output.parent / "INFO_EDGE_BOARD.md").write_text(edge_report(edges, now))
    (output.parent / "OUTCOME_FEEDBACK.md").write_text(feedback_report(opportunities + edges, events))
    (output.parent / "BUYER_INTENT_DISCOVERY.md").write_text(buyer_report(opportunities, now, run))
    from .action_reports import source_yield_report, tool_report
    (output.parent / "SOURCE_YIELD.md").write_text(source_yield_report(opportunities, now, run, events))
    if tools_path.exists():
        (output.parent / "TOOL_OPPORTUNITIES.md").write_text(tool_report(tools, now))
    (output.parent / "ranking.json").write_text(json.dumps(
        [{"id": o.id, **s} for o, s in rank(opportunities + edges, now, events)],
        ensure_ascii=False, indent=2) + "\n")
    print(f"generated reports from {len(opportunities)} live observations, {len(events)} outcome events, {len(grouped)} clusters")

if __name__ == "__main__":
    main()
