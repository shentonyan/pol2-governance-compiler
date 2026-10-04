# 结果卡

还没有结果。每次编译和评测后在这里提交一张结果卡，格式沿用 PoL-Governance 的 [results 卡片模板](https://github.com/naturaldao/NaturalDAO/blob/main/PoL-Governance/results/CARD.template.md)，并额外包括：

- `gates/run_all.py` 的完整输出，包括 `fail` 和 `incomplete`；
- G06 的底线表：每个退化策略的漏判率、误拦率、J，以及候选是否高于底线；
- 数据版本、参考标签状态（待审或已审定）、失败请求数、硬件类别；
- [诚实边界](../docs/honesty.md)中的声明。

编译产物（`build/`）不提交，只提交结果卡和生成它的命令。
