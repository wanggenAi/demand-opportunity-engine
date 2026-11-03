"""Bounded public HTTP adapters, immutable snapshots, conservative normalization.

No LLM, credentials, outbound contacts, or dependency outside the stdlib.
"""
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


def stamp(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return (parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc))
    except ValueError:
        for fmt in ('%d-%b-%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        try:
            return parsedate_to_datetime(value).astimezone(timezone.utc)
        except (TypeError, ValueError):
            return None


def clean(value):
    value = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', value or '', flags=re.S | re.I)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value))).strip()


def clean_main(text):
    main = re.search(r'<main\b[^>]*>(.*?)</main>', text, re.S | re.I)
    return clean(main[1] if main else text)


def award_date(text):
    match = re.search(r'Date Notification of Award Issued.*?(\d{4})/(\d{2})/(\d{2})', clean(text), re.I)
    return '-'.join(match.groups()) if match else None


def signed_value(text):
    match = re.search(r'Signed Contract [Pp]rice\s+([A-Z]{3})\s+([\d,.]+)', clean(text))
    return match[0] if match else None  # contract disclosure, never revenue/receipt


def canonical(url):
    p = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(p.query)
             if not k.lower().startswith('utm_') and k not in ('fbclid', 'gclid')]
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/'),
                                   urllib.parse.urlencode(sorted(query)), ''))


def key(value):
    return hashlib.sha256(value.encode()).hexdigest()[:24]


def fetch(url):
    request = urllib.request.Request(url, headers={
        'User-Agent': 'demand-opportunity-engine-world-shift/1.0 (public research; no commercial outreach)',
        'Accept': 'application/json, application/rss+xml, text/html, */*'})
    # One retry only for transient transport/server errors; never retry access denial.
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read(3_000_001)
                if len(raw) > 3_000_000:
                    raise ValueError('Response exceeds 3 MB bound')
                return raw, {'status': response.status, 'final_url': response.url,
                             'server_date': response.headers.get('Date')}
        except urllib.error.HTTPError as exc:
            if exc.code not in (500, 502, 503, 504) or attempt:
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt:
                raise
        time.sleep(1)


