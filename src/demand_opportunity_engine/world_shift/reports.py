"""Reproducible reports; analyst hypotheses are separately attributed and dated."""
import json
from pathlib import Path
from .engine import stamp


def strength(e):
    # Ranks evidence class, never topical popularity or industry.
    return {'procurement': 4, 'policy': 3, 'technology': 2, 'market': 2,
            'corporate_action': 1, 'demand': 1}.get(e['category'], 0)


def generate(events, run, output, review=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    header = (f"采集时间：{run['collected_at']}（UTC）；重点最近30天、背景90天。\n\n"
              f"解析 {run['raw_records']} 条；时间过滤后 {run['retained_before_dedup']} 条；"
              f"本轮按公告URL及同一项目采购编号聚类后 {run['unique_this_run']} 条；历史库 {run['historical_events']} 条。\n\n"
              "有界、非代表性样本。首次观察不证明增长；来源声明不等于独立验证。"
              "未披露的采购预算、收入、付费客户和政策生效时间均保持未知。仅给日期的来源保留原文日期；UTC零点仅用于排序，不代表真实发生时刻。\n\n")
    current_ids = {s['source_id'] for s in run['sources'] if s['status'] == 'OK'}
    current = [e for e in events if e['last_verified_at'] == run['collected_at'] and e['source_id'] in current_ids]
    daily = '# WORLD SHIFT DAILY\n\n' + header
    if review:
        daily += review.get('overview', '') + '\n\n'
    daily += '## 证据清单（按证据类别强度，非机会评分）\n\n'
    selected = {ref for section in ('signals', 'hypotheses') for item in (review or {}).get(section, []) for ref in item['evidence_ids']}
    highlights = [e for e in current if e['id'] in selected] if selected else sorted(current, key=lambda x: -strength(x))[:10]
    for e in sorted(highlights, key=lambda x: (-strength(x), x.get('published_at') or '', x['id'])):
        daily += (f"### {e['title']}\n\n"
                  f"- ID：`{e['id']}`；[{e['source_name']}]({e['url']})\n"
                  f"- 公布：{e.get('published_at_source') or e['published_at'] or '未知'}；原始事件：{e.get('event_at_source') or e.get('event_at') or '未单独确认'}；{e['freshness']}\n"
                  f"- {e['country']} / {e['industry']} / {e['event_type']}\n"
                  f"- 来源摘录：{e['evidence_excerpt'][:650]}\n"
                  f"- 重要性边界：{e['payment_evidence']['status']}；{e['credibility']}。{e['historical_change']}\n"
                  f"- 缺口：{'；'.join(e['unknowns'])}\n\n")
    daily += f'完整 {len(current)} 条本轮核验证据及快照路径见 `data/world_shift/events.json`；此处只列研究引用条目，其他采集条目不自动升格为信号。\n\n'
    if not current:
        daily += '本轮没有可报告的新核验证据。\n'
    early = '# EARLY SIGNALS\n\n' + header
    hypo = '# OPPORTUNITY HYPOTHESES\n\n' + header
    if review:
        index = {e['id']: e for e in events}
        for section, target in [('signals', 'early'), ('hypotheses', 'hypo')]:
            entries = review.get(section, [])
            if section == 'hypotheses' and len(entries) > 3:
                raise ValueError('At most three research hypotheses')
            for item in entries:
                refs = item['evidence_ids']
                if not refs or any(x not in index for x in refs):
                    raise ValueError('Review must reference stored evidence IDs')
                if section == 'hypotheses':
                    for required in ('support', 'counterevidence', 'unknowns', 'falsifiers', 'dimensions'):
                        if not item.get(required):
                            raise ValueError('Incomplete hypothesis: ' + required)
                block = f"## {item['title']}\n\n人工研究判断日期：{review['reviewed_at']}；不会随自动采集刷新。\n\n{item['analysis']}\n\n"
                for field in ('support', 'counterevidence', 'unknowns', 'falsifiers', 'dimensions'):
                    if field in item:
                        label = {'support': '支持证据', 'counterevidence': '反面证据', 'unknowns': '未知问题', 'falsifiers': '推翻条件', 'dimensions': '五维判断'}[field]
                        block += f"**{label}**：{item[field]}\n\n"
                block += '证据：' + '；'.join(f"[{index[x]['title']}]({index[x]['url']})（{x}）" for x in refs) + '\n\n'
                if target == 'early':
                    early += block
                else:
                    hypo += block
    if not review or not review.get('hypotheses'):
        hypo += '目前没有发现足够可靠的新机会。未生成自动商业假设；需要原始采购、预算和买方验证。\n'
    if not review or not review.get('signals'):
        early += '尚无经人工复核的早期信号；新旧程度和商业化程度未知。\n'
    health = '# SOURCE HEALTH\n\n' + header
    health += ('|源/类别|访问|本次尝试 / 最近成功|解析/保留|过旧/未来|缺失字段|失败原因|\n'
               '|---|---|---|---|---|---|---|\n')
    for s in run['sources']:
        health += (f"|[{s['name']}]({s['url']}) / {s['category']}|{s['status']}|{s['attempted_at']} / "
                   f"{s['last_successful_collection_at'] or '本轮无成功'}|{s['fetched']}/{s['retained']}|"
                   f"{s['outside_window']}/{s['future_dated']}|{json.dumps(s['missing_fields'], ensure_ascii=False)}|"
                   f"{s['failure'] or '—'}|\n")
    health += '\n## 新鲜度与覆盖限制\n\n'
    for s in run['sources']:
        subset = [e for e in current if e['source_id'] == s['source_id']]
        dates = [e.get('event_at') or e.get('published_at') for e in subset]
        dates = sorted(d for d in dates if d)
        health += (f"- {s['source_id']}：本轮可知日期 {dates[0] if dates else '未知'} 至 {dates[-1] if dates else '未知'}；"
                   f"无日期 {sum(e['freshness'] == 'UNDATED_BASELINE' for e in subset)}。\n")
    health += ('\n同一 canonical URL 去重；World Bank 按项目ID+采购编号聚类，保留各批次/标段/授标原始公告，不视作独立需求；不把重复关键词命中的公告当独立需求。'
               '跨 URL 转载还须人工记录同一 underlying_event_key；未实现语义自动归并，不能按来源数量推断独立支持。'
               '采购 API 按关键词各取25条、未翻页；HF 各取最近修改的10–15模型；HN 每查询15–20条，均非全市场。'
               'RSS日期是发布而非项目投资发生日期；政策索引只有公布日期，正文及生效日须另核验。'
               '来源失败不删除历史证据，也不更新其 last_verified_at。原始快照 SHA256 见运行 JSON。\n')
    for name, document in [('WORLD_SHIFT_DAILY', daily), ('EARLY_SIGNALS', early),
                           ('OPPORTUNITY_HYPOTHESES', hypo), ('SOURCE_HEALTH', health)]:
        (output / (name + '.md')).write_text('\n'.join(line.rstrip() for line in document.splitlines()).rstrip() + '\n')
