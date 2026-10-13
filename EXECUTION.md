# Operate the money loop

Python 3.11+ standard library only. Run from repository root:

~~~sh
PYTHONPATH=src python3 -m demand_opportunity_engine.cli discover
PYTHONPATH=src python3 -m unittest discover -s tests -v
~~~

Discovery independently refreshes bounded Hacker News Algolia and GitHub public issue searches, retrieves primary bodies and replies, saves API responses with collection time and SHA256 pointers in data/evidence/, upserts canonical source URLs and records DISCOVERED once. It then regenerates reports. Edit queries in data/discovery_config.json; no paid API, login or evasion.

Use the report command without fetching. --as-of 2026-10-13T04:00:00Z makes time gates reproducible. Adapter failures are recorded in data/discovery_run.json, never fabricated as success. Retained records keep their prior observed_at. GitHub comments are fetched up to 100; incomplete counts become UNKNOWN competition.

data/opportunities.json is the unchanged V1 seed/audit fixture. It contains interpreted and sometimes misattributed evidence and is deliberately excluded from V2 ranking, clusters and edges. Do not ingest it as verified primary evidence.

data/info_edges.json holds manually verified current web changes, separate from demand discovery. This run cross-checked one announcement against an independent benchmark. Target-buyer awareness remains unverified, so no paid edge is promoted. Future verification must retain the event date, not replace it with collection time.

## Record real outcomes

Prepare one JSON event using the actual store ID. Shape only, not a real event:

~~~json
{
  "event_id": "unique-event-id",
  "opportunity_id": "actual-store-id",
  "event_type": "CONTACTED",
  "occurred_at": "2026-10-13T04:00:00Z",
  "channel": "GitHub"
}
~~~

Append and regenerate:

~~~sh
PYTHONPATH=src python3 -m demand_opportunity_engine.cli outcome --event /absolute/path/to/real-event.json
PYTHONPATH=src python3 -m demand_opportunity_engine.cli report
~~~

Events: DISCOVERED, CONTACTED, REPLIED, QUALIFIED, QUOTED, WON, LOST, REVENUE. QUOTED/REVENUE require amount/currency; LOST requires loss_reason. IDs deduplicate, unknown opportunities reject. No command deletes/rewrites outcome rows. Repeated contacts, changed quotes and revenue payments require distinct event IDs. Unreplied contacts stay in the cohort, not fabricated REPLIED=false events; early rates are provisional.

Scoring actually reads the log. Only DISCOVERED exists so far, giving zero conversion bonus. Controlled success/loss fixtures prove nonzero adjustments without synthetic sales in production; see OUTCOME_FEEDBACK.md and FEEDBACK_DEMONSTRATION.md.

## Human limit

One primary money action and one small experiment. DO NOW may be empty. VALIDATE means confirm need, permission and payment; it does not authorize pitching every bug reporter. Price ranges are test proposals for Brain/human review, never buyer budgets. No warehouse, QC, freight or specialist capacity is assumed.

Discovery is rerunnable on demand; no scheduler is installed this sprint. Reddit returned HTTP 403 and browser-harness initialization failed; no Reddit refresh is claimed.
