# SOURCE HEALTH

采集时间：2026-11-03T09:28:04.931399+00:00（UTC）；重点最近30天、背景90天。

解析 176 条；时间过滤后 129 条；本轮按公告URL及同一项目采购编号聚类后 124 条；历史库 149 条。

有界、非代表性样本。首次观察不证明增长；来源声明不等于独立验证。未披露的采购预算、收入、付费客户和政策生效时间均保持未知。仅给日期的来源保留原文日期；UTC零点仅用于排序，不代表真实发生时刻。

|源/类别|访问|本次尝试 / 最近成功|解析/保留|过旧/未来|缺失字段|失败原因|
|---|---|---|---|---|---|---|
|[World Bank procurement — energy](https://search.worldbank.org/api/v2/procnotices?format=json&rows=25&qterm=energy) / procurement|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|25/23|2/0|{"deadline": 8, "budget": 23, "event_at": 15, "country": 2}|—|
|[World Bank procurement — digital](https://search.worldbank.org/api/v2/procnotices?format=json&rows=25&qterm=digital) / procurement|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|25/19|6/0|{"deadline": 3, "budget": 19, "event_at": 16}|—|
|[World Bank procurement — equipment](https://search.worldbank.org/api/v2/procnotices?format=json&rows=25&qterm=equipment) / procurement|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|25/7|18/0|{"deadline": 6, "budget": 7, "country": 1, "event_at": 1}|—|
|[MIDA general RSS (mixed promotional content; not orders)](https://www.mida.gov.my/feed/) / corporate_action|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|10/10|0/0|{"event_at": 10}|—|
|[Hugging Face Qwen model metadata](https://huggingface.co/api/models?author=Qwen&sort=lastModified&direction=-1&limit=15&full=true) / technology|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|15/14|1/0|{}|—|
|[Hugging Face DeepSeek model metadata](https://huggingface.co/api/models?author=deepseek-ai&sort=lastModified&direction=-1&limit=10&full=true) / technology|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|10/4|6/0|{}|—|
|[SGLang official GitHub releases](https://api.github.com/repos/sgl-project/sglang/releases?per_page=10) / technology|FAILED|2026-11-03T09:28:04.931399+00:00 / 本轮无成功|0/0|0/0|{}|HTTPError: HTTP Error 403: rate limit exceeded|
|[HN public discussion via Algolia — AI](https://hn.algolia.com/api/v1/search_by_date?query=AI&tags=ask_hn&hitsPerPage=20) / demand|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|20/20|0/0|{"event_at": 20, "country": 20}|—|
|[HN public discussion via Algolia — automation](https://hn.algolia.com/api/v1/search_by_date?query=automation&tags=story&hitsPerPage=15) / demand|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|15/15|0/0|{"event_at": 15, "country": 15}|—|
|[DeepSeek official API pricing](https://api-docs.deepseek.com/quick_start/pricing) / market|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|1/1|0/0|{"published_at": 1, "event_at": 1}|—|
|[DeepSeek official changelog](https://api-docs.deepseek.com/updates) / technology|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|1/1|0/0|{}|—|
|[NDRC official notices](https://www.ndrc.gov.cn/xwdt/tzgg/) / policy|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|25/11|14/0|{"event_at": 11}|—|
|[Reddit public machinelearning discussion](https://www.reddit.com/r/MachineLearning/new.json?limit=10) / demand|FAILED|2026-11-03T09:28:04.931399+00:00 / 本轮无成功|0/0|0/0|{}|HTTPError: HTTP Error 403: Blocked|
|[SEC corporate filings RSS](https://www.sec.gov/Archives/edgar/usgaap.rss.xml) / corporate_action|FAILED|2026-11-03T09:28:04.931399+00:00 / 本轮无成功|0/0|0/0|{}|HTTPError: HTTP Error 403: Forbidden|
|[Alibaba Cloud official Netherlands region announcement](https://www.alibabacloud.com/blog/alibaba-cloud-launches-first-public-cloud-region-in-the-netherlands_603704) / corporate_action|FAILED|2026-11-03T09:28:04.931399+00:00 / 本轮无成功|0/0|0/0|{}|ValueError: HTML shell/no substantive article; HTTP 200 is not collection success|
|[MIDA official renewable supply-chain release](https://www.mida.gov.my/media-release/mida-strengthens-malaysias-renewable-energy-supply-chain-at-igem-2026/) / corporate_action|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|1/1|0/0|{}|—|
|[MIDA official data-centre ecosystem release](https://www.mida.gov.my/media-release/mida-charts-next-phase-for-malaysias-data-centre-sector-from-attracting-investment-to-building-value-for-smes-and-malaysians/) / corporate_action|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|1/1|0/0|{}|—|
|[Cloudflare official Workers AI changelog](https://developers.cloudflare.com/changelog/product/workers-ai/) / technology|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|1/1|0/0|{"country": 1}|—|
|[NDRC original Southern regional power market reply](https://www.ndrc.gov.cn/xwdt/tzgg/202610/t20261028_1408425.html) / policy|OK|2026-11-03T09:28:04.931399+00:00 / 2026-11-03T09:28:04.931399+00:00|1/1|0/0|{"event_at": 1}|—|

## 新鲜度与覆盖限制

- wb-energy：本轮可知日期 2026-10-13T00:00:00+00:00 至 2026-11-01T00:00:00+00:00；无日期 0。
- wb-digital：本轮可知日期 2026-08-10T00:00:00+00:00 至 2026-10-30T00:00:00+00:00；无日期 0。
- wb-equipment：本轮可知日期 2026-08-07T00:00:00+00:00 至 2026-10-31T00:00:00+00:00；无日期 0。
- mida：本轮可知日期 2026-10-29T02:04:52+00:00 至 2026-11-02T02:17:43+00:00；无日期 0。
- hf-qwen：本轮可知日期 2026-08-12T10:23:42+00:00 至 2026-10-12T09:45:49+00:00；无日期 0。
- hf-deepseek：本轮可知日期 2026-08-13T16:28:28+00:00 至 2026-10-17T05:46:55+00:00；无日期 0。
- sglang：本轮可知日期 未知 至 未知；无日期 0。
- hn-ai：本轮可知日期 2026-11-01T16:26:34+00:00 至 2026-11-03T06:03:24+00:00；无日期 0。
- hn-automation：本轮可知日期 2026-10-31T12:01:28+00:00 至 2026-11-03T01:58:48+00:00；无日期 0。
- deepseek-pricing：本轮可知日期 未知 至 未知；无日期 1。
- deepseek-updates：本轮可知日期 2026-10-17T00:00:00+00:00 至 2026-10-17T00:00:00+00:00；无日期 0。
- ndrc：本轮可知日期 2026-08-10T00:00:00+00:00 至 2026-10-30T00:00:00+00:00；无日期 0。
- reddit：本轮可知日期 未知 至 未知；无日期 0。
- sec：本轮可知日期 未知 至 未知；无日期 0。
- alibaba-netherlands：本轮可知日期 未知 至 未知；无日期 0。
- mida-re-supply：本轮可知日期 2026-10-08T00:00:00+00:00 至 2026-10-08T00:00:00+00:00；无日期 0。
- mida-dc：本轮可知日期 2026-09-14T00:00:00+00:00 至 2026-09-14T00:00:00+00:00；无日期 0。
- cloudflare-models：本轮可知日期 2026-08-17T00:00:00+00:00 至 2026-08-17T00:00:00+00:00；无日期 0。
- ndrc-south-market：本轮可知日期 2026-10-28T00:00:00+00:00 至 2026-10-28T00:00:00+00:00；无日期 0。

同一 canonical URL 去重；World Bank 按项目ID+采购编号聚类，保留各批次/标段/授标原始公告，不视作独立需求；不把重复关键词命中的公告当独立需求。跨 URL 转载还须人工记录同一 underlying_event_key；未实现语义自动归并，不能按来源数量推断独立支持。采购 API 按关键词各取25条、未翻页；HF 各取最近修改的10–15模型；HN 每查询15–20条，均非全市场。RSS日期是发布而非项目投资发生日期；政策索引只有公布日期，正文及生效日须另核验。来源失败不删除历史证据，也不更新其 last_verified_at。原始快照 SHA256 见运行 JSON。
