# Brain Review — V1

Status: **PARTIAL PASS**

The first money loop is directionally correct: the repository can represent evidence-bearing opportunities, rank them, cap human attention, and generate a `TODAY_MONEY_BOARD.md`. The sourcing demand discovered is real and commercially relevant.

However, this is not yet a production demand radar. It is currently a static seeded dataset plus deterministic ranking. The next sprint must improve revenue signal quality before expanding architecture.

## What passed

- 20 evidence-bearing source URLs are retained.
- All three routes exist in the dataset: `DIRECT_LEAD`, `PRODUCT_SIGNAL`, `INFO_EDGE`.
- The board is attention-capped.
- Direct leads include a source, buyer problem, payment rationale, contact path, offer, effort, and risk.
- Tests exist for the core ranking/validation behavior.

## P0 problems that can cause bad money decisions

### 1. Freshness is too weak

The quality report itself says `Fresh evidence published within 7 days: 0/20`, yet old candidates still enter `DO NOW`.

For a revenue-first system, stale demand must not outrank current demand merely because the text contains strong payment/reachability signals.

### 2. Payment/evidence is double-counted and partly analyst-authored

`evidence_strength()` is derived from the concatenation of `payment_intent_evidence` and `evidence_text`, while the same evidence strength is then weighted once as `payment` and again as `evidence`.

The system must distinguish raw source evidence from analyst inference. A generated phrase such as “explicitly asks...” must not become self-validating evidence.

### 3. Reachability is too abstract

`Reddit DM` is not enough. A `DO NOW` lead should identify the actual target account/profile or another concrete public contact path that the human can click and use immediately.

### 4. Competition is not measured from reality

A sourcing request with many agents already pitching the buyer is materially different from a fresh request with zero relevant replies. Current `competition_gap` is hand-scored rather than measured.

### 5. Operator fit is too coarse

Remote supplier research, translation, RFQ comparison, company verification, and desk research are different from physical factory inspection, warehousing, DDP fulfillment, or specialist compliance work. The system must not rank an opportunity highly if fulfillment requires capabilities not currently controlled by the operator.

### 6. Product opportunity detection is not yet a real cluster

Repeated sourcing leads are present, but a `PRODUCT_SIGNAL` should be based on multiple independent buyers exhibiting the same narrow paid problem, not merely a route label on individual records.

### 7. INFO_EDGE is not yet an information-arbitrage engine

Information edges must be recent by definition. Old Hacker News product launches are useful background evidence, but they are not current information asymmetry.

### 8. Outcome feedback is declared but not wired into prioritization

`data/outcomes.jsonl` exists and the board tells the operator to append events, but the ranking path does not consume those outcomes. Until replies, quotes, wins/losses, and revenue affect future ranking, there is no learning flywheel.

### 9. No repeatable live discovery loop yet

The current `data/opportunities.json` is a seeded snapshot. The next version must demonstrate repeatable acquisition from public sources and produce a changed board on a subsequent run without manually rewriting the dataset.

## Brain verdict

Do **not** build a dashboard, SaaS UI, login system, vector DB, or broad crawler platform next.

Fix signal quality first. The next sprint is successful only when the system can find newer opportunities, prove why they are actionable, and rank them using real buyer activity + competition + capability fit + feedback.
