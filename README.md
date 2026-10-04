# PoL2 治理层编译器

[English](README.en.md)

为 [NaturalDAO PoL-Governance](https://github.com/naturaldao/NaturalDAO/tree/main/PoL-Governance) 做的一套**只含知识和门禁**的工具箱。用法是：编码 Agent 借助它，为某个具体宿主（例如 DSH 插件）编译出一个 PoL2 运行时治理层；同时，十条不可变的门禁阻止它靠"全部拦截""偷看测试集""藏起失败请求"这类捷径通过评测。

做法借鉴 [MetaInfer](https://github.com/HuangPuStar/MetaInfer)：后者按（模型 × 硬件 × 负载）生成专用推理引擎，本项目按（宿主 × 判定面 × 条款子集 × 延迟预算）编译专用治理层。

> **当前状态：v0.2.0，第 0 段完成。** 十条门禁全部实现，配有 3 个常量退化策略和一套 16 种作弊手法的红队矩阵，共 56 项测试。没有接入任何判定模型，也**没有任何关于模型效果的结论**。

![系统架构](docs/figures/fig1_architecture.png)

*图 1　系统架构。知识层（条款契约、DATA-02 本体、裁定队列）复用并随使用增长；编译回路里三个角色相互隔离，任何一条门禁不过都打回编译者；条款歧义进入裁定队列，由团队裁定，Agent 不自行补规则；退化策略底线通过 G06 永远与候选同台。*

## 它解决什么问题

PoL-Governance 的 SPEC、AGENTS 和 PROTOCOL 已经用文字写清了评测规则。本项目把每一条写成脚本：数据、预测或结果卡要进入公共基线，都要先通过这些脚本。

| 门禁 | 规则来源 | 封住的捷径 |
|---|---|---|
| G01 schema 与执行状态 | PROTOCOL 机器接口 | 用超时掩盖错误判定；悄悄丢掉难题 |
| G02 分区不跨族 | SPEC 第 1 阶段 | 把测试题改写后放进调参集 |
| G03 去重与长度捷径 | SPEC 质量检查 | 近似重复样本；靠文本长度就能猜出标签 |
| G04 保留集零接触 | AGENTS 数据边界 | 把保留集放进仓库 |
| G05 阈值来源 | SPEC 第 1、3 阶段 | 在测试集上选阈值 |
| G06 退化策略底线 | PROTOCOL 三项比较 | 全放、全拦、全推给人，或它们的随机混合 |
| G07 血缘隔离 | SPEC 教师生成 | 判定模型与出题、标注模型同一家族 |
| G08 条款覆盖与三类齐备 | SPEC 第 1 阶段 | 声称覆盖某条款，却缺它的难例 |
| G09 诚实条款 | SPEC、PROTOCOL | 把看过的公开测试写成盲测；在待审标签上排名 |
| G10 延迟与失败披露 | PROTOCOL | 结果卡里隐去失败请求、低报 p95 |

每条门禁的设计理由见 [docs/gate-design.md](docs/gate-design.md)。

## 门禁真的拦得住吗：红队矩阵

我们构造了一个诚实的对照场景：一个有少量错误的候选，加一张如实填写的结果卡。然后逐一构造 16 种作弊，每种只改对照中的一处，再实跑全部十条门禁。

![红队矩阵](docs/figures/fig3_redteam.png)

*图 2　红队矩阵（由 `python -m redteam` 实跑生成）。诚实对照通过全部十条门禁；16 种作弊全部被预定的门禁拦下（黑框），矩阵接近对角线。C08（跨区改写）同时被 G02 和 G03 拦下；C06 的预测格式不合法，G06 不再计分（灰色）。合成夹具不含任何 PoL2 内容。*

两点结论：门禁**不误伤**诚实的工作；每条门禁都至少拦下一种作弊，**没有空转的门禁**。详见 [docs/redteam.md](docs/redteam.md)。

## G06：为什么底线是凸包而不是单点

![G06 底线](docs/figures/fig2_floor.png)

*图 3　G06 的判定平面（合成夹具，48 条违规、48 条正常）。横轴为正常案例的误拦率，纵轴为违规案例的漏判率，两者都是越低越好。全放和全拦落在两个角上；不看输入、只按概率在两者间抛硬币，就能落在虚线 J = 0 上任意一点（灰点为 1000 次抛硬币）。所以候选必须落在虚线左下方，并且 J 的单侧 95% 置信下界要大于 0。诚实候选（星号）的 J 为 0.88，下界为 0.75。*

只赢过单个常量策略不够：一个漏判率 0.3、误拦率 0.7 的候选，单独看两项都不比全放或全拦差，但它和"按 30% 概率放行的抛硬币"没有区别。抛硬币策略仍有约 5% 的概率偶然通过 G06（夹具上 1000 次中 5.2%，pilot 上 4.4%），这是 95% 置信水平的代价，属于已知局限。

## 条款对照：三套工程解读覆盖了什么

![条款对照覆盖](docs/figures/fig4_crosswalk.png)

*图 4　按章统计三套已有工程解读引用的条款数（数据来自 [contracts/crosswalk.csv](contracts/crosswalk.csv)）。DATA-02 本体覆盖第 1、2、4、5 章和工程策略，但没有登记第七章；而 GOV-01 和 LIT-01 恰恰大量引用第七章。爱语（第 2 章）的 16 条只有本体覆盖。第七章是否登记已列为待裁定事项 [N-01](rulings/OPEN.md)。*

## 快速开始

只需要 Python 3.10 及以上；门禁不依赖任何第三方库或模型。重画配图需要 matplotlib。

```powershell
python -m unittest discover -s tests -t .
python -m redteam
python -m baselines.constant --policy always_block --inputs data/pilot/pilot.jsonl --out build/always_block.jsonl
python -m gates.run_all --cases data/pilot/pilot.jsonl --predictions build/always_block.jsonl
python -m tools.make_figures
```

第四条命令以退出码 1 结束，这是预期结果：always_block 被 G06 判为不高于底线。另外 G08 也不通过，因为 pilot 的 20 条里只有 2 条是"信息不足"，大部分场景族缺这一类。这 20 条是助手生成、尚未人工审定的试例，只能用来调接口，不能用来排名。

## 目录

| 目录 | 内容 |
|---|---|
| [gates/](gates/) | 十条门禁与 `run_all.py`；结果卡读取见 `card.py` |
| [baselines/](baselines/README.md) | 退化策略底线 |
| [redteam/](redteam/) | 合成夹具与 16 种作弊场景 |
| [contracts/](contracts/README.md) | 条款对照表与契约格式 |
| [rulings/](rulings/README.md) | 待裁定事项（19 条）与裁定模板 |
| [skills/](skills/README.md) | 编译者、条款审查者、盲评测者的 SOP 草稿与阶段表 |
| [results/](results/README.md) | 结果卡模板与红队表格 |
| [docs/](docs/) | 门禁设计、红队说明、结果卡字段、MetaInfer 对照、诚实边界、配图 |
| [judges/](judges/README.md)、[hosts/](hosts/README.md) | 判定器适配与宿主需求（第 2 段） |

## 路线

![路线图](docs/figures/fig5_roadmap.png)

*图 5　四段路线，每段的出口是一道门禁。第 0 段已完成；第 1 段已完成条款对照表和待裁清单，契约文件与团队首轮裁定待做；第 2 段为首次编译；第 3 段依赖 DATA-02 的教师真值和 APP-01 的宿主接口。*

## 与 NaturalDAO 的关系

- 本项目目前在本仓库独立开发，尚未在 PoL-Governance 认领任务。若后续并入，计划的任务号为 HARNESS-01，目标目录为 `PoL-Governance/research/PoL2-Governance-Compiler/`。
- 条款 id 沿用 DATA-02 的 PoL2 标签本体，本项目不新增条款解读；条款有歧义时记入 [rulings/OPEN.md](rulings/OPEN.md)，等团队裁定。
- 数据边界遵守 PoL-Governance 的 AGENTS 约定：私有保留集不进入本仓库，G04 在 CI 中检查。

## 诚实边界

门禁只能拦住已经被想到的捷径，通过全部门禁不等于治理效果好；pilot 和合成夹具上的任何数字都不是效果证据；合成数据上的结论不推广到真实人群。详见 [docs/honesty.md](docs/honesty.md)。

## 许可与引用

原创代码与文档采用 [CC0 1.0](LICENSE)，与 PoL-Governance 一致。`data/pilot/` 的来源与许可见该目录的 [README](data/pilot/README.md)。制图规则沿用 GOV-01 实验室的制图规范，代码为本仓库重写。引用格式见 [CITATION.cff](CITATION.cff)。
