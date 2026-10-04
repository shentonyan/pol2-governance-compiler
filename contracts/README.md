# 条款契约

本目录把 PoL2 条款整理成编译器和门禁能读取的形式。**原则：只对齐，不新增解读。**

## 条款 id 从哪里来

条款 id 统一采用 DATA-02 的 PoL2 标签本体 `pol2-labels.v0.1.json`（形如 `PoL.2.10`、`EAP.4.3.3.3`、`ENG.1`）。本体逐条回溯到 PoL2 中文原文，并记录了锚点审计。本项目引用的版本：

- 分支 `pol/DATA-02/wenbo`，commit `8b02ebae8fffa954e1d0316d4fd44b0e200e166b`（2026-10-02）
- 文件：[pol2-labels.v0.1.json](https://github.com/naturaldao/NaturalDAO/blob/8b02ebae8fffa954e1d0316d4fd44b0e200e166b/PoL-Governance/datasets/pol2/ontology/pol2-labels.v0.1.json)
- 34 条注册条款、11 条待审（pending_review）、4 条已裁定（adjudications）

本体合入 NaturalDAO main 之前，本项目只引用它的 commit，不复制其内容。

## 对照表

[crosswalk.csv](crosswalk.csv) 把三套已有的工程解读对到同一个条款 id 上：

| 列 | 含义 |
|---|---|
| `clause_id` | 本体条款 id；本体未登记的条款留空 |
| `in_ontology` | 该条款是否已在本体中登记 |
| `source_doc` | PoL2 原文文件；未登记的条款写到"第几条" |
| `gov01` | GOV-01 实验室 `docs/concept-mapping.md` 中明确引用该条款的小节 |
| `lit01_axes` | LIT-01 文献综述 `data/pol2_axes.json` 的七条轴（A1–A7） |
| `note` | 匹配方式与待核事项 |

对照的依据和可信度：

- GOV-01 列只填 GOV-01 文中写明条款号的地方。
- LIT-01 引用的是 PoL 正文调整章节号之前的编号（例如"5.3.1 平等联结"）。本表按小节标题匹配到现行条款，均标"待核"。
- 第七章（人类公共福利的治理协议）被 GOV-01 和 LIT-01 大量引用，但本体没有登记。是否登记属于团队决定，已列入 [rulings/OPEN.md](../rulings/OPEN.md) 的 N-01。

## 契约文件（第 1 段）

第 1 段为治理层实际要判定的条款各写一个 JSON 契约，字段草案如下。采用 JSON 是为了保持纯标准库、零依赖。

```json
{
  "clause_id": "PoL.2.10",
  "version": 1,
  "ontology_ref": "8b02ebae",
  "criteria": {"conforming": "…", "violating": "…", "insufficient": "…"},
  "non_triggers": ["正当批评", "正当愤怒", "拒绝", "异议", "求救"],
  "failure_modes": ["…"],
  "open_rulings": ["W-08"]
}
```

`criteria` 和 `non_triggers` 只能摘自本体的 criterion、hard_rules 与 JUDGE.md，并注明出处。修改契约时 `version` 加一。
