# Planning Gate — Escalation Notification Persisted Surface Contract

> 日期: 2026-05-06
> 状态: PAUSED
> 来源: `mcp_doc-based-cod_workflow_interrupt` during `design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md`

## Why this exists

在当前 `Project Progress Graph Interactive Control Surface` 的最小 source coverage 调研里，已经确认：

1. handoff 当前有真实 persisted owner surface：`.codex/handoffs/CURRENT.md` + canonical handoff markdown
2. `review_intake` 当前只复用 `FeedbackAPI.register()` 的 in-memory pending review surface
3. escalation 当前只有 `EscalationNotifier.notify()` contract 与可选 `src/pep/notifiers/file_notifier.py`
4. 当前 workspace 中没有默认 `FileNotifier` wiring、没有默认 output directory、也没有任何现存 escalation JSON artifact

因此，如果继续把 escalation 纳入 control snapshot，就不再是“消费现有 persisted source”，而会变成“引入新的 persisted artifact contract”。这超出了当前 gate 的最小 source coverage 边界，需要单独记录。

## Scope

本 gate 只处理：

1. escalation notification 是否需要 first-class persisted file surface
2. 若需要，默认 owner surface、默认 output path 与最小 delivery contract 应该是什么
3. 哪条 focused validation 才能证明 escalation artifact 已真实落盘，可被后续 control snapshot 诚实消费

本 gate 不处理：

1. 当前 `design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md` 的继续实现
2. review_intake 的 persistence redesign
3. direct mutation controls
4. daemon replay / history runtime

## Current findings

当前已确认：

1. `src/pep/notifiers/file_notifier.py` 可以把 notification JSON 写到调用方传入的 `output_dir`
2. 当前 `src/` 中没有任何默认 `FileNotifier(...)` 的实例化或默认路径配置
3. `src/runtime/orchestration/landing_dispatch.py` 只依赖抽象的 `EscalationNotifier.notify()`，并不决定 file sink
4. `tests/test_runtime_orchestration_landing_dispatch.py` 对 escalation 只验证 stub notifier；同一文件里 handoff 才有真实 owner-surface file persistence test
5. 当前 workspace 搜索没有任何 escalation JSON artifact

当前判断：在没有新的 persisted artifact contract 之前，escalation 不是可被当前 control snapshot 诚实消费的 source。

## Working hypothesis

当前最小可行路线应是：

1. 若未来确实需要 escalation source coverage，先固定 `FileNotifier` 或等价 file sink 的 owner surface
2. 先明确默认 persisted path，再决定 control snapshot 如何投影它
3. 先补真实落盘 focused validation，再让 graph/control snapshot 消费它

## Activation condition

仅当以下条件满足时再激活本 gate：

1. 当前 active gate 不再把 escalation 误当成“现有 persisted source”
2. 用户明确需要 escalation source coverage，或当前 graph/control overlay 已经消费完 handoff 这条 persisted source
3. 决定要么复用既有 persisted file surface，要么显式引入新的 escalation persistence contract

## First slice suggestion

进入实现时，当前第一刀应只做：

1. 固定 escalation persisted owner surface
2. 固定默认 output path
3. 补一条真实落盘 focused validation
4. 在 validation 成立后，再讨论 control snapshot 是否消费该 artifact