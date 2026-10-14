import json
import tempfile
import unittest
from datetime import datetime, timezone
from dataclasses import replace
from demand_opportunity_engine.markets import freelancer_op, market_sources, project_document, advantage
from demand_opportunity_engine.action_reports import source_yield_report, tool_decision, TOOL_GATES
from demand_opportunity_engine.scoring import do_now_rejections
from demand_opportunity_engine.models import Outcome
from demand_opportunity_engine.feedback import feedback_adjustment
from demand_opportunity_engine.clusters import clusters
from demand_opportunity_engine.signals import normalize_intent

NOW = datetime(2026, 10, 14, 4, tzinfo=timezone.utc)


def project(**changes):
    raw = dict(projectId=123, title="China supplier research", description="I need a China sourcing agent to compare prices and prepare an RFQ.",
               startTime=int(NOW.timestamp()*1000)-3600000, endTime=int(NOW.timestamp()*1000)+86400000,
               latestActivityTime=0, status="active", budget={"min": 100, "max": 250}, formattedBudget="$100-250 USD",
               currencyDetails={"code": "USD"}, bids=[], bidStats={"bidCount": 0}, isLocal=False)
    raw.update(changes)
    return raw


class FourthSprintTests(unittest.TestCase):
    def op(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            return freelancer_op(raw, 'https://www.freelancer.com/projects/research/test', NOW, directory)

    def test_structured_primary_budget_not_analyst_payment_claim(self):
        op = self.op(project())
        self.assertIn("Budget: $100-250 USD", op.source_text)
        self.assertEqual(op.observed_budget["min"], 100)
        self.assertEqual(op.commercial_intent_type, "BUDGET_STATED")
        self.assertEqual(op.fulfillment_mode, "REMOTE_NOW")  # 'prices' must not match IC hardware.
        op.derived_interpretation = 'budget $9999 explicit paid hiring'
        self.assertEqual(op.payment_evidence_quote, "Budget: $100-250 USD")

    def test_bid_activity_never_revives_buyer_and_unknown_never_low(self):
        raw = project(startTime=int(NOW.timestamp()*1000)-30*86400000,
                      latestActivityTime=int(NOW.timestamp()*1000), bidStats={})
        op = self.op(raw)
        self.assertFalse(op.buyer_activity_verified)
        self.assertEqual(op.competition_pressure, "UNKNOWN")
        self.assertTrue(do_now_rejections(op, NOW))

    def test_real_bid_count_and_specialist_scope_block_outreach(self):
        op = self.op(project(description="I need a China sourcing agent for ASTM F963 compliance and factory audit.", bidStats={"bidCount": 32}))
        self.assertEqual(op.competition_pressure, "HIGH")
        self.assertEqual(op.fulfillment_mode, "SPECIALIST_REQUIRED")
        self.assertTrue(do_now_rejections(op, NOW))

    def test_full_marketing_funnel_not_counted_as_narrow_reporting_job(self):
        op = self.op(project(title='Meta lead generation', description='Build the full funnel, track leads in Meta Ads Manager and report weekly.'))
        op.cluster_name = 'marketing_report_automation'
        self.assertNotEqual(advantage(op).cluster_name, 'marketing_report_automation')

    def test_unresolved_employers_do_not_inflate_independent_paid_cluster(self):
        op = self.op(project())
        self.assertEqual(clusters([op,replace(op,id='another-project')]),[])

    def test_internal_acquisition_task_is_not_a_paid_customer_request(self):
        op = self.op(project())
        op.source_platform = 'GitHub'
        op.title = 'Company: zero-cost first-customer acquisition sprint'
        op.source_text = 'Acquire the first verified paying B2B customer, with $0 upfront spend.'
        op.raw_evidence_quote = op.source_text
        self.assertEqual(normalize_intent(op).commercial_intent_type,'NONE')

    def test_html_shell_not_a_project_and_source_failure_does_not_stop_next(self):
        with self.assertRaises(ValueError):
            project_document('<html>Please sign in</html>')
        config = {"market_sources": [
            {"family": "blocked", "url": "https://blocked.test", "kind": "founder", "target_pattern": "need", "max_pages": 1},
            {"family": "accessible", "url": "https://ok.test", "kind": "founder", "target_pattern": "need", "max_pages": 1}]}
        def fetch(url):
            if 'blocked' in url:
                raise PermissionError('403 no bypass')
            return '<a href="/post/no-paid-demand">a discussion</a>'
        with tempfile.TemporaryDirectory() as directory:
            rows, audits = market_sources(config, NOW, directory, fetch)
        self.assertEqual(rows, [])
        self.assertEqual(len(audits[0]['errors']), 1)
        self.assertEqual(audits[1]['records_inspected'], 1)

    def test_duplicate_market_categories_not_two_independent_families(self):
        a = dict(source_family='one marketplace', inspected_keys=['p1'], records_inspected=1, opportunity_ids=[],
                 verified_buyer_requests=0, records=[], limitations=[], errors=[])
        report = source_yield_report([], NOW, {'buyer_sources':[a,a]})
        self.assertEqual(report.count('| one marketplace |'), 1)
        self.assertIn('| one marketplace | 1 |', report)

    def test_tool_cannot_build_from_keyword_or_one_user_or_stale_supply(self):
        candidate = dict(gates={k: True for k in TOOL_GATES}, checked_at=NOW.isoformat(), demand_evidence=[])
        self.assertNotEqual(tool_decision(candidate, NOW)[0], 'BUILD NOW')
        candidate['demand_evidence'] = [dict(primary_verified=True,author_key='one')]*2
        self.assertNotEqual(tool_decision(candidate, NOW)[0], 'BUILD NOW')
        candidate['demand_evidence'].append(dict(primary_verified=True,author_key='two'))
        self.assertNotEqual(tool_decision(candidate, NOW)[0], 'BUILD NOW')  # No tester, prices or cross-platform paid proof.
        candidate['checked_at'] = '2026-09-01T00:00:00Z'
        self.assertNotEqual(tool_decision(candidate, NOW)[0], 'BUILD NOW')
        candidate['checked_at'] = NOW.isoformat()
        candidate['gates']['distribution_path'] = False
        self.assertNotEqual(tool_decision(candidate, NOW)[0], 'BUILD NOW')

    def test_real_feedback_consumes_source_offer_and_type_cohorts(self):
        op = self.op(project())
        other = replace(op, id='other')
        events = []
        for obj in [op, other]:
            for kind in ['CONTACTED','REPLIED','QUOTED','WON','REVENUE']:
                events.append(Outcome(obj.id+kind,obj.id,kind,NOW.isoformat(),'Freelancer',100 if kind in {'QUOTED','REVENUE'} else None,'USD' if kind in {'QUOTED','REVENUE'} else None))
        bonus, groups = feedback_adjustment(op, events, [op, other])
        self.assertGreater(bonus,0)
        for key in ['source:'+op.source_family,'offer:'+op.suggested_offer,'type:'+op.discovery_route]:
            self.assertEqual(groups[key]['win_rate'],1)
            self.assertEqual(groups[key]['average_ticket_by_currency'],{'USD':100})
        self.assertEqual(feedback_adjustment(op,[],[op,other])[0],0)


if __name__ == '__main__':
    unittest.main()
