# Fourth Sprint — find lower-competition buyers where we have an advantage

## Objective

Stop optimizing the scoring engine. Improve the **quality of where we look**.

The system already finds explicit commercial intent, but the current strongest source is highly saturated. This sprint must test additional lawful public buyer-intent markets and quantify which source families produce fresh, reachable, low/medium-competition buyers that match our real capabilities.

## 1. Keep the three routes separate

### DIRECT_LEAD
Search for primary/original posts where the author is explicitly asking to hire, buy, receive a quote, find a vendor/agent, commission a task, or procure a service.

### PRODUCT_SIGNAL
Use repeated independent pains and commercial requests to form narrow clusters. GitHub/HN are useful here, but ordinary bugs are not leads.

### INFO_EDGE
Track current verifiable changes only. Do not promote a novelty unless target-buyer awareness gap and monetization are evidenced.

## 2. Expand DIRECT_LEAD into operator-advantage markets

Test at least **four additional independent source families** beyond the existing n8n Jobs category. Different queries on the same site do not count as independent families.

Prioritize lawful public sources capable of surfacing:

- overseas buyers seeking China sourcing agents / supplier research / factory research
- China-side representative or coordinator requests
- supplier verification / due diligence requests
- RFQ / procurement / vendor comparison requests
- Chinese marketplace / 1688 / Alibaba research help
- technical sourcing for electronics / software / industrial products
- market research / competitor research / lead research jobs
- bounded automation / integration / QA jobs
- paid tasks / bounties / freelance requests with primary commercial text
- founder/operator communities with public job or vendor-request sections

Possible discovery mechanisms may include official APIs/RSS/JSON, public forum/category feeds, public request boards, search-engine discovery, and publicly accessible primary pages. Respect site terms, rate limits, robots/access controls and login boundaries. Do not bypass anti-bot controls.

Search-engine or aggregator results are discovery hints only. Promotion requires the original buyer page or another primary buyer-authored source.

## 3. Add operator-advantage evidence

For each commercial buyer, record deterministic fields or equivalent evidence for:

- `china_local_advantage`: NONE / LOW / MEDIUM / HIGH
- `language_advantage`: NONE / LOW / MEDIUM / HIGH
- `technical_advantage`: NONE / LOW / MEDIUM / HIGH
- `direct_contactability`: LOW / MEDIUM / HIGH
- `competition_pressure`: LOW / MEDIUM / HIGH / UNKNOWN
- `delivery_mode`: REMOTE_NOW / LOCAL_RESEARCH_NOW / PARTNER_REQUIRED / SPECIALIST_REQUIRED

These must be supported by the task text and our actually controlled capabilities, not optimistic prose.

A China-side request may score high for local/language advantage but must still be downgraded if it requires uncontrolled inspection, warehousing, freight, customs, certification or specialist liability.

## 4. Source-yield metrics

Generate `reports/SOURCE_YIELD.md` with one row per independent source family showing at least:

- records inspected
- primary buyer pages resolved
- explicit commercial buyers
- buyers published <= 7 days
- LOW/MEDIUM competition buyers
- capability-fit buyers
- contactable buyers
- `DO NOW` candidates
- buyer yield per 100 inspected
- actionable yield per 100 inspected
- access limitations / terms / failure reason

This report should answer: **where should the engine spend tomorrow's discovery budget?**

Do not celebrate raw record count.

## 5. DO NOW gate

Do not loosen V3 gates.

A `DO NOW` direct lead must have, at minimum:

- role = BUYER
- buyer-authored supported commercial intent type + exact quote
- primary/original source
- legitimate contact/application path
- fresh enough under current policy
- competition LOW or MEDIUM, not UNKNOWN/HIGH
- REMOTE_NOW or LOCAL_RESEARCH_NOW delivery, or another fully controlled bounded capability
- no fabricated portfolio/case-study requirement
- a concrete first offer we can actually deliver
- a truthful differentiator (`why us`) supported by operator advantage

`DO NOW = 0` is acceptable.

## 6. Buyer-market fit before outreach

For each top buyer, show:

- what they are buying
- exact commercial evidence
- why this buyer is still active
- competition evidence
- why we have an advantage
- what we cannot promise
- contact path and contact rules
- smallest paid offer
- observed budget, if stated; otherwise clearly label proposed test price
- estimated effort
- expected blockers

The board must distinguish `PRIMARY OUTREACH`, `VALIDATE`, and `WATCH`.

Only one `PRIMARY OUTREACH` may be recommended.

## 7. Product signal narrowing

Do not promote broad `workflow_reliability` merely because the count grows.

Attempt to split broad clusters into narrow standardized jobs using buyer and pain evidence, for example only when data supports them:

- voice-agent QA / stress testing
- paid marketing reporting automation
- supplier verification research
- supplier shortlist / RFQ preparation
- lead-research enrichment
- workflow health/reliability audit

Promotion still requires independent buyers, commercial signals, at least two communities/sources and a distribution path. Do not build the product this sprint.

## 8. Information-edge discipline

Continue current-edge tracking, but this sprint should not spend disproportionate engineering effort on it.

For any candidate, retain:

- exact event date
- primary official verification
- independent corroboration when material
- target buyer
- measured or interview-based awareness evidence
- monetization path
- decay window
- legal/compliance note

No verified awareness gap = no promoted edge.

## 9. Outcome feedback

Keep production outcome data truthful. Do not synthesize CONTACTED/REPLIED/QUOTED/WON/REVENUE.

If the human has not contacted anyone, feedback remains neutral.

## 10. Required outputs

Regenerate/update:

- `reports/TODAY_MONEY_BOARD.md`
- `reports/BUYER_INTENT_DISCOVERY.md`
- `reports/SOURCE_QUALITY_CHECK.md`
- `reports/SOURCE_YIELD.md`
- `reports/PRODUCT_THESIS.md`
- `reports/INFO_EDGE_BOARD.md`
- `reports/OUTCOME_FEEDBACK.md`
- `reports/FOURTH_SPRINT_HANDOFF.md`

## 11. Acceptance criteria

- test suite passes
- real lawful discovery is executed, not fixture-only
- at least 4 additional independent source families are attempted and audited
- n8n Jobs cannot account for more than 50% of newly verified commercial buyers unless the report explicitly proves all other attempted families yielded zero and explains why
- every promoted sales candidate has primary buyer-authored commercial evidence
- source-yield report is generated
- broad product clusters are narrowed or explicitly remain unvalidated
- no stale/high-competition/uncontrolled-capability lead is promoted just to fill the board

## Mandatory handoff

Return:

1. What changed
2. Source families attempted
3. Source-yield table and interpretation
4. Verified commercial buyers found
5. `DO NOW / VALIDATE / WATCH`
6. Product clusters
7. Information edges
8. Human action required
9. Blockers / uncertainty
10. Revenue impact hypothesis

Finally answer one question directly:

> If the human can make only one revenue-oriented move today, is there a defensible person/company to contact now? If yes, identify the exact buyer, source, offer, price basis, contact path, competition level and why we have a real advantage. If not, say no and identify which source family should be scanned next. Do not invent a lead.