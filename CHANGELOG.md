# 更新记录

## 0.1.0 · 2026-10-05

第 0 段的第一批内容。

- 门禁 G02（分区不跨族）、G04（保留集零接触）、G06（退化策略底线，按凸包判定，执行失败按最坏情况计分），以及 `gates/run_all.py`。未实现的门禁明确报告为 `not_implemented`。
- 常量退化策略：always_allow、always_block、always_clarify。
- `contracts/crosswalk.csv`：DATA-02 本体 34 条条款，对照 GOV-01 与 LIT-01 的引用；另列 6 条本体未登记的第七章条款。
- `rulings/OPEN.md`：汇总 11 条本体待审、6 处 GOV-01 ❓、1 条新发现。
- 三个角色 SOP 草稿与阶段表。
- 21 项单元测试，纯标准库，Python 3.10 及以上。
