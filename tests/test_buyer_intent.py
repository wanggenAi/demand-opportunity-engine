import tempfile
import unittest
from dataclasses import replace
from test_engine import opportunity, result, NOW
from demand_opportunity_engine.signals import commercial_truth, normalize_intent
from demand_opportunity_engine.board import classify, build_board
from demand_opportunity_engine.discovery import make_op
from demand_opportunity_engine.buyer_discovery import discourse_jobs, inspect_public_path

class BuyerIntentTests(unittest.TestCase):
    def test_none_cannot_pass_even_with_payment_field_claim(self):
        op = opportunity()
        op.commercial_intent_type = 'NONE'
        self.assertNotEqual(classify(op,result(op)),'DO NOW')

    def test_analyst_claim_does_not_create_commercial_intent(self):
        text = 'I need help with a workflow bug.'
        op = opportunity(source_text=text,raw_evidence_quote=text,derived_interpretation='hiring, budget $1000, willing to pay')
        self.assertEqual(commercial_truth(op),('NONE',''))
        self.assertEqual(classify(op,result(op)),'REJECTED')
        self.assertNotIn('### 1.',build_board([op],NOW.isoformat()))

    def test_type_and_quote_must_match_primary_evidence(self):
        op=opportunity()
        op.commercial_intent_type='HIRING'
        self.assertNotEqual(classify(op,result(op)),'DO NOW')
        op=opportunity(contact_path='')
        self.assertNotEqual(classify(op,result(op)),'DO NOW')
        with self.assertRaises(ValueError):
            replace(op,commercial_intent_quote='fabricated quote').validate()

    def test_supported_types_and_seller_exclusion(self):
        cases={'BUDGET_STATED':'Budget $200 for our workflow.',
               'QUOTE_REQUESTED':'Please send pricing for our supplier search.',
               'HIRING':'Looking to hire a workflow developer.',
               'PAID_TASK':'Paid task: workflow testing.',
               'BOUNTY':'Bounty $200 for fixing automation.',
               'AGENT_OR_VENDOR_REQUEST':'I need a China sourcing agent.',
               'PROCUREMENT_REQUEST':'RFQ for automation services.',
               'WILLING_TO_PAY':'Willing to pay for workflow recovery.'}
        for kind,text in cases.items():
            op=opportunity(source_text=text,raw_evidence_quote=text)
            self.assertEqual(commercial_truth(op),(kind,text))
            seller=replace(op,title='[FOR HIRE] Automation services')
            self.assertEqual(commercial_truth(seller),('NONE',''))

    def test_service_ads_with_hiring_and_paid_trial_are_still_sellers(self):
        for title,text in [
            ('Open to Remote Opportunities','If anyone is hiring an n8n developer, DM me.'),
            ('Available for Hire','Paid trial workflow welcome.'),
            ('N8n Automation Developer','I’m a beginner AI automation developer. Looking to hire? Contact me.'),
            ('Looking for Remote Work','I am happy to start with a paid task.'),
            ('N8n Builder','Continuing the discussion from Looking for an n8n Freelancer. Hi, I saw your post looking for a partner. My rate is $20.'),
        ]:
            op=opportunity(title=title,source_text=text,raw_evidence_quote=text)
            self.assertEqual(op.buyer_role,'SELLER')
            self.assertEqual(op.commercial_intent_type,'NONE')
        op=opportunity(title='Hiring workflow developer',source_text='I am looking for an n8n developer.',raw_evidence_quote='I am looking for an n8n developer.')
        self.assertEqual(op.buyer_role,'BUYER')

    def test_generated_digest_is_not_a_buyer_quote(self):
        op=opportunity(source_platform='GitHub',title='Weekly Digest',source_text='Please send pricing for RFQ.',raw_evidence_quote='Please send pricing for RFQ.')
        self.assertEqual(op.commercial_intent_type,'NONE')

    def test_github_issue_default_observer_but_primary_hiring_can_be_buyer(self):
        with tempfile.TemporaryDirectory() as tmp:
            def op(body):
                return make_op('GitHub','n8n-io/n8n','https://github.com/a/b/issues/1','https://api.github.com/a',
                               'Bug description: workflow failed',body,'author','https://github.com/author',
                               '2026-10-12T00:00:00Z',NOW.isoformat(),[],0,True,True,{'body':body},tmp)
            bug=op('To reproduce: workflow fails on retry. Please fix.')
            self.assertEqual(bug.buyer_role,'PROBLEM_OBSERVER')
            self.assertEqual(bug.commercial_intent_type,'NONE')
            self.assertEqual(classify(bug,result(bug)),'REJECTED')
            paid=op('I am looking to hire someone to fix this workflow. Budget $200.')
            self.assertEqual(paid.buyer_role,'BUYER')
            self.assertEqual(paid.commercial_intent_type,'BUDGET_STATED')

    def test_discourse_listing_activity_does_not_replace_publication(self):
        row={'id':1,'slug':'need-help','title':'Hiring workflow developer','created_at':'2026-10-01T00:00:00Z'}
        first={'id':10,'post_number':1,'username':'buyer','created_at':row['created_at'],'cooked':'Looking to hire a workflow developer. Budget $200.'}
        reply={'id':11,'post_number':2,'username':'vendor','created_at':'2026-10-12T00:00:00Z','cooked':'I can help. DM me.'}
        topic={'title':row['title'],'posts_count':2,'post_stream':{'posts':[first,reply],'stream':[10,11]}}
        def fetch(url):return {'topic_list':{'topics':[row]}} if '/c/' in url else topic
        with tempfile.TemporaryDirectory() as tmp:
            ops,audit=discourse_jobs({'base_url':'https://community.n8n.io','category_id':13,'pages':1},NOW,tmp,fetch)
            self.assertEqual(audit['verified_buyer_requests'],1)
            self.assertEqual(ops[0].published_at,row['created_at'])
            self.assertIsNone(ops[0].buyer_activity_at)
            self.assertNotEqual(classify(ops[0],result(ops[0])),'DO NOW')

    def test_access_failure_is_not_zero_record_success(self):
        def blocked(url):raise PermissionError('public access denied')
        with tempfile.TemporaryDirectory() as tmp:
            ops,audit=inspect_public_path({'family':'bounty','url':'https://example.com'},NOW,tmp,blocked)
            self.assertEqual(ops,[])
            self.assertEqual(audit['verified_buyer_requests'],0)
            self.assertTrue(audit['errors'])

    def test_bracketed_primary_budget_and_offer_fit_are_idempotent(self):
        from demand_opportunity_engine.buyer_discovery import fit_job
        text='Looking to hire an n8n specialist. Budget: ₹[10,000] (~US$[115]).'
        op=opportunity(source_text=text,raw_evidence_quote=text)
        self.assertEqual(op.commercial_intent_type,'BUDGET_STATED')
        self.assertEqual(result(op)['components']['expected_ticket'],1)
        text='Hiring a marketing specialist for a consumer apparel brand.'
        op=opportunity(source_text=text,raw_evidence_quote=text)
        fit_job(op);first=op.to_dict();fit_job(op)
        self.assertEqual(op.to_dict(),first)
        self.assertEqual(op.fulfillment_mode,'PARTNER_REQUIRED')

    def test_job_applications_count_as_competition_without_dm_me_phrase(self):
        from demand_opportunity_engine.signals import competition
        replies=[{'author':str(i),'text':'Here is my portfolio and experience. Application sent by email.','url':f'https://example.com/{i}'} for i in range(6)]
        self.assertEqual(competition(replies,True,'Hiring',applications=True)[1],'HIGH')

if __name__=='__main__':unittest.main()
