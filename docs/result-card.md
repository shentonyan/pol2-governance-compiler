# 机器可读结果卡

文字版结果卡沿用 PoL-Governance 的 [results 模板](https://github.com/naturaldao/NaturalDAO/blob/main/PoL-Governance/results/CARD.template.md)。旁边再放一份 `card.json`，让门禁核对文字版里的说法。模板见 [results/card.template.json](../results/card.template.json)。

| 字段 | 含义 | 由谁检查 |
|---|---|---|
| `candidate` | 候选治理层的名字 | — |
| `data.version` | 数据版本，例如 commit 或数据集 id | — |
| `data.reference_status` | `proposed_unreviewed` 或 `reviewed` | G09 与数据中的 annotation_status 核对 |
| `data.eligible_for_ranking` | 是否参与排名；需要已审定标签且不在 pilot 上 | G09 |
| `evaluation.split` | 被评测的分区 | G09 与数据核对 |
| `evaluation.blind` | 是否声称盲测；只有独立评测者在保留集上、且测试集未被看过时才能为 true | G09 |
| `evaluation.public_test_seen` | 构建候选时是否看过这份测试集 | G09 |
| `evaluation.evaluator` | `self` 或 `independent` | G09 |
| `thresholds.case_ids` | 定阈值所用的 case id；空列表表示没有调过阈值 | G05 |
| `lineage.generator` / `truth` / `judges` | 出题、标注、判定所用的模型：name、family，微调模型另写 base_family | G07 |
| `clauses` | 声称覆盖的条款 id | G08 |
| `latency.requests` / `failures` / `p50_ms` / `p95_ms` | 请求数、失败数、延迟分位数；必须与预测文件重算的结果一致 | G10 |
| `latency.hardware_class` / `concurrency` | 硬件类别与并发数；写类别，不写型号 | G10 |
| `honesty.*` | 三条诚实声明，必须都为 true | G09 |

三条诚实声明：

- `reference_not_gold_unless_reviewed`：参考标签未经独立审定时，不称为金标准。
- `no_generalisation_to_real_people`：合成数据上的结论不推广到真实人群。
- `negative_results_reported`：未改善、低于底线、门禁不过的结果照常提交。
