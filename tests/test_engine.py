import json
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path

from demand_opportunity_engine.models import Opportunity, Outcome
from demand_opportunity_engine.signals import payment_truth, competition, cluster_for, normalize_intent
from demand_opportunity_engine.scoring import score_opportunity, edge_rejections
from demand_opportunity_engine.board import classify, selections, build_board, rank
from demand_opportunity_engine.clusters import clusters
from demand_opportunity_engine.discovery import github_adapter, hn_adapter, relevant_buyer_activity
from demand_opportunity_engine.feedback import metrics
from demand_opportunity_engine.store import upsert, append_outcome, load_outcomes

NOW = datetime(2026, 10, 13, 4, tzinfo=timezone.utc)

def opportunity(id="buyer", **changes):
    text = "I need supplier verification before an order. Budget $250. Looking for someone to help."
    op = Opportunity(
        id=id, title="Supplier verification request", source_platform="Test",
        source_url=f"https://example.com/post/{id}", community="sourcing",
        published_at="2026-10-12T03:00:00Z", observed_at=NOW.isoformat(),
        raw_evidence_quote=text, source_text=text, buyer_id=f"Test:{id}",
        target_profile_url=f"https://example.com/users/{id}", source_verified=True,
        buyer_role="BUYER", competition_pressure="LOW", comments_complete=True,
        seller_competition_count=0, comment_count=0, cluster_name="supplier_verification",
        suggested_offer="One supplier desk memo", suggested_price_range="USD 100–250 proposal",
        first_message="Which supplier and deadline?", differentiation="One bounded remote memo",
        effort="2 hours", next_action="Confirm scope and budget", contact_channel="email")
    changes.setdefault("contact_path", op.source_url)
    return normalize_intent(replace(op, **changes))

def result(op, events=(), population=()):
    return score_opportunity(op, NOW, events, population or [op])

def event(oid, kind, day=8, amount=None, currency=None, channel="email"):
    return Outcome(f"{oid}-{kind}", oid, kind, f"2026-10-{day:02d}T00:00:00Z",
                   channel, amount, currency, "not a fit" if kind == "LOST" else "")

