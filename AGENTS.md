# Agent 入口

第一步是读规则，不是写代码。顺序：

1. [docs/gate-design.md](docs/gate-design.md)：十条门禁各自封住什么捷径。
2. [contracts/README.md](contracts/README.md) 和 [contracts/crosswalk.csv](contracts/crosswalk.csv)：条款 id 从哪里来。
3. [rulings/OPEN.md](rulings/OPEN.md)：哪些条款问题还没有定论。
4. 你被分配的角色：[skills/](skills/README.md) 下对应的 SKILL.md。

## 硬规则

- **不改门禁来让自己通过。** `gates/` 与 `baselines/` 的修改只能单独提交，提交说明写明它封住或放开了哪条捷径，并经人审过。
- **不接触私有保留集。** 不读、不请求、不推测其内容；在任何地方看到疑似保留集内容，立即停止并报告。
- **不替原文补规则。** 条款没写清的地方，写进 `rulings/OPEN.md` 等团队裁定，不自行决定。
- **失败如实提交。** 门禁不过、分数不好、低于底线，都写进结果卡；不删除、不挑选运行。
- **评价行为，不评价人。** 任何输出都不给人贴道德标签。
- **不在公开文件里写机器细节**：本机路径、邮箱、显卡型号、账号名都不写。

## 运行

```powershell
python -m unittest discover -s tests -t .
python -m gates.run_all --cases <cases.jsonl> --predictions <predictions.jsonl>
```

`run_all` 的结论只有三种：`fail`、`incomplete`（还有门禁未实现）、`pass`。在十条门禁全部实现之前，结论不可能是 `pass`。
