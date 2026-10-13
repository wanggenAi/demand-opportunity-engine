# First Sprint — Prove the money loop

## Objective
Do not build a complete platform. Prove that the repository can turn public market signals into a short list of real opportunities that a human can act on today.

## Required deliverables

### 1. Minimal data model
Create a simple opportunity schema/store that preserves:
- source URL
- source/platform
- observed timestamp
- evidence text
- candidate route(s): DIRECT_LEAD / PRODUCT_SIGNAL / INFO_EDGE
- payment-intent evidence
- urgency
- reachability
- operator fit
- repeatability
- competition gap
- information-decay risk
- confidence
- suggested next action

### 2. Ingest at least 20 real opportunities
They must be evidence-bearing and currently relevant enough to validate.

Use legal/reliable sources first. Do not waste the sprint fighting blocked platforms.

The initial sample should include all three routes, with emphasis on opportunities close to revenue:
- China sourcing / supplier research / local execution
- AI / business automation jobs or explicit requests
- repeated pains that could become Skills/tools/templates
- fresh information/price/channel gaps with a plausible legal monetization path

### 3. Deterministic scoring
Implement transparent scoring. No ML.

Strong signals:
- explicit budget/payment
- explicit request for help
- clear buyer identity or reachable account
- urgency/deadline
- repeat occurrence across independent users
- evidence of existing paid alternatives

Weak signals:
- likes/views alone
- generic trend commentary
- AI-generated market claims with no source evidence

### 4. Generate `reports/TODAY_MONEY_BOARD.md`
Global attention cap:
- DO NOW: max 3
- VALIDATE: max 3
- WATCH: max 5

Every DO NOW item must contain:
- what the buyer/problem is
- source URL
- why payment is plausible
- how to reach/validate
- suggested offer
- estimated effort/risk
- why it beats lower-ranked options

### 5. Outcome log
Add append-only feedback storage for:
- contacted
- replied
- qualified
- quoted
- won/lost
- revenue
- loss reason

### 6. Tests
Test only business-critical behavior:
- scoring order
- stale-evidence decay
- board attention caps
- rejection of evidence-free/speculative candidates

## Explicit non-goals
Do NOT build:
- web UI/dashboard
- authentication
- billing
- SaaS tenancy
- vector DB
- complex LLM orchestration
- elaborate crawler framework
- speculative forecasting model

## Acceptance criteria
This sprint passes only if:
1. At least 20 sourced opportunities are ingested.
2. Weak/noisy opportunities are rejected or demoted.
3. `TODAY_MONEY_BOARD.md` is generated successfully.
4. The top items are concrete enough for a human to contact/validate immediately.
5. Every top item has provenance and a real next action.
6. Codex reports which single opportunity it believes deserves the human's attention first, while leaving the final business judgment to ChatGPT/human.

## Final handoff
Use the format in `BRAIN_PROTOCOL.md`.
