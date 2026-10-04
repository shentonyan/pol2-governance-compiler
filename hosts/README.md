# 宿主需求（第 2 段）

尚未定稿。一份宿主需求描述"要为谁编译治理层"，字段草案如下：

| 字段 | 含义 |
|---|---|
| `host` | 宿主名称，例如 DSH 插件、编码 Agent 的工具调用 |
| `surfaces` | 判定面：user_input、assistant_output、tool_action 中的若干个 |
| `clauses` | 要覆盖的条款 id 子集（取自 `contracts/crosswalk.csv`） |
| `latency_budget_ms_p95` | 每次判定的 p95 延迟上限 |
| `judges_available` | 宿主环境能运行的判定器 |
| `rollout` | shadow（只记录）或 enforce（生效）；按 SPEC 第 4 阶段先影子再启用 |

字段需要与 APP-01 的宿主接口负责人确认后才定稿。
