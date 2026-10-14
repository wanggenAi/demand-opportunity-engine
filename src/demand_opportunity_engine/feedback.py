from .models import timestamp

def metrics(events):
    """Distinct contacted opportunities form the cohort; absent events stay unknown."""
    contacted = {e.opportunity_id for e in events if e.event_type == "CONTACTED"}
    def cohort(kind):
        return {e.opportunity_id for e in events if e.event_type == kind} & contacted
    n, won = len(contacted), cohort("WON")
    totals, paying = {}, {}
    for e in events:
        if e.event_type == "REVENUE" and e.opportunity_id in won:
            totals[e.currency] = totals.get(e.currency, 0) + e.amount
            paying.setdefault(e.currency, set()).add(e.opportunity_id)
    cycles = []
    for oid in won:
        start = min(timestamp(e.occurred_at) for e in events if e.opportunity_id == oid and e.event_type == "CONTACTED")
        end = min(timestamp(e.occurred_at) for e in events if e.opportunity_id == oid and e.event_type == "WON")
        if end >= start:
            cycles.append((end - start).total_seconds() / 86400)
    quotes = {}
    for e in events:
        if e.event_type == "QUOTED" and e.opportunity_id in contacted:
            quotes.setdefault(e.currency, []).append(e.amount)
    minutes = sum(e.human_minutes or 0 for e in events
                  if e.opportunity_id in contacted and e.event_type != "DISCOVERED")
    return {
        "contacted": n, "reply_rate": len(cohort("REPLIED")) / n if n else None,
        "quote_rate": len(cohort("QUOTED")) / n if n else None,
        "win_rate": len(won) / n if n else None,
        "loss_rate": len(cohort("LOST")) / n if n else None,
        "average_ticket_by_currency": {c: round(v / len(paying[c]), 2) for c, v in totals.items()},
        "average_cycle_days": round(sum(cycles) / len(cycles), 2) if cycles else None,
        "quoted_range_by_currency": {c: {"min": min(v), "max": max(v), "observations": len(v)} for c, v in quotes.items()},
        "recorded_human_minutes": minutes,
        "revenue_per_recorded_hour_by_currency": {c: round(v * 60 / minutes, 2) for c, v in totals.items()} if minutes else {},
    }

def grouped_metrics(events, opportunities):
    index = {o.id: o for o in opportunities}
    groups = {}
    price_cohorts = {}
    for event in sorted(events, key=lambda e: timestamp(e.occurred_at)):
        if event.event_type == "QUOTED" and event.amount is not None and event.currency:
            band = "<=100" if event.amount <= 100 else ("100-250" if event.amount <= 250 else ("250-500" if event.amount <= 500 else ">500"))
            price_cohorts[event.opportunity_id] = f"price:{event.currency}:{band}"
    for event in events:
        op = index.get(event.opportunity_id)
        if not op:
            continue
        for key in (f"platform:{op.source_platform}", f"cluster:{op.cluster_name}", f"channel:{event.channel}",
                    f"source:{op.source_family}", f"type:{op.discovery_route}", f"offer:{op.suggested_offer}",
                    price_cohorts.get(event.opportunity_id, "price:")):
            if not key.endswith(":"):
                groups.setdefault(key, []).append(event)
    return {key: metrics(group) for key, group in sorted(groups.items())}

def feedback_adjustment(op, events, opportunities):
    groups = grouped_metrics(events, opportunities)
    chosen = {k: groups[k] for k in (
        f"platform:{op.source_platform}", f"cluster:{op.cluster_name}", f"channel:{op.contact_channel or op.source_platform}",
        f"source:{op.source_family}", f"type:{op.discovery_route}", f"offer:{op.suggested_offer}")
              if k in groups and groups[k]["contacted"] >= 2}
    baseline = metrics(events)
    adjustments = []
    for m in chosen.values():
        n = m["contacted"]
        r = (m["reply_rate"] * n + 1) / (n + 2)
        q = (m["quote_rate"] * n + 1) / (n + 2)
        w = (m["win_rate"] * n + 1) / (n + 2)
        adjustment = 8 * (r - .5) + 4 * (q - .5) + 6 * (w - .5) - 4 * m["loss_rate"]
        # Relative value/cycle correction, bounded, never mixes currencies.
        values = []
        for currency, ticket in m["average_ticket_by_currency"].items():
            average = baseline["average_ticket_by_currency"].get(currency)
            if average and ticket:
                values.append(max(-2, min(2, 2 * (ticket / average - 1))))
        adjustment += sum(values) / len(values) if values else 0
        cycle, avg_cycle = m["average_cycle_days"], baseline["average_cycle_days"]
        if cycle is not None and avg_cycle:
            adjustment += max(-1, min(1, 1 - cycle / avg_cycle))
        adjustments.append(adjustment)
    # Avoid counting the same history three times. This bonus cannot bypass gates.
    bonus = round(sum(adjustments) / len(adjustments), 2) if adjustments else 0.0
    return bonus, chosen
