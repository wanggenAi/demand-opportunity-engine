# demand-opportunity-engine

A revenue-first opportunity intelligence system.

Current acquisition budget = 0. Paid application channels are not primary execution channels. Only an evidenced ZERO-cost lawful contact path may enter DO NOW / PRIMARY OUTREACH; see PRINCIPLES.md and NEXT_ACTION.md. MANY VALIDATIONS, FEW HEAVY COMMITMENTS. The prior bounded market tests are complete; current execution follows the daily portfolio policy in BRAIN_REVIEW_V4.md.

## Mission
Continuously discover, verify, rank, and act on opportunities that can produce real revenue for a solo operator using AI/Codex as leverage.

## Three monetization routes
1. **DIRECT_LEAD** — a reachable person/business is explicitly asking for help and may pay now.
2. **PRODUCT_SIGNAL** — the same pain repeats across many users and can be productized into a Skill/tool/template/agent.
3. **INFO_EDGE** — valuable information, pricing, access, technology, channels, or rules are known earlier than the target market and can be monetized legally.

## Operating model
- **ChatGPT = brain:** market judgment, opportunity prioritization, offer strategy, outreach strategy, review and acceptance criteria.
- **Codex = execution operator:** implementation, collection, cleaning, enrichment, automation, tests and reports.
- **Human operator = CEO + sales:** trust, conversations, negotiation, payment, final decisions.

## North-star metrics
- Qualified reachable leads
- Conversations started
- Replies
- Quotes sent
- Deals won
- Revenue

Not metrics: commit count, crawler count, lines of code, dashboards, total scraped rows.

## Daily output
`reports/DAILY_MONEY_PORTFOLIO.md` is the primary output; `reports/TODAY_MONEY_BOARD.md` contains the same portfolio. Machine-readable details: `reports/DAILY_PORTFOLIO.json`.

DIRECT_LEAD, PRODUCT_SIGNAL and INFO_EDGE remain independent and run together. Recommend up to 5 qualified CONTACT_TODAY objects and 5 due FOLLOW_UPs, not just Top 1. Empty sections are honest results, never quotas.

## Human WIP
One human can run many small bets, but only a few heavy commitments. Defaults: 10–15 validations total; product validations <=5, presell/interviews <=3, info validations <=5; open quotes <=5; active product builds <=2; heavy deliveries <=3. WATCH can exceed 50. No build without repeated paying demand, current alternatives/prices, controlled delivery, distribution and a verified willing tester/preorder.

Read `PRINCIPLES.md` and `CODEX_BOOTSTRAP.md` before implementation.

## Run signal-quality discovery

Python standard library only. See [EXECUTION.md](EXECUTION.md) for discovery, reports and real outcome recording.

~~~sh
PYTHONPATH=src python3 -m demand_opportunity_engine.cli discover
PYTHONPATH=src python3 -m unittest discover -s tests -v
~~~

V1 data/opportunities.json is an audit seed; live ranking uses data/live_opportunities.json. See reports/SCORING_POLICY.md for hard gates and score weights.
