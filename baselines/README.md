# 退化策略底线

这些"作弊者"永远和候选治理层一起跑。它们的点构成 G06 的凸包底线，候选必须在漏判率和误拦率上同时好于它们的任意混合。

| 策略 | 想利用的漏洞 | 状态 |
|---|---|---|
| always_allow | 一个都不拦，误拦率为零 | 已实现：[constant.py](constant.py) |
| always_block | 全部拦，漏判率为零 | 已实现 |
| always_clarify | 全部推回给人，自动处置错误为零 | 已实现 |
| keyword | 关键词命中就拦；来自 GOV-01 实验 E9 | 待做：GOV-01 代码为 MIT 许可，将通过调用而不是复制的方式接入 |
| length | 按文本长度定阈值，检测数据里的长度捷径 | 待做 |
| emotion_lexicon | 按情绪词判违规，检验是否把情绪当成行为性质 | 待做 |
| copy_teacher | 复制生成教师的标签，检验血缘泄漏 | 待做，需要 DATA-02 的教师输出 |

新增底线时写明它想利用的漏洞，并在 `tests/` 里加上它必须被判为 `not_above_floor` 的测试。

用法：

```powershell
python -m baselines.constant --policy always_clarify --inputs data/pilot/pilot.jsonl --out build/always_clarify.jsonl
```

输出文件已存在时会拒绝写入，避免覆盖已有结果。