class GateTests(unittest.TestCase):
    def test_fresh_primary_demand_can_pass(self):
        op = opportunity()
        self.assertEqual(classify(op, result(op)), "DO NOW")

    def test_stale_high_keywords_cannot_bypass_gate_or_caps(self):
        op = opportunity(published_at="2026-01-01", derived_interpretation="explicit paid fee budget " * 100)
        self.assertNotEqual(classify(op, result(op)), "DO NOW")
        board = build_board([op], NOW.isoformat())
        self.assertIn("## DO NOW\n\nNone.", board)

    def test_7_to_14_days_is_validate(self):
        op = opportunity(published_at="2026-10-03")
        self.assertEqual(classify(op, result(op)), "VALIDATE")

    def test_verified_buyer_activity_revives_old_lead(self):
        op = opportunity(published_at="2026-01-01", buyer_activity_at="2026-10-12",
                         buyer_activity_url="https://example.com/comments/1",
                         buyer_activity_quote="Still looking for someone, budget $250",
                         buyer_activity_verified=True, buyer_activity_author_id="Test:buyer")
        self.assertEqual(classify(op, result(op)), "DO NOW")

    def test_seller_or_unverified_activity_does_not_revive(self):
        op = opportunity(published_at="2026-01-01", buyer_activity_at="2026-10-12",
                         buyer_activity_url="https://example.com/comments/1",
                         buyer_activity_quote="I can help", buyer_activity_verified=True,
                         buyer_activity_author_id="Test:seller")
        self.assertNotEqual(classify(op, result(op)), "DO NOW")
        self.assertIsNone(relevant_buyer_activity(
            [{"author": "seller", "text": "Still looking for help", "at": "2026-10-12", "url": "x"}], "buyer"))

    def test_generic_op_thanks_does_not_revive(self):
        self.assertIsNone(relevant_buyer_activity(
            [{"author": "buyer", "text": "Thanks!", "at": "2026-10-12", "url": "x"}], "buyer"))

    def test_inference_cannot_inflate_payment_or_score(self):
        text = "I need help comparing suppliers."
        op = opportunity(source_text=text, raw_evidence_quote=text)
        inflated = replace(op, derived_interpretation="explicit paid fee budget $999 " * 100,
                           payment_signal_type="EXPLICIT_BUDGET", suggested_price_range="$10000")
        self.assertEqual(result(op)["score"], result(inflated)["score"])
        self.assertEqual(payment_truth(inflated)[0], "INFERRED")

    def test_source_quote_cannot_be_invented(self):
        with self.assertRaises(ValueError):
            opportunity(raw_evidence_quote="explicit payment").validate()

    def test_no_budget_and_seller_are_not_paid_leads(self):
        for text in ("I need automation but no budget, not willing to pay.", "Looking for free help. Budget $100 later."):
            op = opportunity(source_text=text, raw_evidence_quote=text)
            self.assertEqual(payment_truth(op)[2], 0)
        op = opportunity(title="[For Hire] Paid automation expert", buyer_role="BUYER")
        self.assertEqual(payment_truth(op)[2], 0)

    def test_competition_reduces_rank_and_blocks_now(self):
        low, high = opportunity(), opportunity("crowded", competition_pressure="HIGH")
        self.assertGreater(result(low)["score"], result(high)["score"])
        self.assertNotEqual(classify(high, result(high)), "DO NOW")
        comments = [{"author": f"seller{i}", "text": "I can help. DM me.", "url": str(i)} for i in range(8)]
        self.assertEqual(competition(comments, True, "")[1], "HIGH")

    def test_partial_reply_collection_is_unknown(self):
        self.assertEqual(competition([], False, "")[1], "UNKNOWN")
        op = opportunity(competition_pressure="UNKNOWN")
        self.assertNotEqual(classify(op, result(op)), "DO NOW")

    def test_unowned_capability_blocks_immediate_action(self):
        remote = opportunity()
        for mode in ("PARTNER_REQUIRED", "SPECIALIST_REQUIRED", "LOCAL_PHYSICAL"):
            op = replace(remote, fulfillment_mode=mode)
            self.assertLess(result(op)["score"], result(remote)["score"])
            self.assertNotEqual(classify(op, result(op)), "DO NOW")

    def test_future_or_closed_source_cannot_pass(self):
        for op in (opportunity(published_at="2026-11-01"), opportunity(source_open=False)):
            self.assertNotEqual(classify(op, result(op)), "DO NOW")

    def test_attention_caps_all_sections_and_empty_do_now(self):
        ops = [opportunity(str(i)) for i in range(20)]
        buckets, _ = selections(ops, NOW)
        self.assertEqual(len(buckets["DO NOW"]), 3)
        self.assertLessEqual(sum(map(len, buckets.values())), 11)
        stale = [replace(o, published_at="2025-01-01") for o in ops]
        self.assertEqual(len(selections(stale, NOW)[0]["DO NOW"]), 0)

