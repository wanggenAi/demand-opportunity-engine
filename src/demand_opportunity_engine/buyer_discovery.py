"""Bounded public buyer-source paths. Access failures are evidence, never empty successes."""
import json
import re
import urllib.request
from datetime import timedelta
from .discovery import fetch_json, text_from_html, make_op, snapshot
from .models import timestamp
from .signals import SELLER, COMMERCIAL_RULES, normalize_intent, PAIN
from .signals import cluster_for


def fetch_page(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'demand-opportunity-engine/0.3 public-demand-research'})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode('utf-8', errors='replace')


def attempt(family, url, method):
    return dict(source_family=family, access_method=method, url=url, records_inspected=0,
                primary_pages_opened=0, verified_buyer_requests=0, explicit_commercial_signals=0,
                collected=0, errors=[], limitations=[], evidence_snapshots=[])


def fit_job(op):
    """Narrow proposals, never invented portfolios or control of buyer systems."""
    text = op.source_text.lower()
    title_cluster = cluster_for(op.title)
    if title_cluster != 'unclassified':
        op.cluster_name = title_cluster
    if op.buyer_role == 'BUYER':
        op.suggested_offer = 'One buyer-specified remote workflow: agree inputs/output, implement in authorized sandbox, test cases and handover; no unscoped rebuild'
        op.suggested_price_range = 'USD 100–200 paid scoping pilot; implementation quote after access/scope review (proposal, not buyer budget)'
        op.first_message = 'Which first workflow and acceptance criteria should a small paid pilot cover? I will disclose actual experience and only quote after checking authorized access and scope.'
        op.required_capabilities += ['Buyer-approved narrow scope and actual relevant portfolio/timezone fit must be checked'] if not op.required_capabilities else []
    op.why_now = 'Original publication and substantive buyer follow-up determine freshness; public supplier replies do not. Confirm availability before quoting.'
    if 'stress-test' in text or 'stress testing' in text:
        op.suggested_offer = 'QA one existing n8n agent: agreed test cases, edge-case/error-handling report and prioritized fixes; no rebuild'
        op.suggested_price_range = 'USD 150–250 fixed QA pilot (test proposal, not stated buyer budget); fixes scoped separately'
        op.first_message = 'For your one-agent paid trial, which agent and acceptance cases matter first? I can scope a sandbox QA report before any fixes. I will state my actual Vapi/Twilio/ElevenLabs experience rather than claim unverified projects.'
        op.effort = '4–6 hours for one bounded QA pilot; integration fixes require separate estimate'
        op.required_capabilities = ['Buyer-authorized sandbox/export and test credentials; call/API test costs agreed in advance', 'Human must evidence actual relevant n8n/voice integration experience before applying']
        op.differentiation = 'A one-agent pass/fail test matrix tied to the requested paid trial; no claim that this beats existing suppliers'
        op.next_action = 'Optional validation only: assess actual portfolio fit and visible competition, then use the invited forum DM if account permits; ask if the one-agent paid trial is still open.'
        op.contact_path = op.target_profile_url
        op.contact_channel = 'Buyer-invited n8n forum DM, only where account rules permit'
    elif 'looker studio' in text and 'meta ads' in text:
        op.suggested_offer = 'Buyer-defined paid test: one Meta Ads account + GA4 to Sheet, existing Looker template, Monday summary email and error alert; no new product UI'
        op.suggested_price_range = 'USD 100–115 fixed test subject to API access and scope (buyer states approx USD 115 / INR 10,000)'
        op.effort = '6–10 hours provisional; 7-day buyer timeline; reject if API scope exceeds budget'
        op.required_capabilities = ['Actual Meta/Google Ads API portfolio proof required; not currently verified', 'Buyer-owned n8n, Google and Meta accounts; authorized test access', 'IST overlap and 4-week capacity confirmation']
        op.contact_channel = 'Buyer-posted application email merrill.sequeira@gmail.com; verify address on source first'
        op.first_message = 'Is the INR 10,000 paid test still open? If actual ads API examples are available, answer your five application questions with one-account scope, tool-cost assumptions and capacity; do not send a generic pitch.'
        op.next_action = 'VALIDATE only: confirm role is still open and actual portfolio/timezone fit through buyer-posted application email; publication is 8–14 days old.'
        op.risk = 'Stale without buyer renewal; budget tight; ads API permissions and portfolio fit unverified. No private credentials requested before scope/consent.'
    elif 'marketing' in text and ('apparel' in text or 'consumer' in text):
        op.fulfillment_mode = 'PARTNER_REQUIRED'
        op.required_capabilities = ['Verified consumer-brand marketing judgment and measurable sales case studies not currently established', 'Buyer consent, brand facts and existing Shopify/email access']
        op.suggested_offer = 'Implementation-only pilot: one approved story to email/social drafts and a human approval queue; full marketing role requires a proven partner'
        op.suggested_price_range = 'USD 250–400 scoped technical pilot only if buyer accepts narrower remit; not a buyer budget'
        op.first_message = 'You require proven consumer-brand marketing results. I would disclose that gap and ask whether a separate implementation-only approval workflow is useful; never imply an apparel sales track record.'
        op.effort = '6–10 hours technical pilot after brand/tool scope; full engagement not estimated'
        op.risk += ' Buyer seeks both strategy and implementation; operator case-study fit unverified.'
        op.next_action = 'Do not apply for the full strategic role without actual consumer-brand proof or a confirmed partner.'
    elif 'operations lead' in text or 'project & delivery management' in text:
        op.fulfillment_mode = 'PARTNER_REQUIRED'
        op.required_capabilities = ['Senior operational/team leadership and MENA client track record not established']
        op.suggested_offer = 'One bounded workflow implementation only if buyer separates it from the senior operations lead role'
        op.first_message = 'Is there a standalone workflow scope, separate from the senior operations/management contract? Disclose actual leadership experience and capacity.'
        op.risk += ' Senior ongoing leadership role is not equivalent to a 2-hour workflow diagnostic.'
    if 'no existing clients' in text:
        op.risk += ' Source explicitly has no existing clients; paid work is conditional on future client acquisition, not a ready commission.'
        op.next_action = 'Verify an actual signed client scope and paid budget exist before any work. No speculative free build.'
    op.risk = ". ".join(dict.fromkeys(part.strip().rstrip(".") for part in op.risk.split(". ") if part.strip())) + "."
    return op


