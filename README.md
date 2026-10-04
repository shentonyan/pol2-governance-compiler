# PoL2 治理层编译器

[English](README.en.md)

为 [NaturalDAO PoL-Governance](https://github.com/naturaldao/NaturalDAO/tree/main/PoL-Governance) 做的一套**只含知识和门禁**的工具箱：让编码 Agent 为某个具体宿主（例如 DSH 插件）编译出一个 PoL2 运行时治理层，并用不可变的门禁阻止它靠"全部拦截""偷看测试集"这类捷径通过评测。

做法借鉴 [MetaInfer](https://github.com/HuangPuStar/MetaInfer)：后者按（模型 × 硬件 × 负载）生成专用推理引擎，本项目按（宿主 × 判定面 × 条款子集 × 延迟预算）编译专用治理层。

> **当前状态：v0.1.0，第 0 段进行中。** 10 条门禁里实现了 3 条（G02、G04、G06），另有 3 个常量退化策略。没有接入任何模型，也**没有任何关于模型效果的结论**。

## 它解决什么问题

PoL-Governance 的 SPEC 和 PROTOCOL 已经用文字写清了评测规则：分区不跨族、保留集不进仓库、阈值只用校验集、全部拒绝不能靠漏判率获得好结论。本项目把这些规则写成脚本，任何数据、预测或结果卡要进入公共基线，都得先过这些脚本。

| 层 | 目录 | 作用 | 状态 |
|---|---|---|---|
| 知识 | [contracts/](contracts/README.md)、[rulings/](rulings/README.md) | 条款对照表；条款歧义的裁定队列 | 对照表与待裁清单已建，契约文件属第 1 段 |
| 门禁 | [gates/](gates/) | 不可变脚本，失败时给出对应的 SPEC 原句 | G02、G04、G06 已实现 |
| 底线 | [baselines/](baselines/README.md) | 永远与候选治理层同台的"作弊者" | 3 个常量策略已实现 |
| 角色 | [skills/](skills/README.md) | 编译者 / 条款审查者 / 盲评测者的 SOP | 草稿 |
| 编译目标 | [judges/](judges/README.md)、[hosts/](hosts/README.md) | 可插拔判定器；宿主需求格式 | 待做 |

设计理由见 [docs/metainfer-mapping.md](docs/metainfer-mapping.md) 和 [docs/gate-design.md](docs/gate-design.md)。

## 快速开始

只需要 Python 3.10 及以上，不需要安装任何依赖或模型。

```powershell
python -m unittest discover -s tests -t .
python -m baselines.constant --policy always_block --inputs data/pilot/pilot.jsonl --out build/always_block.jsonl
python -m gates.run_all --cases data/pilot/pilot.jsonl --predictions build/always_block.jsonl
```

第三条命令以退出码 1 结束，这是预期结果。在 20 条公开试例上（9 条违规、9 条正常、2 条信息不足），三个常量策略的漏判率与误拦率如下：

| 策略 | 漏判率 | 误拦率 | J = 1 − 漏判 − 误拦 |
|---|---|---|---|
| always_allow | 1.00 | 0.00 | 0 |
| always_block | 0.00 | 1.00 | 0 |
| always_clarify | 0.00 | 1.00 | 0 |

把 always_block 当作候选提交，G06 判定它"不高于底线"。任何候选治理层都必须在两项错误率上**同时**好于这些策略的任意随机混合，相当于 J > 0；只好于单个策略不够。原因见 [gate-design.md](docs/gate-design.md#g06-为什么是凸包而不是单点)。

这 20 条是助手生成、尚未人工审定的试例，只用来调接口，不能用来排名。

## 与 NaturalDAO 的关系

- 本项目在 PoL-Governance 的任务号暂定为 HARNESS-01。开发在本仓库进行，第 0–2 段完成后整目录迁入 `PoL-Governance/research/`。
- 条款 id 沿用 DATA-02 的 PoL2 标签本体，本项目不新增条款解读。条款有歧义时进入 [rulings/OPEN.md](rulings/OPEN.md)，等团队裁定。
- 数据边界遵守 PoL-Governance 的 AGENTS 约定：私有保留集不进入本仓库，G04 负责检查。

## 诚实边界

见 [docs/honesty.md](docs/honesty.md)。要点：门禁只能拦住已知的捷径，通过门禁不等于治理效果好；pilot 上的任何数字都不是效果证据；合成数据上的结论不推广到真实人群。

## 许可与引用

原创代码与文档采用 [CC0 1.0](LICENSE)，与 PoL-Governance 一致；`data/pilot/` 的来源与许可见该目录的 [README](data/pilot/README.md)。引用格式见 [CITATION.cff](CITATION.cff)。