class ProductEdgeTests(unittest.TestCase):
    def test_seeking_work_is_supply_not_buyer_demand(self):
        from demand_opportunity_engine.signals import SELLER
        for title in ("SEEKING FREELANCE / CONTRACT WORK", "SEEKING FREELANCE | Remote"):
            self.assertTrue(SELLER.search(title))
            text = title + " I build workflow automation. Budget $250."
            op = opportunity(title=title, source_text=text, raw_evidence_quote=text)
            self.assertEqual(payment_truth(op)[2], 0)
        self.assertFalse(SELLER.search("SEEKING FREELANCER: build our workflow"))

    def test_source_code_does_not_mean_supplier_sourcing(self):
        self.assertEqual(cluster_for("Workflow sourceCode file failed to save"), "workflow_reliability")

    def test_repeated_record_or_author_not_independent(self):
        one = opportunity()
        self.assertEqual(clusters([one] * 10)[0]["independent_demand_count"], 1)
        self.assertEqual(clusters([one] * 10)[0]["status"], "UNVALIDATED CLUSTER")
        copies = [replace(one, id=str(i), source_url=f"https://example.com/{i}") for i in range(8)]
        self.assertEqual(clusters(copies)[0]["independent_demand_count"], 1)

    def test_product_requires_five_two_sources_and_payment(self):
        ops = []
        for i in range(5):
            text = f"I need supplier verification for order {i}. Budget $250."
            ops.append(opportunity(str(i), source_text=text, raw_evidence_quote=text,
                                   community="sourcing" if i < 3 else "importing"))
        c = clusters(ops)[0]
        self.assertEqual(c["status"], "PRODUCT OPPORTUNITY")
        self.assertEqual(c["payment_evidence_count"], 5)
        unpaid = [replace(o, source_text="I need supplier verification for order " + o.id,
                          raw_evidence_quote="I need supplier verification for order " + o.id) for o in ops]
        self.assertEqual(clusters(unpaid)[0]["status"], "UNVALIDATED CLUSTER")

    def edge(self, **changes):
        e = {"novelty":"new price", "information_gap":"verified buyer awareness gap",
             "gap_verified":True, "monetization_path":"audit", "target_buyer":"operator",
             "decay_window":"14 days", "legality_check":"public and authorized",
             "verification_sources":[
                 {"url":"https://vendor.com/news","quote":"new","verified":True,"independent":True},
                 {"url":"https://benchmark.org/model","quote":"price","verified":True,"independent":True}]}
        return opportunity(routes=["INFO_EDGE"], info_edge=e, **changes)

    def test_info_edge_must_be_fresh_and_corroborated(self):
        self.assertFalse(edge_rejections(self.edge(), NOW))
        self.assertTrue(edge_rejections(self.edge(published_at="2025-01-01"), NOW))
        stale = self.edge(published_at="2025-01-01")
        self.assertEqual(classify(stale, result(stale)), "REJECTED")
        one = self.edge()
        one.info_edge["verification_sources"] = one.info_edge["verification_sources"][:1]
        self.assertTrue(edge_rejections(one, NOW))
        unknown = self.edge()
        unknown.info_edge["gap_verified"] = False
        self.assertTrue(edge_rejections(unknown, NOW))

