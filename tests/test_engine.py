import json
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from demand_opportunity_engine.board import build_board, rank
from demand_opportunity_engine.models import Opportunity
from demand_opportunity_engine.scoring import freshness_score
from demand_opportunity_engine.store import load_opportunities


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 13, 1, 30, tzinfo=timezone.utc)
        self.opportunities = load_opportunities(Path(__file__).parents[1] / "data/opportunities.json")

    def test_real_dataset_has_twenty_and_all_routes(self):
        self.assertGreaterEqual(len(self.opportunities), 20)
        self.assertEqual({"DIRECT_LEAD", "PRODUCT_SIGNAL", "INFO_EDGE"},
                         {route for op in self.opportunities for route in op.routes})

    def test_scoring_order_prefers_explicit_reachable_demand(self):
        ranked = rank(self.opportunities, self.now)
        self.assertEqual("opp-013", ranked[0][0].id)
        self.assertIn("opp-001", [item[0].id for item in ranked[:3]])
        self.assertGreater(ranked[0][1]["score"], ranked[-1][1]["score"])

    def test_stale_evidence_decays(self):
        fresh = freshness_score("2026-10-13T01:30:00+00:00", 1, self.now)
        stale = freshness_score("2024-01-01T00:00:00+00:00", 5, self.now)
        self.assertGreater(fresh, stale)
        self.assertEqual(0, stale)

    def test_board_attention_caps(self):
        board = build_board(self.opportunities)
        self.assertLessEqual(board.count("### "), 11)
        self.assertLessEqual(board.split("## DO NOW", 1)[1].split("## VALIDATE", 1)[0].count("### "), 3)
        self.assertLessEqual(board.split("## VALIDATE", 1)[1].split("## WATCH", 1)[0].count("### "), 3)

    def test_evidence_free_candidate_is_rejected(self):
        raw = json.loads(json.dumps(self.opportunities[0].to_dict()))
        raw["evidence_text"] = ""
        with self.assertRaises(ValueError):
            Opportunity(**raw).validate()

    def test_quality_check_tracks_urls_and_freshness(self):
        from demand_opportunity_engine.quality import quality_report
        report = quality_report(self.opportunities, self.now)
        self.assertIn("Candidates: 20", report)
        self.assertIn("Fresh evidence published within 7 days: 0/20", report)


if __name__ == "__main__":
    unittest.main()
