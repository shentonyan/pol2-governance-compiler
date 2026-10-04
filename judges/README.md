# 判定器适配（第 2 段）

尚未实现。计划的统一接口：

```text
predict(inputs) -> 每条一行 PROTOCOL 预测：id, status, issues, action, latency_ms, execution_status[, status_probs]
```

候选来源以 PoL-Governance 的[模型清单](https://github.com/naturaldao/NaturalDAO/blob/main/PoL-Governance/models/CATALOG.md)为准。第一批计划接入：

| 适配器 | 说明 |
|---|---|
| ollama_typed | 本地 Ollama 模型，以 noul / choice 问题形式输出概率 |
| kev_http | 包装 PoL-Governance 已有的 `benchmark/kev_adapter.py`，不重写 |
| laya_local | 本地 Laya 编码器 |

官方 Jev 按 DATA-02 的结论只作外部基线，不进入候选池。