def discourse_jobs(config, now, directory, fetch=fetch_json):
    base = config['base_url'].rstrip('/')
    listing = f"{base}/c/jobs/{config['category_id']}.json?order=created"
    audit = attempt('public founder/operator job community', listing, 'Discourse public category/topic JSON')
    ops, seen = [], set()
    for page in range(config.get('pages', 2)):
        url = listing + f'&page={page}'
        try:
            data = fetch(url)
            saved, digest = snapshot({'url':url,'collected_at':now.isoformat(),'source':data}, directory, url)
            audit['evidence_snapshots'].append(f'{saved}#sha256={digest}')
            for row in data['topic_list']['topics']:
                if row['id'] in seen:
                    continue
                seen.add(row['id']); audit['records_inspected'] += 1
                if (timestamp(row['created_at']) > now or
                    timestamp(row['created_at']) < now - timedelta(days=config.get('lookback_days', 30)) or
                    SELLER.search(row['title']) or not re.search(r'workflow|automation|n8n|sourcing|supplier|rfq', row['title'], re.I)):
                    continue
                api = f"{base}/t/{row['id']}.json"
                try:
                    topic = fetch(api); audit['primary_pages_opened'] += 1
                    posts = topic['post_stream']['posts']
                    first = next(p for p in posts if p['post_number'] == 1)
                    # Re-read all public replies, capped to avoid unlimited collection.
                    ids = topic['post_stream'].get('stream', [])
                    loaded = {p['id'] for p in posts}
                    missing = [i for i in ids if i not in loaded]
                    for start in range(0, min(len(missing), config.get('max_reply_fetch', 200)), 20):
                        chunk = missing[start:start+20]
                        reply_url = f"{base}/t/{row['id']}/posts.json?" + '&'.join(f'post_ids[]={i}' for i in chunk)
                        posts.extend(fetch(reply_url)['post_stream']['posts'])
                    unique_posts = {p['id']:p for p in posts}
                    comments = [{'author':p['username'],'text':text_from_html(p['cooked']),
                                 'at':p['created_at'],'url':f"{base}/t/{row['id']}/{p['post_number']}"}
                                for p in unique_posts.values() if p['post_number'] != 1 and timestamp(p['created_at']) <= now]
                    complete = len(unique_posts) == len(ids)
                    op = make_op('n8n Community', 'n8n Jobs', f"{base}/t/{row['slug']}/{row['id']}", api,
                                 topic['title'], text_from_html(first['cooked']), first['username'],
                                 f"{base}/u/{first['username']}", first['created_at'], now.isoformat(),
                                 comments, topic['posts_count']-1, complete,
                                 not topic.get('closed',False) and not topic.get('archived',False),
                                 {'topic':topic,'loaded_posts':list(unique_posts.values())}, directory)
                    op.source_family = audit['source_family']; op.discovery_route = 'DIRECT_LEAD'
                    op.contact_path = op.source_url
                    op.contact_channel = 'n8n Community reply/application'
                    op.risk += ' Platform reply/application rules apply; private DM competition is unobservable.'
                    ops.append(fit_job(op))
                except Exception as exc:
                    audit['errors'].append({'url':api,'error':f'{type(exc).__name__}: {exc}'})
        except Exception as exc:
            audit['errors'].append({'url':url,'error':f'{type(exc).__name__}: {exc}'})
    audit['limitations'] = ['Two newest-topic pages, not complete market coverage; max 200 extra replies per topic. Incomplete competition remains UNKNOWN unless observed high.',
                            'Last activity is not publication time. Only substantive buyer-authored follow-ups can renew a lead.']
    audit['collected'] = len(ops)
    audit['verified_buyer_requests'] = sum(o.buyer_role == 'BUYER' for o in ops)
    audit['explicit_commercial_signals'] = sum(o.commercial_intent_type != 'NONE' for o in ops)
    return ops, audit


