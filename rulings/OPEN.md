# 待裁定事项

收集自三处来源，原文措辞以来源为准。本页只做汇总和编号，不给出倾向。

最后同步：2026-10-05。

## 来自 DATA-02 本体的 pending_review（11 条）

来源：[pol2-labels.v0.1.json](https://github.com/naturaldao/NaturalDAO/blob/8b02ebae8fffa954e1d0316d4fd44b0e200e166b/PoL-Governance/datasets/pol2/ontology/pol2-labels.v0.1.json) 的 `pending_review`，分支 `pol/DATA-02/wenbo`，commit `8b02eba`。

| 编号 | 本体 id | 条款 | 问题 |
|---|---|---|---|
| W-01 | issue.consent_violation.granularity | PoL.2.10 | "违背持续同意"单列为 issue，还是并入 coercion_manipulation？ |
| W-02 | issue.harm_facilitation.membership | PoL.1.3 | "协助伤害"是否纳入 v1.0 正式 issue 清单？ |
| W-03 | issue.unnecessary_restriction.form | PoL.1.5 | 误拦以独立 issue 表达，还是只用 mitigations 加 status=conforming 表达？ |
| W-04 | issue.tool_scope_overreach.grounding | EAP.4.3.3 | 工具越权的条款锚点是否足够？ |
| W-05 | issue.untrusted_instruction_injection.grounding | PoL.5.4.1 | 不可信文档注入的条款锚点是否足够？ |
| W-06 | polarity.unclear.boundary | EAP.4.3.2 | polarity=unclear 与 polarity=neither 的判定边界如何划定？ |
| W-07 | evidence.three_values.thresholds | PoL.1.3 | sufficient/insufficient/contradictory 的判定阈值由谁定，如何在标注中保持一致？ |
| W-08 | mitigation.consent_continues.silence | PoL.2.10 | 沉默或未回应是否构成撤回（或同意）？ |
| W-09 | love_languages.text_evidence | PoL.2.14 | 载体共振、跨物种共情、宇宙之爱在单轮对话文本中如何取证？ |
| W-10 | issues.multi_label.ordering | PoL.1.2 | 多个 issue 叠加时的优先级与排序规则？ |
| W-11 | surface.tool_action.granularity | PoL.5.4.1 | 工具调用在 PoL2 判据中的粒度如何定义（文本描述与实际调用是否分别判定）？ |

同一文件里已有 4 条在 2026-10-02 裁定：PoL2 定义的两种表述并存、安保警示不视为仇恨攻击、参与战争归入暴力崇拜、文艺作品中的仇恨描写归入游戏与幽默边界。这些以本体为准，不在此重复。

## 来自 GOV-01 实验室的 ❓（6 处）

来源：[PoL2-DAO-Governance-Lab docs/concept-mapping.md](https://github.com/naturaldao/NaturalDAO/blob/053a67b89c9f17e412d5758de7e7f21441eed012/PoL-Governance/research/PoL2-DAO-Governance-Lab/docs/concept-mapping.md)，main `053a67b`。

| 编号 | 条款（* 为本项目推断） | 问题 |
|---|---|---|
| G-01 | 第七章第 2 条 | 自主决策与人类投票：PAI 直接决定、人类只能质询，还是人类投票作为 PAI 决策的输入？ |
| G-02 | 第七章第 4 条 | 透明与隐私：公开记名选票可能带来压力与报复风险。 |
| G-03 | EAP.4.3.2* | 谁来定义恨语标记？基线词表未经协作者共识。 |
| G-04 | EAP.4.3.1 | 筛查的代价由谁承担？模拟显示误报落在少数派的批评上；对少数派用更高阈值是否与"平等对待行为"冲突？ |
| G-05 | EAP.4.3.1 | 身份：一人多号可以击穿二次方投票，而人格证明本身带来隐私与排斥风险。 |
| G-06 | 第七章第 11.5 条 | 修订版本永久存档：专门的修订流程尚未实现。 |

## 本项目对照时发现的（1 条）

| 编号 | 条款 | 问题 |
|---|---|---|
| N-01 | 第七章（人类公共福利的治理协议） | GOV-01 和 LIT-01 多处引用第七章，但本体没有登记该章条款。运行时治理层是否需要判定第七章的条款？如需要，由谁补登记？ |
