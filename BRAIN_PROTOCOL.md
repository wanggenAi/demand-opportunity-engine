# Brain ↔ Codex Protocol

This repository uses a strict separation of responsibilities.

## ChatGPT (Brain)
Owns:
- market thesis
- opportunity taxonomy
- prioritization
- scoring philosophy
- monetization logic
- offer design
- outreach strategy
- acceptance/rejection of Codex work
- deciding the next experiment

ChatGPT does **not** optimize for software elegance. It optimizes for evidence that moves toward revenue.

## Codex (Execution Operator)
Owns:
- implementation
- legal/reliable data collection
- normalization/deduplication
- deterministic scoring implementation
- tests
- scheduled workflows
- report generation
- data quality checks
- outcome logging

Codex must not silently redefine business priorities. When a choice changes what market to pursue, what counts as evidence, how money is made, or which opportunity should be pursued, surface the choice rather than embedding it as an engineering assumption.

## Human Operator
Owns:
- real conversations
- trust building
- outreach approval/sending where needed
- negotiation
- payment
- final business decisions
- reporting real outcomes back into the system

## Iteration loop
1. Brain defines objective and acceptance criteria.
2. Codex implements and produces evidence/results.
3. Brain reviews output against revenue criteria.
4. Human executes the highest-value real-world action.
5. Outcome is recorded.
6. Brain adjusts priorities/scoring based on outcome.
7. Codex implements the next iteration.

## Mandatory handoff format from Codex
Every meaningful execution round must end with:

1. What changed
2. Current DIRECT_LEAD portfolio
3. Current PRODUCT_SIGNAL portfolio
4. Current INFO_EDGE portfolio
5. Follow-ups
6. Active builds
7. Active deliveries
8. Today's recommended action portfolio
9. Estimated total human time
10. Blockers
11. Revenue impact hypothesis

Include primary evidence/provenance, test/discovery status and actual outcome counts. Finish with the concrete 5–10 actions supported by evidence for a human with 4–6 available hours. Do not invent actions to fill time, sales outcomes, budgets or expected revenue. Multiple small validations/outreaches are allowed; heavy WIP remains bounded. No handoff consisting only of code/test completion.
