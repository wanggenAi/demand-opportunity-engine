# SECOND SPRINT — SIGNAL QUALITY + LIVE DISCOVERY

## Objective

Turn V1 from a static seeded ranking demo into a repeatable revenue radar that can surface current, contactable opportunities and learn from human outcomes.

Do not expand into a product platform. This sprint is about **better money decisions**.

## P0 acceptance criteria

### 1. Add source-truth fields

Each opportunity must distinguish:

- `raw_evidence_quote`: verbatim or tightly preserved source evidence
- `payment_signal_type`: one of `EXPLICIT_BUDGET`, `FEE_REQUEST`, `HIRING`, `COMMERCIAL_INTENT`, `INFERRED`
- `published_at`
- `buyer_activity_at` when the buyer/OP has recent follow-up activity that can be verified
- `target_profile_url` or another concrete public contact target
- `seller_competition_count` or an evidence-backed competition bucket
- `fulfillment_mode`: `REMOTE`, `LOCAL_PHYSICAL`, `PARTNER_REQUIRED`, `SPECIALIST_REQUIRED`

Analyst-written summaries must never be scored as raw evidence.

### 2. Make freshness a hard gate

For `DIRECT_LEAD`:

- `DO NOW` normally requires source age <= 14 days.
- A source older than 14 days may enter `DO NOW` only if there is verifiable **buyer/OP activity** within the last 7 days.
- Anything older than 30 days without recent buyer activity cannot be `DO NOW`.

For `INFO_EDGE`:

- source/event age <= 14 days is mandatory;
- preferably <= 7 days;
- at least two independent evidence points are required before recommending monetization.

Do not treat seller comments as proof that the buyer is still active.

### 3. Rebuild payment scoring

Do not double-count one keyword score as both `payment` and `evidence`.

Score separately:

- source authenticity / quote quality
- payment intent
- urgency
- reachability
- freshness / buyer activity
- operator capability fit
- competition pressure
- expected value / likely ticket
- repeatability
- confidence

The score explanation must show the components.

### 4. Measure competition

For public posts, estimate how crowded the lead is using actual relevant replies where technically possible.

A two-week-old post with many agents already pitching should be materially penalized versus a fresh post with few/no service pitches.

### 5. Capability-aware ranking

Do not assume the operator owns a warehouse, QC team, freight license, physical inspection network, legal/compliance expertise, or category-specific certification expertise.

High-priority initial offers should favor capabilities that can be delivered immediately, such as:

- supplier/company research
- supplier verification desk memo
- 1688 / factory shortlist research
- RFQ translation and structured comparison
- competitor / market research
- public-data lead research
- AI/business automation discovery and implementation within known software capabilities

If physical or specialist delivery is required, label it `PARTNER_REQUIRED` or `SPECIALIST_REQUIRED` and reduce immediate-action priority until a partner path exists.

### 6. Build real PRODUCT_SIGNAL clusters

Create demand clusters from independent buyer evidence.

A product thesis may be promoted only when all are true:

- >= 5 independent buyer/problem observations
- evidence spans >= 2 sources or communities where possible
- >= 2 observations have explicit commercial/payment signals, or there is strong existing paid-market evidence
- the repeated problem is narrow enough to standardize
- there is a plausible distribution channel to the same buyer type

Output `reports/PRODUCT_THESIS.md` with at most 3 theses.

For each thesis include:

- repeated job-to-be-done
- unique buyer count
- representative evidence URLs
- existing alternatives / free competition
- why a Skill/Tool/Service might still win
- simplest pre-build validation experiment

No product implementation is allowed until the validation experiment is run.

### 7. Build real INFO_EDGE detection

Output `reports/INFO_EDGE_BOARD.md` with at most 3 items.

Each item must include:

- what changed
- exact date
- why target users may not know yet
- two independent sources when possible
- target buyer group
- monetization path
- expected decay window
- legality/compliance check
- 24–48 hour validation action

Old launches are background research, not INFO_EDGE.

### 8. Wire outcome feedback into ranking

Support events at minimum:

- `CONTACTED`
- `REPLIED`
- `QUALIFIED`
- `QUOTED`
- `WON`
- `LOST`
- `REVENUE`

The next ranking run must consume these events.

At minimum, source/channel/cluster conversion history should influence future priority. Keep the learning transparent and deterministic; no ML is required.

### 9. Demonstrate repeatable live discovery

Implement the smallest compliant/free discovery path possible. Prefer public feeds/APIs/search endpoints over brittle scraping.

Minimum: at least 2 independently refreshed public source adapters and an ingestion command that can add/update opportunities without hand-editing `opportunities.json`.

Do not require paid APIs for this sprint.

### 10. Board output must be executable

`TODAY_MONEY_BOARD.md` must contain at most:

- 3 `DO NOW`
- 3 `VALIDATE`
- 5 `WATCH`

Every `DO NOW` must include:

- concrete target profile/contact path
- source age and buyer-activity age
- competition evidence
- capability/fulfillment mode
- expected ticket range
- offer to test
- one short outreach draft
- reason it beats the other candidates today

If there are no sufficiently fresh opportunities, `DO NOW` is allowed to be empty. **Do not fill slots with stale leads just to make the report look complete.**

## Tests required

Add tests proving:

1. a stale high-keyword lead cannot become `DO NOW` without recent buyer activity;
2. recent buyer activity can revive an older lead;
3. analyst inference cannot masquerade as explicit payment evidence;
4. high seller competition reduces ranking;
5. physical/specialist fulfillment reduces immediate fit where no partner exists;
6. outcome events change later priority in the intended direction;
7. INFO_EDGE rejects stale items;
8. product thesis threshold is based on independent observations, not one record;
9. live ingestion is idempotent/deduplicated.

## Mandatory handoff

When finished, return:

1. What changed
2. Live sources actually refreshed
3. New evidence collected and its date distribution
4. TODAY_MONEY_BOARD result
5. PRODUCT_THESIS result
6. INFO_EDGE_BOARD result
7. Outcome-feedback behavior demonstrated
8. Tests run / result
9. Remaining blockers
10. If the human can do only one revenue action today: exactly what, to whom, through which URL/contact path, with what offer

## Forbidden scope

Do not build:

- dashboard UI
- login/auth
- SaaS billing
- vector database
- generic agent framework
- broad scraping infrastructure
- paid-data dependencies

until signal quality and first-contact conversion have been demonstrated.