def remotive_jobs(config, now, directory, fetch=fetch_json):
    url = config['url']; audit = attempt('public freelance/job listings',url,'Remotive public JSON API; attributed source links')
    ops = []
    try:
        data = fetch(url)
        saved,digest = snapshot({'url':url,'collected_at':now.isoformat(),'source':data},directory,url)
        audit['evidence_snapshots'].append(f'{saved}#sha256={digest}')
        for row in data['jobs']:
            audit['records_inspected'] += 1
            body = text_from_html(row['description'])
            if not PAIN.search(row['title']) or timestamp(row['publication_date']) > now:
                continue
            op = make_op('Remotive', 'Remotive jobs', row['url'], url, row['title'],
                         body, row['company_name'],row['url'],
                         row['publication_date'],now.isoformat(),[],None,False,True,row,directory)
            # Aggregator text is not verified buyer-authored primary evidence until employer page is read.
            op.source_verified = False
            op.raw_evidence_quote = body[:700]
            op.source_family = audit['source_family']; op.discovery_route = 'DIRECT_LEAD'
            op.buyer_role = 'PROBLEM_OBSERVER'; normalize_intent(op)
            op.risk = 'Employer source, location eligibility and contract-vs-employment fit unverified. API listings delayed 24h.'
            ops.append(op)
        audit['limitations'] = ['Employer application pages not verified. No employer-authored quote invented from aggregator job labels.',
                                data.get('0-legal-notice','API attribution required; maximum four calls/day.')]
        audit['collected'] = len(ops)
    except Exception as exc:
        audit['errors'].append({'url':url,'error':f'{type(exc).__name__}: {exc}'})
    return ops, audit


def inspect_public_path(config, now, directory, fetch=fetch_page):
    audit = attempt(config['family'],config['url'], 'bounded public HTTP page inspection')
    try:
        body = fetch(config['url'])
        saved,digest = snapshot({'url':config['url'],'collected_at':now.isoformat(),'body':body},directory,config['url'])
        audit['evidence_snapshots'].append(f'{saved}#sha256={digest}')
        if 'contractsfinder.service.gov.uk' in config['url']:
            links = list(dict.fromkeys(re.findall(r'href="(https://www.contractsfinder.service.gov.uk/notice/[^"?]+)',body)))
            audit['records_inspected'] = len(links)
            for url in links[:3]:
                try:
                    page = fetch(url); audit['primary_pages_opened'] += 1
                    p,d = snapshot({'url':url,'collected_at':now.isoformat(),'body':page},directory,url)
                    audit['evidence_snapshots'].append(f'{p}#sha256={d}')
                except Exception as exc:
                    audit['errors'].append({'url':url,'error':f'{type(exc).__name__}: {exc}'})
            audit['limitations'].append('Search returned procurement notices; up to three detail pages attempted. No buyer request promoted: eligibility, exact remote scope, submission deadline and award status require manual verification.')
        else:
            # A JS shell or bot wall is not a collection of verified requests.
            audit['limitations'].append('No structured primary buyer requests extracted; static shell is not commercial proof. No login or anti-bot evasion.')
    except Exception as exc:
        audit['errors'].append({'url':config['url'],'error':f'{type(exc).__name__}: {exc}'})
    return [], audit


def buyer_sources(config, now, directory):
    ops, audits = [], []
    for name, adapter in [('discourse_jobs',discourse_jobs),('remotive_jobs',remotive_jobs)]:
        if name in config:
            rows,audit = adapter(config[name],now,directory); ops.extend(rows); audits.append(audit)
    for path in config.get('public_buyer_paths',[]):
        rows,audit = inspect_public_path(path,now,directory); ops.extend(rows); audits.append(audit)
    return ops,audits
