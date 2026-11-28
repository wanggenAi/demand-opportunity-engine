import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from .engine import collect
from .reports import generate


def main():
    p = argparse.ArgumentParser(description='Independent free public world-shift research; no commercial-store writes')
    p.add_argument('command', choices=['collect', 'report'])
    p.add_argument('--data', default='data/world_shift')
    p.add_argument('--config', default='data/world_shift/sources.json')
    p.add_argument('--output', default='reports/world_shift')
    p.add_argument('--review', help='Optional dated analyst review JSON with stored evidence IDs')
    args = p.parse_args()
    if args.command == 'collect':
        events, run = collect(args.config, args.data, datetime.now(timezone.utc))
    else:
        events = json.loads((Path(args.data) / 'events.json').read_text())
        run = json.loads((Path(args.data) / 'latest_run.json').read_text())
    review = json.loads(Path(args.review).read_text()) if args.review else None
    generate(events, run, args.output, review)
    print(json.dumps({k: run[k] for k in ('collected_at', 'raw_records', 'retained_before_dedup', 'unique_this_run', 'historical_events')}))
    print(json.dumps({x['source_id']: x['status'] for x in run['sources']}))


if __name__ == '__main__':
    main()
