# 结果

## 红队表格

`python -m redteam` 生成：

- [tables/redteam_matrix.csv](tables/redteam_matrix.csv)：17 个场景 × 10 条门禁的实跑结果
- `tables/coin_flip.json`：1000 次抛硬币在夹具与 pilot 上的 G06 结果

说明见 [docs/redteam.md](../docs/redteam.md)。

## 结果卡

还没有任何真实候选的结果。每次编译和评测后提交两份：

1. 文字版结果卡，沿用 PoL-Governance 的 [results 卡片模板](https://github.com/naturaldao/NaturalDAO/blob/main/PoL-Governance/results/CARD.template.md)；
2. 机器可读的 `card.json`，从 [card.template.json](card.template.json) 复制填写，字段说明见 [docs/result-card.md](../docs/result-card.md)。

再附上 `gates/run_all.py` 的完整输出，包括 `fail` 和 `incomplete`。编译产物（`build/`）不提交。