def parse(source, raw):
    """Yield source claims, never infer payment from words or engagement."""
    kind = source['adapter']
    text = raw.decode('utf-8-sig').strip()
    data = json.loads(text) if kind in ('worldbank', 'huggingface', 'github', 'hn', 'reddit') else None
    if kind == 'worldbank':
        for x in data['procnotices']:
            yield {'url': 'https://projects.worldbank.org/en/projects-operations/procurement-detail/' + x['id'],
                   'title': x.get('bid_description', ''), 'published_at': x.get('noticedate'),
                   'event_at': award_date(x.get('notice_text', '')), 'event_type': x.get('notice_type', 'procurement_notice'),
                   'country': x.get('project_ctry_name') or x.get('contact_ctry_name'), 'text': clean(x.get('notice_text')),
                   'procurement': {'buyer': x.get('contact_organization'), 'project': x.get('project_name'), 'buyer_identity_status': 'disclosed authority' if x.get('contact_organization') else 'UNKNOWN; review notice',
                                   'reference': x.get('bid_reference_no'), 'content': x.get('bid_description'),
                                   'deadline': x.get('submission_deadline_date'), 'deadline_local_time': x.get('submission_deadline_time'), 'budget': None, 'signed_contract_value_source_text': signed_value(x.get('notice_text', '')),
                                   'status': x.get('notice_type'), 'project_id': x.get('project_id')},
                   'underlying_event_key': 'wb:' + x['id'], 'related_procurement_key': x.get('bid_reference_no'), 'cluster_key': 'wb:' + x.get('project_id', '') + ':' + (x.get('bid_reference_no') or x['id'])}
    elif kind == 'rss':
        root = ET.fromstring(text)
        items = root.findall('.//item')
        if not items:
            raise ValueError('No RSS items; not a usable feed')
        for x in items[:20]:
            yield {'url': x.findtext('link'), 'title': clean(x.findtext('title')),
                   'published_at': x.findtext('pubDate'), 'event_type': 'official_release',
                   'text': clean(x.findtext('description'))}
    elif kind == 'huggingface':
        for x in data:
            yield {'url': 'https://huggingface.co/' + x['id'], 'title': x['id'],
                   'published_at': x.get('createdAt'), 'event_at': x.get('lastModified'),
                   'event_type': 'model_metadata_update', 'text': 'Public metadata: ' + json.dumps({k: x.get(k) for k in ('id', 'createdAt', 'lastModified', 'downloads', 'likes', 'pipeline_tag')}, ensure_ascii=False),
                   'metrics': {'downloads': x.get('downloads'), 'likes': x.get('likes')},
                   'metric_scope': 'Hugging Face platform reported downloads; not unique users, payment, or global adoption'}
    elif kind == 'github':
        for x in data:
            yield {'url': x['html_url'], 'title': x.get('name') or x['tag_name'],
                   'published_at': x.get('published_at'), 'event_type': 'software_release',
                   'text': clean(x.get('body'))}
    elif kind == 'hn':
        for x in data['hits']:
            yield {'url': 'https://news.ycombinator.com/item?id=' + x['objectID'],
                   'title': x.get('title') or '', 'published_at': x.get('created_at'),
                   'event_type': 'public_discussion', 'text': clean(x.get('story_text')) or x.get('title') or '',
                   'original_url': x.get('url'), 'metric_scope': 'HN selected query sample; discussion is not buying intent'}
    elif kind == 'reddit':
        for child in data['data']['children']:
            x = child['data']
            yield {'url': 'https://www.reddit.com' + x['permalink'], 'title': x['title'],
                   'published_at': datetime.fromtimestamp(x['created_utc'], timezone.utc).isoformat(),
                   'event_type': 'public_discussion', 'text': x.get('selftext') or x['title']}
    elif kind == 'ndrc':
        matches = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, re.S)
        for url, title in matches:
            title = clean(title)
            date = re.search(r'/\d{6}/t(\d{8})_', url)
            if date and title:
                yield {'url': urllib.parse.urljoin(source['url'], url), 'title': title,
                       'published_at': datetime.strptime(date[1], '%Y%m%d').replace(tzinfo=timezone.utc).isoformat(),
                       'event_type': 'policy_index_entry', 'text': title,
                       'policy_stage': 'UNKNOWN — index only; full document and effective date require review'}
    elif kind == 'page':
        title = re.search(r'<title[^>]*>(.*?)</title>', text, re.S)
        if len(clean_main(text)) < 200:
            raise ValueError('HTML shell/no substantive article; HTTP 200 is not collection success')
        # Undated current pages are baseline, never dated as today's event.
        yield {'url': source['url'], 'title': clean(title[1]) if title else source['name'],
               'published_at': source.get('published_at'), 'event_at': source.get('event_at'),
               'event_type': source.get('event_type', 'current_page_baseline'),
               'text': clean_main(text), 'date_provenance': source.get('date_provenance', 'not disclosed; collection is not publication')}
    else:
        raise ValueError('Unsupported adapter: ' + kind)


def sector(title):
    t = title.lower()
    if re.search(r'energy|electric|solar|battery|power|grid|storage|transformer', t):
        return 'energy_equipment'
    if re.search(r'\bai\b|qwen|deepseek|gpu|inference|sglang', t):
        return 'ai_compute'
    if re.search(r'digital|data cent|ict|network|software|automat', t):
        return 'digital_automation'
    return 'other_structural'


def normalize(item, source, observed, snapshot):
    if not item.get('url') or not item.get('title'):
        raise ValueError('Missing source URL/title')
    pub, event = stamp(item.get('published_at')), stamp(item.get('event_at'))
    text = item.pop('text', '')
    item = dict(item)
    item.update(id=key(item.get('underlying_event_key') or canonical(item['url'])),
                url=canonical(item['url']), source_id=source['id'], source_name=source['name'],
                category=source['category'], country=item.get('country') or source.get('country', 'UNKNOWN'),
                industry=sector(item['title']), published_at_source=item.get('published_at'), event_at_source=item.get('event_at'),
                date_precision='Source date-only values use UTC midnight for sorting only; actual timezone/time not established',
                published_at=pub.isoformat() if pub else None,
                event_at=event.isoformat() if event else None, first_collected_at=observed,
                last_verified_at=observed, snapshot=snapshot, evidence_excerpt=text[:1200],
                evidence_summary='Source claim only; see original snapshot for full context.',
                economic_constraint='UNKNOWN — requires analyst review', affected_value_chain='UNKNOWN',
                payment_evidence={'status': 'PROCUREMENT_NOTICE' if item.get('procurement') else 'NOT_ESTABLISHED',
                                  'revenue': None, 'paid_users': None, 'cross_border_buyer': None},
                credibility='Official source claim; outcome not independently established' if source['category'] != 'demand' else 'Public user statement; identity and payment unverified',
                unknowns=['Actual buyer budget, implementation and outcome require verification'],
                historical_change='FIRST_OBSERVATION; no growth established', trend='BASELINE')
    return item


