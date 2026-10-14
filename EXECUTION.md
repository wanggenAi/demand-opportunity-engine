# Operate the money loop

Python 3.11+ standard library only. Run from repository root:

~~~sh
PYTHONPATH=src python3 -m demand_opportunity_engine.cli discover
PYTHONPATH=src python3 -m unittest discover -s tests -v
~~~

Discovery splits routes in data/discovery_config.json: explicit buyer requests via public n8n Jobs JSON, Remotive job API, procurement/RFQ pages, bounty pages and Reddit request pages; HN/GitHub pain feeds remain PRODUCT_SIGNAL inputs. Primary buyer quotes, original post dates and visible replies are retrieved, snapshots saved with SHA256, canonical URLs upserted, and DISCOVERED recorded once. Access errors remain visible in BUYER_INTENT_DISCOVERY.md. No paid API, login or evasion. Remotive is attributed and delayed 24h: do not run its API more than four times per day; remove that adapter config when refreshing other sources more frequently.

Use the report command without fetching. --as-of 2026-10-13T04:00:00Z makes time gates reproducible. Adapter failures are recorded in data/discovery_run.json, never fabricated as success. Retained records keep their prior observed_at. GitHub comments are fetched up to 100; incomplete counts become UNKNOWN competition.

data/opportunities.json is the unchanged V1 seed/audit fixture. It contains interpreted and sometimes misattributed evidence and is deliberately excluded from V2 ranking, clusters and edges. Do not ingest it as verified primary evidence.

data/info_edges.json holds verified current web changes, separate from demand discovery: Haiku launch/pricing cross-checked against an independent benchmark, and n8n Assistant credit top-ups verified through the official public forum API. No target-buyer awareness gap is established; no edge is promoted. Never replace event dates with collection time. data/search_discovery_audit.json retains the manual public-search fallback, queries, primary vs indirect verification and rejections. It is an audit supplement, not an automated search adapter or live lead feed.

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

MANY VALIDATIONS, FEW HEAVY COMMITMENTS. Up to five independent CONTACT_TODAY candidates plus real due FOLLOW_UPs; DO NOW may be empty. VALIDATE means confirm need, permission and payment; it does not authorize pitching every bug reporter. Price ranges are test proposals for Brain/human review, never buyer budgets. No warehouse, QC, freight or specialist capacity is assumed.

Discovery is rerunnable on demand; no scheduler is installed this sprint. Reddit returned HTTP 403 and browser-harness initialization failed; no Reddit refresh is claimed.

## Buyer-intent hard gate

DIRECT_LEAD requires BUYER plus one supported commercial_intent_type and an exact author-written commercial_intent_quote, matching the deterministic source-only classifier. NONE, service ads, quoted hiring references, generated task digests and ordinary bug reports cannot become sales recommendations. Labels and derived prose add no second payment score. Source contact/application paths are mandatory. 0–3-day requests rank ahead of 4–7-day requests; 8–14 days require buyer renewal for DO NOW. Unknown/high competition and uncontrolled capabilities still block immediate action. Ordinary observers remain available in PRODUCT_THESIS only.

CONTACT_TODAY is selected only from unchanged DO NOW hard gates. If empty, there is no qualified buyer; independent product/info validations continue. VALIDATE_FIRST is a bounded desk permission/fit check, not a sales commitment. A real CONTACTED event must use the actual opportunity ID and actual channel; only then does the next report consume it.

## Fourth sprint: bounded markets and stop rule

`market_sources` now tests four independent public ecosystems, with explicit per-family page caps. Server-rendered Freelancer startTime, budget and bidCount are primary source fields; unknown employers never inflate independent clusters. Shopify support requests stay product pain unless the author explicitly invites paid work. Indie Hackers self-promotion and physical RFQs are audited separately from service leads. Raw same-round cache replay is disclosed in discovery_run, not called a fresh network read.

Reports now include SOURCE_YIELD.md and TOOL_OPPORTUNITIES.md. Tools are PRODUCT_SIGNAL, with BUILD NOW / VALIDATE / WATCH / REJECT; keyword hypotheses are not volume. Current manually reviewed tool assessments retain original evidence/check dates, so scheduled reports cannot silently refresh their freshness or assert new SEO demand. Future supply/demand research must update actual evidence before promotion.

`.github/workflows/daily-discovery.yml` schedules one daily run at 02:15 UTC (10:15 Shanghai), plus workflow_dispatch. Push runs tests only. Source errors are audited individually; artifacts are retained before normal data/report pushes. No forced pushes. The old "no scheduler installed" sentence above describes the third sprint only.

Outcome ranking additionally consumes source family, opportunity type and offer cohorts. Actual grouped realized ticket/cycle metrics inform source and price assumptions; absent sales events remain neutral. No claimed revenue from proposed prices. After a bounded source test yields no qualified outreach or build, stop. Do not use the first high-competition VALIDATE item as an automatic outreach recommendation.

## Daily portfolio execution

The report/discover commands write DAILY_MONEY_PORTFOLIO.md, a matching TODAY_MONEY_BOARD.md and DAILY_PORTFOLIO.json. FIRST CONTACT <=5, FOLLOW_UP <=5; product validation <=5 and info validation <=5; total validation <=15. Heavy build/delivery caps are 2/3. Qualified contacts sort by portfolio_priority after truth gates; missing financial history stays UNKNOWN with neutral factors. Due intervals: CONTACTED/QUOTED 2 days, REPLIED/QUALIFIED 1 day; timestamps are UTC, future events ignored, WON/LOST conversations excluded.

Optional human state file data/portfolio_state.json has active_builds (tool candidate IDs) and active_deliveries (opportunity IDs). Absent file means no active work reported. Listing an ID does not bypass gates: build needs verified tester commitment, competitor pricing, five independent demands on >=2 platforms and >=2 primary payment signals; delivery needs real WON. Real overflow is disclosed and pauses new contacts, not silently hidden. WON without reported delivery status remains explicitly unconfirmed.

Build evidence in data/tool_opportunities.json: build_evidence.competitor_prices and .tester_commitment each require verified=true, source_url and exact_quote; standardized_delivery must be confirmed. Demand items retain platform, primary_verified, author_key and primary payment_quote/payment_primary_verified. Never manufacture these fields to pass a gate.

Optional outcome human_minutes is actual reported time per event; do not enter planning estimates. Price learning shows real QUOTED ranges separately from realized REVENUE by currency. Realized revenue/hour uses recorded time only, so missing time stays unknown. No account creation, outreach sending, charging or payments are performed by discovery/report generation.

Existing INFO_EDGE primary URLs are rechecked during discover using the existing public HTTP fetcher. A matching primary quote refreshes verification only; event dates, awareness gaps and buyer intent are never renewed. Each failure is audited and leaves the previous verification time unchanged; expired events are not refetched or rejuvenated. New information windows still need independent primary evidence and awareness/payment validation.
