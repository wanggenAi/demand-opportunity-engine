import unittest
from dataclasses import replace
from demand_opportunity_engine.models import Outcome
from demand_opportunity_engine.portfolio import daily_portfolio, render_portfolio, priority
from demand_opportunity_engine.feedback import grouped_metrics, metrics
from demand_opportunity_engine.action_reports import tool_decision, TOOL_GATES
from demand_opportunity_engine.reports import refresh_known_edges
from unittest.mock import patch
from test_engine import opportunity, event, NOW
import test_engine


class PortfolioTests(unittest.TestCase):
    def test_info_recheck_failure_does_not_renew_and_expired_event_not_fetched(self):
        fresh = test_engine.ProductEdgeTests().edge()
        old = replace(fresh, id="old", published_at="2025-01-01")
        observed, published = fresh.observed_at, fresh.published_at
        def blocked(url):
            raise PermissionError("403; no bypass")
        audits = refresh_known_edges([fresh, old], NOW, blocked)
        self.assertFalse(audits[0]["refreshed"])
        self.assertIn("403", audits[0]["error"])
        self.assertIn("expired", audits[1]["reason"])
        self.assertEqual((fresh.observed_at, fresh.published_at), (observed, published))
        with patch("demand_opportunity_engine.discovery.snapshot", return_value=("audit.json", "digest")):
            self.assertTrue(refresh_known_edges([fresh], NOW, lambda url: fresh.raw_evidence_quote)[0]["refreshed"])
        self.assertEqual(fresh.published_at, published)

    def test_multiple_contacts_without_relaxing_zero_cost_competition_or_freshness(self):
        good = [opportunity(str(i)) for i in range(8)]
        bad = [opportunity("paid", acquisition_cost="REQUIRED_PAID"),
               opportunity("unknown", competition_pressure="UNKNOWN"),
               opportunity("stale", published_at="2025-01-01"),
               opportunity("specialist", fulfillment_mode="SPECIALIST_REQUIRED")]
        p = daily_portfolio(good + bad, NOW)
        self.assertEqual(len(p["CONTACT_TODAY"]), 5)
        self.assertFalse({r["id"] for r in p["CONTACT_TODAY"]} & {o.id for o in bad})
        self.assertEqual(p["ACTIVE_BUILDS"], [])
        self.assertEqual(p["FOLLOW_UP"], [])
        self.assertIsNone(p["CONTACT_TODAY"][0]["expected_value"]["amount"])

    def test_followups_due_real_contacts_only_closed_and_future_excluded(self):
        ops = [opportunity(k) for k in ("waiting", "quoted", "fresh", "won", "lost", "future", "observer")]
        events = [event("waiting", "CONTACTED"), event("quoted", "CONTACTED"),
                  event("quoted", "QUOTED", amount=150, currency="USD"),
                  event("fresh", "CONTACTED", day=13), event("won", "CONTACTED"), event("won", "WON"),
                  event("lost", "CONTACTED"), event("lost", "LOST"), event("future", "CONTACTED", day=20)]
        p = daily_portfolio(ops, NOW, events)
        self.assertEqual({r["id"] for r in p["FOLLOW_UP"]}, {"waiting", "quoted"})
        self.assertNotIn("fresh", {r["id"] for r in p["CONTACT_TODAY"]})
        self.assertEqual(p["ACTIVE_DELIVERY"], [])  # WON alone doesn't claim delivery is underway.
        self.assertEqual(daily_portfolio(ops, NOW, events, state={"active_deliveries": ["won", "observer"]})["ACTIVE_DELIVERY"][0]["id"], "won")

    def test_three_routes_coexist_and_partial_product_demand_never_builds(self):
        ops = [opportunity("supplier"), opportunity("workflow", cluster_name="workflow_reliability")]
        edge = test_engine.ProductEdgeTests().edge()
        p = daily_portfolio(ops + [edge], NOW)
        self.assertEqual(len(p["PRODUCT_VALIDATIONS"]), 2)
        self.assertEqual(len(p["INFO_EDGE_VALIDATIONS"]), 1)
        self.assertTrue(all(r["build_status"] == "NO BUILD" for r in p["PRODUCT_VALIDATIONS"]))
        text = render_portfolio(p)
        for section in ("CONTACT TODAY", "FOLLOW UPS", "PRODUCT VALIDATIONS", "INFO EDGE VALIDATIONS", "ACTIVE BUILDS", "ACTIVE DELIVERY", "TODAY ACTION PLAN"):
            self.assertIn(section, text)

    def test_historical_price_conversion_cycle_and_actual_time_change_allocation(self):
        ops = [opportunity("a"), opportunity("b")]
        events = []
        for op in ops:
            events.extend([replace(event(op.id, "CONTACTED"), human_minutes=10),
                           event(op.id, "REPLIED"), event(op.id, "QUOTED", amount=100, currency="USD"),
                           event(op.id, "WON", day=9), event(op.id, "REVENUE", day=9, amount=100, currency="USD")])
        groups = grouped_metrics(events, ops)
        neutral = priority(ops[0], {})
        learned = priority(ops[0], groups)
        self.assertIsNone(neutral["probability_of_conversion"])
        self.assertEqual(learned["speed_to_cash"]["observed_average_days"], 1)
        self.assertEqual(learned["expected_value"]["amount"], 75)
        self.assertNotEqual(neutral["portfolio_priority"], learned["portfolio_priority"])
        self.assertEqual(metrics(events)["revenue_per_recorded_hour_by_currency"], {"USD": 600})
        self.assertEqual(metrics(events)["quoted_range_by_currency"]["USD"]["max"], 100)
        self.assertEqual(groups["price:USD:<=100"]["win_rate"], 1)
        self.assertGreater(priority(ops[0], groups, human_minutes=10)["portfolio_priority"],
                           priority(ops[0], groups, human_minutes=180)["portfolio_priority"])
        with self.assertRaises(ValueError):
            replace(events[0], human_minutes=-1).validate()

    def test_source_outcomes_affect_portfolio_even_with_the_same_offer(self):
        ops = [opportunity(str(i), source_family="good" if i < 2 else "poor") for i in range(4)]
        events = [event(o.id, "CONTACTED") for o in ops]
        events += [event(o.id, "WON") for o in ops[:2]]
        events += [event(o.id, "LOST") for o in ops[2:]]
        groups = grouped_metrics(events, ops)
        self.assertGreater(priority(ops[0], groups)["portfolio_priority"], priority(ops[2], groups)["portfolio_priority"])

    def test_build_requires_real_tester_prices_cross_platform_and_paid_demands(self):
        c = {"id": "tool", "title": "Bounded tool", "gates": {k: True for k in TOOL_GATES}, "checked_at": NOW.isoformat(),
             "demand_evidence": [{"author_key": str(i), "primary_verified": True, "platform": "A" if i < 3 else "B",
                                  "payment_primary_verified": True, "payment_quote": "Budget $100"} for i in range(5)]}
        self.assertNotEqual(tool_decision(c, NOW)[0], "BUILD NOW")
        proof = {"verified": True, "source_url": "https://example.com/primary", "exact_quote": "I will test this paid pilot"}
        c["build_evidence"] = {"competitor_prices": {**proof, "exact_quote": "$20/month"}, "tester_commitment": proof, "standardized_delivery": True}
        self.assertEqual(tool_decision(c, NOW)[0], "BUILD NOW")
        self.assertEqual(daily_portfolio([], NOW, tool_candidates=[c])["ACTIVE_BUILDS"], [])
        self.assertEqual(len(daily_portfolio([], NOW, tool_candidates=[c], state={"active_builds": ["tool"]})["ACTIVE_BUILDS"]), 1)

    def test_heavy_wip_overflow_is_visible_and_blocks_new_commitments(self):
        ops = [opportunity(str(i)) for i in range(5)]
        events = [e for o in ops[:4] for e in (event(o.id, "CONTACTED"), event(o.id, "WON"))]
        p = daily_portfolio(ops, NOW, events, state={"active_deliveries": [o.id for o in ops[:4]]})
        self.assertEqual(len(p["ACTIVE_DELIVERY"]), 3)
        self.assertEqual(p["wip_overflow"]["ACTIVE_DELIVERY"], 1)
        self.assertEqual(p["CONTACT_TODAY"], [])


if __name__ == "__main__":
    unittest.main()
