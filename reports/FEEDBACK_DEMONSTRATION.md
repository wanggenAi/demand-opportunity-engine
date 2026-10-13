# Outcome feedback demonstration

CONTROLLED SYNTHETIC FIXTURES ONLY — not real market outcomes.

Temporary stores and JSONL event logs were read by the same load_outcomes → rank → score_opportunity path used in production. No fixture event was appended to data/outcomes.jsonl.

- neutral: future opportunity score=80.0; outcome adjustment=0.0; groups=[]
- success: future opportunity score=84.5; outcome adjustment=4.5; groups=['platform:Test', 'cluster:supplier_verification', 'channel:email']
- loss: future opportunity score=71.5; outcome adjustment=-8.5; groups=['platform:Test', 'cluster:supplier_verification', 'channel:email']

Success fixture: two prior contacted opportunities replied, qualified, quoted USD 200, won and realized USD 200 each; average cycle 1 day. Loss fixture: two contacts followed by explicit LOST events. Neutral fixture: no human conversion events.
History affects a new similar opportunity; it cannot override freshness, capability or payment gates. Production remains neutral because all real events are DISCOVERED.
