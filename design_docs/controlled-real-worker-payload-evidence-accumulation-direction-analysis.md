# Direction Analysis — After Real-Worker Payload Adoption Judgment

## 背景

`design_docs/stages/planning-gate/2026-04-16-real-worker-payload-adoption-judgment.md` 已完成执行，并在 `review/real-worker-payload-adoption-judgment-2026-04-16.md` 中收口出当前判断：

1. `LLMWorker` real-worker payload path 已有 1 条正向 live signal。
2. 当前仍不能把 real-worker payload path 升格为默认稳定面。
3. 若要扩大 adoption wording，最小额外证据门是再拿到 1 条在无新 runtime 改动前提下的独立受控 live success。

这意味着下一步默认不再是继续争论 adoption wording 本身，而是选择是否去满足这条最小额外证据门。

## 当前判断

当前最有价值的新工作不再是继续写 `LLMWorker` runtime 代码，而是：

1. 决定是否要再做 1 条独立受控 rerun，验证这次成功不是偶发 signal。
2. 若不做，就保持当前 wording 停留在“1 条正向 live signal”。
3. 用户新增记录的 dogfood 证据/问题/反馈整合组件或 skill，仍应保留在 backlog，而不是抢在证据门之前进入实现。

## 候选方向

### A. controlled real-worker payload evidence accumulation

做什么：

1. 在无新 runtime code、schema 或 worker 语义变更的前提下，再执行 1 条独立受控 live rerun。
2. 继续保持窄 `allowed_artifacts` 边界。
3. 继续按 raw response / final report / writeback outcome 三层证据归档。

为什么是现在：

1. adoption judgment 已经把最小额外证据门写清楚。
2. 现在最自然的下一步，就是决定是否去满足这条门。

依据：

- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `review/live-payload-rerun-verification-2026-04-16.md`
- `docs/first-stable-release-boundary.md`

风险：低到中。

### B. HTTPWorker failure fallback schema alignment

做什么：

1. 只处理 `HTTPWorker` 本地 failure fallback 与当前 `Subagent Report` schema 的一致性。
2. 不改变远端成功态透传边界。

为什么仍可做：

1. 它与当前 `LLMWorker` positive signal 基本正交。
2. 若你不想继续积累 real-worker 证据，它仍是一个低风险替代切片。

依据：

- `docs/subagent-schemas.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/Project Master Checklist.md`

风险：低。

### C. dogfood evidence / issue / feedback integration direction only

做什么：

1. 不直接实现组件或 skill。
2. 先把证据收集、问题收集、反馈整合的抽象边界整理成单独方向分析，为后续 backlog 转 gate 做准备。

为什么可选：

1. adoption judgment 已证明这条需求不是凭空提出。
2. 但它当前仍低于最小额外证据门。

依据：

- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `design_docs/Project Master Checklist.md`
- `review/research-compass.md`

风险：低。

## 当前推荐

我当前倾向于优先进入 **A. controlled real-worker payload evidence accumulation**。

原因：

1. adoption judgment 已经把口径边界说清楚了。
2. 现在继续积累 1 条独立受控成功信号，比提前实现 dogfood 组件或 skill 更直接地回答当前最关键的不确定性。
3. 若下一条 rerun 失败，价值也很高，因为它会直接界定当前 wording 只能停在什么层级。