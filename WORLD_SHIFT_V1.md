# World-shift V1 audit and operation

2026-11-03. Existing repository, branch `feature/world-shift-v1`, based on the current
`origin/main` after fetching its automated evidence updates. Read README, PRINCIPLES,
CODEX_BOOTSTRAP, EXECUTION and BRAIN_REVIEW_V4 before implementation. The explicit user
request authorizes this independent research module; the previous prohibition on crawler
expansion for commercial execution is not a reason to change the commercial system.

## Reuse and isolation

The existing Python standard-library CLI, public HTTP collection pattern, SHA256 evidence,
JSON stores, Markdown reports and unittest framework are reusable. Existing discovery has
HN/GitHub pain discovery, n8n/Remotive/buyer-market sources, primary-source rechecks,
commercial truth gates, outcome feedback, WIP limits and one daily workflow at 02:15 UTC.
Baseline: 59 tests passed. These modules, configuration, scoring, evidence and outcomes
remain untouched. The other Reddit business repository was neither read nor modified.

A new package under `src/demand_opportunity_engine/world_shift/` has an independent CLI;
there is deliberately no path from macro hypotheses into CONTACT_TODAY, BUILD or scores.
The new workflow is **workflow_dispatch only**, read-only repository permission, isolated
concurrency group, artifact output only. No new schedule or push to main is enabled.
Repeated unattended runs should retain downloaded artifact histories before the next run;
the workflow does not commit them. Local runs persist history normally.

## Commands

```sh
PYTHONPATH=src python3 -m demand_opportunity_engine.world_shift collect
PYTHONPATH=src python3 -m demand_opportunity_engine.world_shift report --review data/world_shift/review_2026-11-03.json
PYTHONPATH=src python3 -m unittest discover -s tests -q
```

`collect` uses actual current UTC, 30-day focus and 90-day context. There is no fake historical
`--as-of` collection option. `report` is offline. Analyst reviews retain their own date and
source references; they are never silently refreshed. The dated review file is an explicit
human-readable research artifact, not an LLM source of new facts. Empty hypotheses are valid.
Default collect emits conservative baseline reports without promoting unreviewed hypotheses.

## Evidence contract

`data/world_shift/events.json`: source URL/name, original source date strings, normalized dates,
first collection and last verification, country/industry, event type, excerpt, possible economic
constraint/value chain (UNKNOWN until reviewed), procurement/payment evidence, credibility,
unknowns, prior snapshot comparison. Dated analyst reasoning and five-dimensional judgments
live separately in `review_2026-11-03.json` and are rendered with primary references.
`runs/`: immutable per-run results. `snapshots/`: content-addressed original public responses.
`latest_run.json`: index to latest attempt, including all failures and missing fields.
Date-only values retain original precision; midnight UTC is a sorting convention, not an
assertion of event time. Procurement notice publication, award notification, deadline and
collection have separate fields. Signed contract disclosure is not cash receipt or revenue.

Exact canonical URLs deduplicate across queries; World Bank project+procurement reference
clusters repeat notices/lots under one demand. Original notice records and different award
values remain preserved. Macro reports count clusters separately from unique notice records.
Semantic syndication across different URLs still needs a shared explicit cluster key/manual
review; no media syndication feeds are used in V1. Never infer independent demand from a
count of raw rows. Source counts are sample coverage, not market size.

Single snapshots are baseline. Two observations, including same-day debugging runs, are
explicitly NOT sustained growth; platform downloads never establish paying demand.
No source failure renews old verification or erases history. HTTP 200 shells fail collection.
One retry for transient failures, 20-second timeout, 3MB response cap, serial requests with
0.3-second minimum spacing; no retry for access denials, credentials, login or evasion.

## Real-run corrections and limits

Several real bounded runs were made while validating adapters and date parsing; they are
all retained. Corrections included RSS whitespace, date-only host timezone conversion,
award-event vs publication date, HTML-shell rejection and HTTP-status vs adapter-status
separation. These runs are engineering checks of one baseline, not a longitudinal trend.
An early Alibaba shell record is retained for audit but invalidated by the latest failure;
it must not be used as substantive evidence. Current reports use only latest successful
verification plus the explicitly dated review. Historic reports can be reconstructed from
run records and snapshots; generated four report names are latest views. Dated review files
are never overwritten by collection.

GitHub anonymous API, Reddit and SEC reject access. Alibaba's public HTML is a navigation
shell; Chrome browser-harness daemon could not start. Its search preview is excluded from
findings. No further evasion attempted. MIDA generic RSS contains promotional events and
one title/description mismatch (DENSO/Air Liquide); it is not evidence of signed orders.
Dedicated MIDA releases were separately fetched. NDRC index publication dates are not legal
effective dates; one full formal reply is fetched, while precise legal effects remain unscored.
TED, NDRC-adjacent ministries, recruitment and broad corporate filings remain future coverage;
not claimed as connected. Six evidence categories have successful public sources, but demand
coverage is weak: HN discussions, no validated overseas purchasing cohort. No country-specific
legal conclusion, customer count, cross-border revenue or compute deployment location is known.

World Bank queries each return 25 latest matches without exhaustive paging. Keyword matches
are noisy; only analyst-selected entries are signals. HF download counts are one-platform rolling
metrics. Page change logs may contain many older entries; the specifically referenced section
and date are explicit in review, not the entire page relabeled as new. Some procurement budgets
are not disclosed, while exact signed-price source text is preserved separately. Report links
point to official notice pages; structured API response snapshots remain the evidence if the
HTML viewer requires JavaScript. `link_verification.json` documents selected direct checks.

Next investigation priorities: procurement qualification/small service gaps; overseas model
buyers' paid production workloads and hosting location; repeated domain-data specification
contracts and existing qualified suppliers. These are desk investigations, not authorized outreach.
