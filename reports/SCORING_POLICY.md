# Signal-quality scoring policy

These are visible implementation choices for the Brain-defined evidence hierarchy, not validated market beliefs. Brain/human may revise the weights after actual outcomes.

- Source authenticity: 15 for a preserved exact primary quote from a refreshed public source.
- Primary payment counted once: budget 25; hiring 22; fee request 20; commercial intent 15; inferred or negative intent 0.
- Urgency: 5 only for primary deadline/asap/urgent words.
- Concrete profile: 10; it proves a public contact target, not buying authority.
- Freshness: 15 for <=7 days; 7 for 7–14 days; 0 otherwise. Verified OP follow-up can renew age; seller replies, updated_at and collection timestamps cannot.
- Capability: REMOTE_NOW 15; PARTNER_REQUIRED 3; LOCAL_PHYSICAL 0; SPECIALIST_REQUIRED -8.
- Competition: LOW 0; MEDIUM -8; HIGH -20; UNKNOWN -12. Five distinct providers, a mature service quote or buyer-reported many DMs means HIGH. Incomplete replies cannot imply LOW. Counts are observed lower bounds.
- Commodity risk: -4; analyst-authored differentiation does not erase it.
- Expected ticket: 0–5 from a numeric primary buyer budget only; proposed offer prices earn zero.
- Measurable cost: 4 for primary quantified downtime/manual-loss evidence.
- Repeatability: 0–5 from distinct author/content observations.
- Confidence: 0–5.
- Outcome feedback: >=2 contacts, Laplace-smoothed reply/quote/win rates and losses, currency-separated realized ticket and contact-to-win cycle. Overlapping platform/channel/cluster effects are averaged, not added. No history = neutral.
- Tie-break: stable opportunity ID, not a claim one market is better.

DO NOW requires every hard gate plus score >=65: verified buyer, open source, primary payment signal, concrete profile, source checked <=7 days, source published <=7 days or verified buyer activity <=7 days, REMOTE_NOW, measured LOW/MEDIUM competition, and complete offer/message/price. Already contacted or WON/LOST items are suppressed.

7–14-day demand is VALIDATE without renewed OP activity. Beyond 14 days, only verified OP activity within 7 days can revive it. Feedback and payment words cannot bypass gates.

INFO_EDGE requires event age <=14 days, two independent verified evidence points, a verified target-buyer information gap, a lawful monetization path and a stated decay window. Current public pricing without verified awareness gap is only a validation candidate.

PRODUCT OPPORTUNITY requires >=5 independent observations, >=2 communities, >=2 primary payment signals, a narrow standardized job and a distribution path. A repeated pain cluster is not yet a product opportunity; no product build without a validation experiment.
