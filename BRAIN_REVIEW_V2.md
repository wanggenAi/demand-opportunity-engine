# BRAIN REVIEW V2

## Verdict

V2 substantially improved trustworthiness. It correctly allows `DO NOW = 0`, excludes stale V1 seeds, uses buyer-authored primary evidence, models public competition and delivery capability, clusters repeated pains, keeps information-edge promotion conservative, and consumes real outcome events in ranking. This is a real improvement.

However, V2 is still not yet a revenue-grade opportunity engine because discovery is dominated by low-commercial-intent sources.

Current live evidence says:
- 50 observations total
- 44 are 0–7 days old
- source roles: 16 SELLER, 26 PROBLEM_OBSERVER, 7 NEWS, only 1 BUYER
- 5 accepted demand/problem observations
- all 5 payment signals are INFERRED
- 0 qualified `DO NOW`
- production outcomes contain only DISCOVERED events; there is no CONTACTED/REPLIED/QUOTED/WON/REVENUE evidence yet

This means signal quality is now better than signal acquisition.

## What passed

1. **Freshness discipline passed.** Old leads are no longer backfilled into `DO NOW`.
2. **Primary-evidence discipline passed.** Derived prose no longer self-inflates payment scoring.
3. **Outcome plumbing passed.** Real outcome events can affect future ranking; synthetic outcomes are not inserted into production.
4. **Product restraint passed.** The workflow-reliability cluster is correctly marked UNVALIDATED because it has zero primary payment signals.
5. **Information-edge restraint passed.** Haiku 5.5 remains only a validation candidate because the information asymmetry is unproven.
6. **Engineering scope control passed.** No dashboard/SaaS/login/payment/vector-store expansion.

## Main failure

The discovery layer is looking where problems are discussed, not where money is actively being spent.

GitHub issues and ordinary Hacker News posts are useful for:
- pain discovery
- product-signal clustering
- technical trend detection
- information-edge research

They are poor primary sources for DIRECT_LEAD unless the primary text contains an explicit transactional signal such as:
- bounty
- paid task
- hiring
- budget
- seeking freelancer/consultant/vendor
- quote/RFP/RFQ request
- explicit willingness to pay

A bug reporter is not a buyer by default. Do not turn GitHub bug reports into a sales prospecting list.

## Third-sprint strategic decision

Do not spend the next sprint optimizing score weights.

The next bottleneck is **buyer-intent discovery and distribution**.

The engine should use different source portfolios for each route:

### DIRECT_LEAD source portfolio
Prioritize places where buyers explicitly request work, quotes, vendors, sourcing, consultants or freelancers. Examples include publicly accessible job/request marketplaces, buyer-request pages, public procurement/RFQ pages, public founder/operator request posts, and search-engine-indexed Reddit/forum demand posts. Use only lawful, public access; no login evasion or anti-bot bypass.

### PRODUCT_SIGNAL source portfolio
Keep GitHub issues, Hacker News, Reddit/forums, product reviews and repeated support complaints. These are for clustering repeated pains, not assumed sales leads.

### INFO_EDGE source portfolio
Official product/model/platform announcements, pricing pages, release notes, policy/rule changes and an independent corroborating source. Promotion still requires a credible target buyer, monetization path and time window.

## Human-sales rule

Until a source proves explicit commercial intent, GitHub/HN problem observers should not be the recommended primary sales action.

For the first real outreach experiment, prefer a person who has explicitly said one of:
- I am looking to hire
- looking for an agent/vendor/freelancer
- send pricing/quote
- budget is ...
- paid task/bounty
- need sourcing/procurement help
- willing to pay

The system's first money milestone remains:

`DISCOVERED -> CONTACTED -> REPLIED -> QUALIFIED -> QUOTED -> WON -> REVENUE`

The next sprint succeeds only if it materially increases the number of fresh, explicit buyer-intent observations and produces at least one ethical, defensible outreach candidate—or honestly reports none after broad buyer-intent discovery.