# 角色 SOP（草稿 v0.1）

三个角色串行工作，后两个与前一个隔离。角色文件只写知识和流程，不绑定任何 Agent 后端；用 Claude Code、Codex 或本地模型都可以。

| 角色 | 文件 | 能看到 | 看不到 |
|---|---|---|---|
| 编译者 | [compiler/SKILL.md](compiler/SKILL.md) | 宿主需求、契约、train 与 validation 分区 | 公开测试的标签、保留集 |
| 条款审查者 | [clause-reviewer/SKILL.md](clause-reviewer/SKILL.md) | 契约、编译产物的配置 | 任何评测分数 |
| 盲评测者 | [blind-evaluator/SKILL.md](blind-evaluator/SKILL.md) | 无标签输入、编译产物 | proposal、参考标签、教师 prompt、编译过程 |

阶段与门禁的对应见 [phases.md](phases.md)。任一角色发现门禁不过，结果打回编译者；发现条款歧义，写进 `rulings/OPEN.md`，不自行裁定。