def merge_events(previous, incoming):
    result = {x['id']: dict(x) for x in previous}
    for event in incoming:
        old = result.get(event['id'])
        if old:
            event['first_collected_at'] = old['first_collected_at']
            # Same-run repeats cannot create trend evidence.
            if old.get('metrics') and event.get('metrics') and old['last_verified_at'] != event['last_verified_at']:
                event['historical_change'] = {'previous_verified_at': old['last_verified_at'],
                                              'previous': old['metrics'], 'current': event['metrics'],
                                              'scope': event.get('metric_scope')}
                event['trend'] = 'TWO_OBSERVATIONS_NOT_SUSTAINED_GROWTH'
            elif old.get('snapshot') != event['snapshot']:
                event['historical_change'] = 'Source content changed; economic significance unverified'
            else:
                event['historical_change'] = old.get('historical_change')
                event['trend'] = old.get('trend', 'BASELINE')
            event['source_ids'] = sorted(set(old.get('source_ids', [old['source_id']]) + [event['source_id']]))
        result[event['id']] = event
    return list(result.values())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def collect(config, directory, now, transport=fetch):
    directory = Path(directory)
    prior_path = directory / 'latest_run.json'
    prior_health = {s['source_id']: s for s in json.loads(prior_path.read_text())['sources']} if prior_path.exists() else {}
    observed = now.isoformat()
    sources = json.loads(Path(config).read_text())
    incoming, health = [], []
    for source in sources:
        h = dict(source_id=source['id'], name=source['name'], url=source['url'], category=source['category'],
                 attempted_at=observed, last_successful_collection_at=prior_health.get(source['id'], {}).get('last_successful_collection_at'), status='FAILED', fetched=0,
                 retained=0, outside_window=0, future_dated=0, missing_fields={}, failure=None)
        try:
            raw, meta = transport(source['url'])
            digest = hashlib.sha256(raw).hexdigest()
            snap = directory / 'snapshots' / (digest + '.txt')
            if not snap.exists():
                snap.parent.mkdir(parents=True, exist_ok=True)
                snap.write_bytes(raw)
            h.update(snapshot=str(snap), sha256=digest, http_status=meta.get('status'),
                     final_url=meta.get('final_url'), server_date=meta.get('server_date'))
            items = list(parse(source, raw))
            if not items:
                raise ValueError('Parsed zero records; adapter/schema or empty feed requires review')
            h['fetched'] = len(items)
            source_events = []
            for item in items:
                event = normalize(dict(item), source, observed, str(snap))
                date = stamp(event.get('event_at') or event.get('published_at'))
                if date and date > now:
                    h['future_dated'] += 1
                    continue
                if date and date < now - timedelta(days=90):
                    h['outside_window'] += 1
                    continue
                event['freshness'] = ('UNDATED_BASELINE' if not date else
                                      'RECENT_30D' if date >= now - timedelta(days=30) else 'BACKGROUND_90D')
                for field in ('published_at', 'event_at', 'country'):
                    if not event.get(field) or event[field] == 'UNKNOWN':
                        h['missing_fields'][field] = h['missing_fields'].get(field, 0) + 1
                if event.get('procurement'):
                    for field in ('deadline', 'budget'):
                        if event['procurement'].get(field) is None:
                            h['missing_fields'][field] = h['missing_fields'].get(field, 0) + 1
                source_events.append(event)
                h['retained'] += 1
            incoming.extend(source_events)
            h.update(status='OK', last_successful_collection_at=observed)
        except Exception as exc:
            h['status'] = 'FAILED'
            h['failure'] = f'{type(exc).__name__}: {exc}'
        health.append(h)
        time.sleep(0.3)
    path = directory / 'events.json'
    previous = json.loads(path.read_text()) if path.exists() else []
    merged = merge_events(previous, incoming)
    run = dict(collected_at=observed, window_days=30, background_days=90, sources=health,
               raw_records=sum(x['fetched'] for x in health), retained_before_dedup=len(incoming),
               unique_notice_records=len({x['id'] for x in incoming}),
               unique_this_run=len({x.get('cluster_key') or x['id'] for x in incoming}), historical_events=len(merged),
               baseline_only=not bool(previous), coverage='Bounded nonrepresentative source sample; not a global census')
    write_json(path, merged)
    # A run is immutable. --as-of denotes real collection time, never manufacture history.
    run_path = directory / 'runs' / (now.strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    if run_path.exists():
        raise ValueError('Run timestamp already exists; choose actual current time')
    write_json(run_path, run)
    write_json(directory / 'latest_run.json', run)
    return merged, run
