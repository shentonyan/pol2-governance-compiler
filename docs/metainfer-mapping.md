# 从 MetaInfer 借了什么

[MetaInfer](https://github.com/HuangPuStar/MetaInfer) 把"写推理引擎"改写成了一个 Agent 能长时间自主推进、又很难作弊的任务。它的论文代码在 `arxiv-paper` 分支，`master` 已演化成更通用的任务编排平台。下表是本项目对应的位置。

| MetaInfer 的做法 | 它解决什么 | 本项目的对应物 |
|---|---|---|
| 知识图谱 `inference_blueprint.json` 加 28 个不可变测试合约；生成时 Agent 不接触原型引擎 meta0 的源码 | 生成有硬边界，知识可复用 | `contracts/`：沿用 DATA-02 本体的条款 id，汇总各方的工程解读 |
| 不可变 oracle：启动服务、发固定输入、由 LLM 判定正确性，不过则打回 | 防止只追分数的"假实现" | `gates/`：十条门禁 + `baselines/` 的退化策略 |
| 三角色对抗：implementer、spec-reviewer、verification，后两者隔离运行 | 单个 Agent 会自我批准 | `skills/`：编译者、条款审查者、盲评测者 |
| `evolution/` 回灌：知识库覆盖不到的模型先走进化流程，结果写回知识库 | 知识库越用越厚 | `rulings/`：歧义进入裁定队列，团队裁定后写回契约 |
| 按（模型 × 硬件 × 负载）生成单路径引擎，与通用引擎对照 | 专用胜过通用 | 按（宿主 × 判定面 × 条款子集 × 延迟预算）编译治理层，与"一个通用 PoL 判定模型"对照 |

## 两条反面教训

1. **数字要带对照面。** MetaInfer 论文的摘要写明是在关闭 CUDA Graph 的条件下与 vLLM 对比（+41%），而开启 CUDA Graph 的 vLLM 快约 3 倍这一点只出现在正文表格里。标题数字容易被单独引用。本项目每个结果卡都要并列底线和对照组，并写明适用范围。
2. **快照和主线要分开。** MetaInfer 的论文流程只能在冻结的分支上找到。本项目用版本号和 CHANGELOG 区分"已被团队审阅的快照"和"仍在演化的主线"，迁入 NaturalDAO 时注明来自哪个 tag。
