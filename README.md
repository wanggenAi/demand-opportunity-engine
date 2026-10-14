# demand-opportunity-engine

A revenue-first opportunity intelligence system.

Current acquisition budget = 0. Paid application channels are not primary execution channels. Only an evidenced ZERO-cost lawful contact path may enter DO NOW / PRIMARY OUTREACH; see PRINCIPLES.md and NEXT_ACTION.md. Development is paused; the current test is bounded to ten original zero-cost buyer-request candidates.

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

## First product artifact
`reports/TODAY_MONEY_BOARD.md`

The board must contain no more than:
- 3 DO NOW actions
- 3 VALIDATE opportunities
- 5 WATCH items

Everything else stays in the opportunity store.

## Rule
The system may watch thousands of opportunities in parallel, but the human actively pursues only **one primary money problem plus one small experiment** at a time.

Read `PRINCIPLES.md` and `CODEX_BOOTSTRAP.md` before implementation.

## Run signal-quality discovery

Python standard library only. See [EXECUTION.md](EXECUTION.md) for discovery, reports and real outcome recording.

~~~sh
PYTHONPATH=src python3 -m demand_opportunity_engine.cli discover
PYTHONPATH=src python3 -m unittest discover -s tests -v
~~~

V1 data/opportunities.json is an audit seed; live ranking uses data/live_opportunities.json. See reports/SCORING_POLICY.md for hard gates and score weights.
