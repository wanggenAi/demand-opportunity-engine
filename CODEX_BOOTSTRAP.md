# Codex execution brief — demand-opportunity-engine V0

You are the implementation operator, not the business strategist. The repository exists to produce revenue opportunities, not engineering output.

## First action
Read `README.md` and `PRINCIPLES.md` before changing anything.

## Hard constraints
- Do not build a dashboard, web app, auth system, SaaS billing, vector database, or elaborate architecture in V0.
- Do not scrape websites in ways that violate their terms, bypass access controls, or require evasion.
- Prefer public feeds/APIs/search results and manually verifiable sources.
- Never treat engagement alone as purchase intent.
- Every source item must preserve URL, timestamp, evidence text, and confidence.
- No product implementation without demand/payment evidence.
- Do not optimize for commit count, crawler count, lines of code, or scraped-row volume.

## V0 objective
Produce one daily artifact: `reports/TODAY_MONEY_BOARD.md`.

It must rank all three routes together:
1. DIRECT_LEAD
2. PRODUCT_SIGNAL
3. INFO_EDGE

Human attention is globally limited to:
- DO NOW: max 3
- VALIDATE: max 3
- WATCH: max 5

## Phase 1 sources
Implement only sources that can be collected legally and reliably without paid infrastructure. Start with:
- Reddit/public web discovery
- Hacker News
- GitHub public signals
- public product/skill marketplaces where permitted
- manually ingested URLs for Upwork/X/Xiaohongshu/other sources when automated retrieval is unreliable

Do not spend more time fighting one blocked source than the expected value of the data.

## Required opportunity fields
At minimum:
- id
- route candidates
- title/problem
- source platform
- source URL
- observed timestamp
- evidence text
- payment-intent evidence
- urgency evidence
- reachability/contact path
- operator fit
- competition gap
- repeatability
- information-decay risk
- confidence
- suggested next action
- suggested offer or validation step

## Scoring philosophy
Evidence strength ranking:
1. payment / paid job / purchase
2. explicit request for help/tool
3. repeated complaint with measurable cost
4. active search intent
5. engagement
6. speculation

Score for:
- payment intent
- reachability
- urgency
- operator fit
- evidence quality
- repeatability
- competition gap
- information decay

## Revenue feedback
Implement a minimal append-only outcome log with:
- opportunity_id
- contacted_at
- channel
- reply yes/no
- qualified yes/no
- quoted amount/currency
- won/lost
- revenue
- short loss reason

Future scoring must be able to learn from this log. Do not implement ML yet; simple aggregate feedback is enough.

## First acceptance test
The repository is useful only if it can ingest at least 20 evidence-bearing opportunity candidates, reject weak/noisy ones, and output a board where each DO NOW item has:
- real source URL
- identifiable demand
- route score
- reason it may pay
- reachable next step
- suggested offer/validation action

## Business guardrail
The project is successful when it increases conversations, quotes, wins and revenue. It is not successful merely because tests pass.

## STOP conditions
Before building any new subsystem, stop and ask whether the current evidence already supports contacting a buyer or validating a product. If yes, surface that action first rather than adding infrastructure.