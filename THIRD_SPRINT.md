> Historical sprint brief. Its single-bet/old display caps are superseded by BRAIN_REVIEW_V4.md and PRINCIPLES.md.

# THIRD SPRINT — BUYER INTENT DISCOVERY

## Goal

Fix the current bottleneck: discovery finds fresh problems but almost no explicit buyers.

Do not redesign the system. Do not add UI, SaaS, login, payments or speculative products. Preserve V2 hard gates.

The sprint succeeds only if discovery broadens toward fresh public buyer-intent sources and the Money Board can distinguish:
- explicit commercial buyers
- problem observers
- sellers/service providers
- news/launches

## 1. Split discovery by route

Create independent source strategies for:

### DIRECT_LEAD
Only sources that can reasonably contain explicit commercial intent.

Search patterns should emphasize phrases such as:
- looking to hire
- hiring freelancer / consultant / agent
- need a vendor
- need sourcing agent / China sourcing / supplier verification
- RFQ / RFP / quote request
- paid task / bounty
- budget
- willing to pay
- looking for someone to automate
- need n8n / workflow / AI automation help
- procurement / supplier request

Use lawful public access only. No login bypass, CAPTCHA bypass, credential use, scraping evasion or ToS circumvention.

If direct platform APIs are blocked, use public search-engine-indexed pages/snippets or alternative public sources, and record that the source is indirect until the underlying page is opened and verified.

### PRODUCT_SIGNAL
GitHub issues, HN, public forums, repeated complaints, reviews and support discussions may remain here. Do not promote them to DIRECT_LEAD without explicit buyer-authored commercial intent.

### INFO_EDGE
Continue official announcements + independent corroboration. Do not promote because something is merely new.

## 2. Add a buyer-intent gate

A DIRECT_LEAD must carry a machine-readable `commercial_intent_type`, one of:
- BUDGET_STATED
- QUOTE_REQUESTED
- HIRING
- PAID_TASK
- BOUNTY
- AGENT_OR_VENDOR_REQUEST
- PROCUREMENT_REQUEST
- WILLING_TO_PAY
- NONE

`NONE` can never enter DO NOW.

Store the exact buyer-authored quote supporting the type.

## 3. Separate buyer from observer

Add/retain role classification:
- BUYER
- PROBLEM_OBSERVER
- SELLER
- NEWS

GitHub issue reporters default to PROBLEM_OBSERVER unless explicit primary text proves commercial intent.

Do not recommend unsolicited paid pitches to ordinary bug reporters.

## 4. Source diversification target

The sprint must attempt at least 4 distinct public source families beyond the existing HN/GitHub problem feed, subject to lawful accessibility.

Examples of source families:
- public freelance/job request listings
- public sourcing/procurement/RFQ listings
- search-engine-indexed Reddit/forum request posts
- public founder/operator communities
- public bounty/paid-task listings
- public business-service request boards

Do not count four query strings against the same site as four source families.

For each adapter/search path report:
- access method
- records inspected
- verified buyer requests
- explicit payment/commercial signals
- errors/limitations

## 5. Freshness

For DIRECT_LEAD:
- 0–3 days: strongest
- 4–7 days: acceptable
- 8–14 days: VALIDATE only unless renewed by buyer
- >14 days: not DO NOW without verified recent buyer activity

A newly indexed old page is still old.

## 6. Contactability

A high-ranked lead must have a legitimate contact path from the source:
- platform reply/application
- public contact form
- public business email
- public DM path where platform rules allow it

Do not harvest private contact data or infer hidden addresses.

## 7. Offer fit

For each commercial lead, produce:
- exact need
- commercial-intent quote
- why now
- what we can deliver REMOTE_NOW
- dependencies we do not control
- first narrow offer
- test price range
- effort estimate
- competition pressure
- first-message angle

For China sourcing, prioritize remote services we can actually perform first:
- supplier search
- supplier verification research
- RFQ preparation/translation
- quote comparison
- company background research
- shortlist/report

Do not promise warehouse/QC/DDP/on-site inspection unless a real partner is available.

## 8. Product opportunity gate remains strict

Do not build a Skill/Tool from the current workflow-reliability cluster.

Promotion requires at minimum:
- >=5 independent pains
- >=2 communities
- >=2 independent primary commercial/payment signals
- narrow standardized job
- identifiable distribution path

## 9. Information edge expansion

Attempt to identify multiple current edges, but promotion still requires:
- exact event date
- official source
- independent corroboration when material
- target buyer
- credible awareness gap evidence
- monetization path
- decay window
- legal/compliance check

Do not confuse lower price with monetizable information asymmetry.

## 10. Real human outcome loop

Do not fabricate CONTACTED/REPLIED/etc.

If the sprint produces a qualified commercial lead, surface exactly one PRIMARY OUTREACH candidate and one optional experiment.

Once the human actually contacts someone, the next report must consume the real event.

## Required outputs

Regenerate:
- `reports/TODAY_MONEY_BOARD.md`
- `reports/SOURCE_QUALITY_CHECK.md`
- `reports/PRODUCT_THESIS.md`
- `reports/INFO_EDGE_BOARD.md`
- `reports/OUTCOME_FEEDBACK.md`

Add:
- `reports/BUYER_INTENT_DISCOVERY.md`
- `reports/THIRD_SPRINT_HANDOFF.md`

## Acceptance criteria

1. Existing V2 tests remain green; add tests for commercial-intent gating.
2. GitHub ordinary bugs cannot enter DO NOW without explicit commercial intent.
3. At least 4 additional public source families are attempted and honestly reported.
4. Buyer-intent counts are reported separately from pain observations.
5. DIRECT_LEAD candidates preserve exact commercial-intent quotes and legitimate contact paths.
6. No stale lead is used to fill DO NOW.
7. No PRODUCT_SIGNAL is promoted without primary commercial evidence.
8. No INFO_EDGE is promoted without a verified information-gap hypothesis strong enough to act on.
9. If a qualified buyer exists, the handoff names one primary outreach candidate with source, need, offer, price test and first-message angle.
10. If no qualified buyer exists after broad discovery, report `DO NOW = 0` and explain which source families failed to yield buyers. Do not substitute bug reporters.

## Mandatory handoff

Return:
1. What changed
2. Sources attempted and access limitations
3. Explicit buyer-intent evidence collected
4. Money Board result
5. Product clusters
6. Information edges
7. Human action required
8. Outcome-feedback status
9. Blockers / uncertainty
10. Revenue impact hypothesis

Final line must answer:

> If the human can do only one thing today to move toward revenue, what exactly should they do, with whom, through what channel, offering what, at what test price—and what primary buyer-authored evidence justifies the action?

If there is no defensible answer, say so.