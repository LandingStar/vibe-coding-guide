# Direction Analysis — Live Payload Rerun Verification

## 文档定位

本文件用于承接 `LLMWorker Live Payload Contract Hardening` 完成后的下一方向分析。

它只回答一个问题：既然 prompt contract、narrow `content_type` alias normalization 与 attempted-payload rejection -> `partial` 已经落地，下一步更应该优先验证什么。

## 当前输入事实

1. `LLMWorker Live Payload Contract Hardening` 已完成，且通过 targeted regression `55 passed, 1 skipped` 与全量回归 `946 passed, 2 skipped`。
2. 当前真实缺口不是本地 schema-valid report 是否还能成立，而是新的 hardening 是否真的改善 live real-model 的 payload writeback 命中率。
3. `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md` 已证明 live DashScope 路径此前会出现 `upsert`、`text/markdown` 这类 payload drift。
4. 当前实现已经针对这些已知 drift 做了最窄的 contract hardening，但还没有做新的 live rerun。
5. `docs/first-stable-release-boundary.md` 已明确 real worker adapters 不属于默认稳定面，因此下一步应保持在“收集真实 signal”的窄边界，而不是趁机扩大 stable-surface 承诺。

## 候选方向

### A. live payload rerun verification

- 做什么：复跑一条受控 `LLMWorker` real-model path，观察新的 prompt + normalization + status policy 会把真实结果推到哪一类：
  - artifact writeback 成功触发
  - payload 仍被拒绝，但 `partial` 表征更准确
  - 仍出现新的 drift 形态
- 为什么现在最值：实现面已经闭环，再继续本地加逻辑只会增加猜测；而 live rerun 是当前最便宜、信息增益最大的下一步。
- 非目标：
  - 不继续扩大 normalization 范围
  - 不改 schema
  - 不顺手并入 `HTTPWorker`
  - 不把一次 live run 结果夸大为稳定面承诺
- 风险：低到中。主要风险是外部模型与 API 环境的非确定性，但这正是当前需要重新测量的真实因素。

### B. HTTPWorker failure fallback schema alignment

- 做什么：把 `HTTPWorker` 的本地 error fallback 拉回当前 `Subagent Report` schema，但不改远端成功态透传边界。
- 为什么优先级次于 A：这条线虽然合理，但当前没有新的 trigger signal；相比之下，`LLMWorker` 已经刚完成 hardening，实现后的第一条真实反馈更紧迫。
- 风险：低。

### C. driver / adapter backlog-recording only

- 做什么：继续把低优先级 driver / adapter / 转接层问题压成文档切片，不进入新的 real-worker 行为验证。
- 为什么优先级更低：这条线不会立刻回答当前最关键的问题，即新 hardening 对 live payload writeback 的真实影响。
- 风险：低。

## 当前判断

我当前推荐直接进入 **A. live payload rerun verification**。

理由很简单：

1. 当前 hardening 已经足够窄，本地实现继续扩不会比 live rerun 更有信息。
2. `HTTPWorker` 路线没有新的近场 signal，优先级自然排在后面。
3. real worker adapters 仍不属于默认稳定面，因此下一步最合理的是继续收集真实 evidence，而不是扩大承诺边界。

## 建议边界

若进入 A，下一切片建议只做：

1. 用同一类受控 `allowed_artifacts` 场景复跑一条 live `LLMWorker` 请求。
2. 记录 raw response 与最终 report / writeback 结果。
3. 只根据新的 live signal 决定是否需要下一条实现切片。

若进入 A，下一切片明确不做：

1. 不追加新的 schema 或 validator framework。
2. 不把 `upsert` 做自动语义映射。
3. 不在没有新 signal 的前提下继续扩 alias normalization。