import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from demand_opportunity_engine.world_shift.engine import canonical, collect, merge_events, normalize, parse, stamp
from demand_opportunity_engine.world_shift.reports import generate

NOW = datetime(2026, 11, 3, 9, tzinfo=timezone.utc)
SOURCE = {'id': 'test', 'name': 'Test', 'adapter': 'hn', 'category': 'demand', 'url': 'https://example.org/api'}


class WorldShiftTests(unittest.TestCase):
    def test_date_only_never_uses_host_timezone(self):
        self.assertEqual(stamp('2026-10-23').isoformat(), '2026-10-23T00:00:00+00:00')

    def test_shell_is_failure(self):
        with self.assertRaises(ValueError):
            list(parse(dict(SOURCE, adapter='page'), b'<html><title>Blog</title><main>Navigation</main></html>'))

    def test_canonical_preserves_notice_ids(self):
        self.assertEqual(canonical('https://EXAMPLE.org/a/?utm_source=x&id=3#foo'), 'https://example.org/a?id=3')
        self.assertNotEqual(canonical('https://example.org/?id=3'), canonical('https://example.org/?id=4'))

    def test_baseline_no_payment_or_growth(self):
        e = normalize({'url': 'https://example.org', 'title': 'AI usage grew with funding', 'text': 'paid users?'}, SOURCE, NOW.isoformat(), 'hash.txt')
        self.assertIsNone(e['published_at'])
        self.assertEqual(e['trend'], 'BASELINE')
        self.assertEqual(e['payment_evidence']['status'], 'NOT_ESTABLISHED')

    def test_upsert_and_same_run_do_not_invent_trends(self):
        e = normalize({'url': 'https://example.org', 'title': 'test', 'metrics': {'downloads': 10}}, SOURCE, NOW.isoformat(), 'a')
        result = merge_events([e], [dict(e), dict(e)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['trend'], 'BASELINE')
        changed = dict(e, last_verified_at='2026-11-04T09:00:00+00:00', metrics={'downloads': 8})
        result = merge_events([e], [changed])[0]
        self.assertEqual(result['first_collected_at'], e['first_collected_at'])
        self.assertEqual(result['trend'], 'TWO_OBSERVATIONS_NOT_SUSTAINED_GROWTH')
        self.assertEqual(result['historical_change']['current']['downloads'], 8)

    def test_procurement_not_invented_budget_deadline(self):
        source = dict(SOURCE, adapter='worldbank', category='procurement')
        raw = json.dumps({'procnotices': [{'id': 'OP1', 'notice_type': 'Contract Award', 'noticedate': '01-Nov-2026', 'submission_date': '2026-11-01T00:00:00Z', 'bid_description': 'solar', 'notice_text': '<p>Signed on August 1</p>'}]}).encode()
        item = list(parse(source, raw))[0]
        self.assertIsNone(item['procurement']['deadline'])
        self.assertIsNone(item['procurement']['budget'])
        self.assertIsNone(item['event_at'])

    def test_end_to_end_dates_failure_dedup_history_and_reports(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg = root / 'sources.json'
            cfg.write_text(json.dumps([SOURCE, dict(SOURCE, id='bad', url='https://example.org/bad')]))
            items = [{'objectID': str(i), 'title': 'Demand', 'story_text': 'need help', 'created_at': date}
                     for i, date in enumerate(['2026-11-01T00:00:00Z', '2024-01-01T00:00:00Z', '2027-01-01T00:00:00Z'])]
            def transport(url):
                if url.endswith('bad'):
                    raise PermissionError('403 no bypass')
                return json.dumps({'hits': items + [items[0]]}).encode(), {'status': 200}
            events, run = collect(cfg, root, NOW, transport)
            self.assertEqual(run['raw_records'], 4)
            self.assertEqual(run['unique_this_run'], 1)
            self.assertEqual(run['sources'][0]['outside_window'], 1)
            self.assertEqual(run['sources'][0]['future_dated'], 1)
            self.assertEqual(run['sources'][1]['status'], 'FAILED')
            generate(events, run, root / 'reports')
            self.assertEqual(len(list((root / 'reports').glob('*.md'))), 4)
            self.assertIn('403 no bypass', (root / 'reports/SOURCE_HEALTH.md').read_text())
            self.assertTrue(Path(events[0]['snapshot']).exists())
            before = events[0]['first_collected_at']
            later = datetime(2026, 11, 4, 9, tzinfo=timezone.utc)
            events2, _ = collect(cfg, root, later, transport)
            self.assertEqual(len(events2), 1)
            self.assertEqual(events2[0]['first_collected_at'], before)
            self.assertEqual(len(list((root / 'runs').glob('*.json'))), 2)

    def test_http_success_shell_failure_and_retained_history(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg = root / 'sources.json'
            source = dict(SOURCE, adapter='page')
            cfg.write_text(json.dumps([source]))
            body = b'<html><title>Official</title><main>' + b'valid evidence ' * 30 + b'</main></html>'
            events, run = collect(cfg, root, NOW, lambda url: (body, {'status': 200}))
            self.assertEqual(run['sources'][0]['status'], 'OK')
            later = datetime(2026, 11, 4, 9, tzinfo=timezone.utc)
            events2, run2 = collect(cfg, root, later, lambda url: (b'<main>Navigation</main>', {'status': 200}))
            self.assertEqual(run2['sources'][0]['status'], 'FAILED')
            self.assertEqual(run2['sources'][0]['http_status'], 200)
            self.assertEqual(run2['sources'][0]['last_successful_collection_at'], NOW.isoformat())
            self.assertEqual(events2[0]['last_verified_at'], events[0]['last_verified_at'])
            self.assertEqual(run2['unique_this_run'], 0)

    def test_invalid_review_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            run = dict(collected_at=NOW.isoformat(), raw_records=0, retained_before_dedup=0, unique_this_run=0, historical_events=0, sources=[])
            with self.assertRaises(ValueError):
                generate([], run, d, {'reviewed_at': NOW.isoformat(), 'signals': [{'title': 'fake', 'analysis': 'fake', 'evidence_ids': ['absent']}]})


if __name__ == '__main__':
    unittest.main()