class FeedbackTests(unittest.TestCase):
    def test_cli_accepts_outcomes_for_information_edge_store(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            upsert(root / "live.json", [opportunity()])
            upsert(root / "edges.json", [opportunity("edge", routes=["INFO_EDGE"])])
            (root / "event.json").write_text(json.dumps(event("edge", "CONTACTED").to_dict()))
            done = subprocess.run([
                sys.executable, "-m", "demand_opportunity_engine.cli", "outcome",
                "--data", str(root / "live.json"), "--edges", str(root / "edges.json"),
                "--outcomes", str(root / "outcomes.jsonl"), "--event", str(root / "event.json"),
            ], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(load_outcomes(root / "outcomes.jsonl")[0].opportunity_id, "edge")

    def test_neutral_without_human_data_and_discovery_events(self):
        op = opportunity()
        self.assertEqual(result(op)["components"]["outcome_feedback"], 0)
        self.assertEqual(result(op, [event("buyer", "DISCOVERED")])["components"]["outcome_feedback"], 0)

    def test_success_and_loss_change_similar_future_rank(self):
        prior = [opportunity("prior1"), opportunity("prior2")]
        future = opportunity("future")
        ops = prior + [future]
        success = [event(o.id, k, 9 if k == "WON" else 8, 200 if k in {"QUOTED","REVENUE"} else None,
                         "USD" if k in {"QUOTED","REVENUE"} else None)
                   for o in prior for k in ("CONTACTED", "REPLIED", "QUALIFIED", "QUOTED", "WON", "REVENUE")]
        failures = [event(o.id,k) for o in prior for k in ("CONTACTED","LOST")]
        positive = result(future, success, ops)["components"]["outcome_feedback"]
        negative = result(future, failures, ops)["components"]["outcome_feedback"]
        self.assertGreater(positive, 0)
        self.assertLess(negative, 0)
        self.assertGreater(result(future, success, ops)["score"], result(future, failures, ops)["score"])
        self.assertEqual(metrics(success)["average_ticket_by_currency"], {"USD": 200})
        self.assertEqual(metrics(success)["average_cycle_days"], 1)

    def test_money_does_not_mix_currencies_or_quote_as_revenue(self):
        es = [event("a","CONTACTED"),event("a","QUOTED",amount=100,currency="USD"),
              event("a","WON",day=9),event("a","REVENUE",amount=50,currency="EUR")]
        self.assertEqual(metrics(es)["average_ticket_by_currency"], {"EUR":50})

    def test_feedback_cannot_revive_stale_and_contacted_suppressed(self):
        op = opportunity(published_at="2025-01-01")
        self.assertNotEqual(classify(op, result(op,[event("buyer","CONTACTED")])), "DO NOW")
        fresh = opportunity()
        self.assertNotEqual(classify(fresh,result(fresh,[event("buyer","CONTACTED")])), "DO NOW")

    def test_append_only_idempotent_and_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"outcomes.jsonl"
            e = event("buyer","CONTACTED")
            self.assertTrue(append_outcome(p,e,[opportunity()]))
            self.assertFalse(append_outcome(p,e,[opportunity()]))
            self.assertEqual(len(load_outcomes(p)),1)
            with self.assertRaises(ValueError):
                append_outcome(p,event("unknown","CONTACTED"),[opportunity()])

class DiscoveryTests(unittest.TestCase):
    def test_live_ingestion_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"store.json"
            op = opportunity()
            upsert(p,[op,op])
            result = upsert(p,[replace(op, observed_at="2026-10-13T05:00:00Z")])
            self.assertEqual(len(result),1)
            self.assertEqual(result[0].id,op.id)
            self.assertEqual(result[0].observed_at,"2026-10-13T05:00:00Z")

    def test_github_updated_at_or_seller_reply_not_buyer_activity(self):
        item = {"title":"Need workflow help", "body":"I need help. Budget $250.",
                "url":"https://api.github.com/repos/acme/workflow/issues/1",
                "html_url":"https://github.com/acme/workflow/issues/1", "created_at":"2026-10-01T00:00:00Z",
                "updated_at":"2026-10-12T00:00:00Z", "state":"open", "comments":1,
                "comments_url":"https://api.github.com/comments","user":{"login":"buyer","html_url":"https://github.com/buyer"}}
        seller = {"user":{"login":"seller"},"body":"I can help! DM me.",
                  "created_at":"2026-10-12T00:00:00Z","html_url":"https://github.com/acme/workflow/issues/1#comment-1"}
        def fake(url):
            return [seller] if url.startswith(item["comments_url"]) else {"items":[item]}
        with tempfile.TemporaryDirectory() as tmp:
            ops,errors=github_adapter({"lookback_days":30,"per_query":3,"github_queries":["workflow"]},NOW,tmp,fake)
            self.assertFalse(errors)
            self.assertEqual(ops[0].seller_competition_count,1)
            self.assertIsNone(ops[0].buyer_activity_at)
            self.assertEqual(ops[0].payment_signal_type,"EXPLICIT_BUDGET")

    def test_hn_adapter_refetches_primary_and_author(self):
        hit = {"objectID":"123","created_at":"2026-10-12T00:00:00Z","title":"Ask HN: Need automation help","author":"buyer"}
        item = {"id":123,"created_at":hit["created_at"],"author":"buyer","text":"I need workflow help. Budget $200.","children":[]}
        def fake(url):
            return item if "/items/" in url else {"hits":[hit]}
        with tempfile.TemporaryDirectory() as tmp:
            ops,errors=hn_adapter({"lookback_days":30,"per_query":3,"hn_queries":["automation"]},NOW,tmp,fake)
            self.assertFalse(errors)
            self.assertEqual(ops[0].target_profile_url,"https://news.ycombinator.com/user?id=buyer")
            self.assertEqual(ops[0].payment_signal_type,"EXPLICIT_BUDGET")
            self.assertTrue(Path(ops[0].source_snapshot.split("#")[0]).exists())

if __name__ == "__main__":
    unittest.main()
