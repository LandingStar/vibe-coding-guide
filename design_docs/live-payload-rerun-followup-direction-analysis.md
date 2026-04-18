# Direction Analysis — After Live Payload Rerun Verification

## 背景

`design_docs/stages/planning-gate/2026-04-16-live-payload-rerun-verification.md` 已完成执行，并在 `review/live-payload-rerun-verification-2026-04-16.md` 中记录了单次受控 live `LLMWorker` rerun 结果：

1. raw response 直接使用了 schema 允许的 `operation=update` 与 `content_type=markdown`。
2. 最终 `LLMWorker` report 通过校验，状态为 `completed`。
3. payload writeback 在临时目录真实命中 `docs/controlled-dogfood-llm.md`。

这意味着上一轮 `LLMWorker Live Payload Contract Hardening` 已经至少在一条受控 real-model path 上得到正向验证。

## 当前判断

当前最重要的新变化不是“还要不要继续修 hardening”，而是：

1. 本地实现面暂时没有新的直接缺口暴露出来。
2. 当前剩余问题开始从 implementation gap 转向 boundary judgment。
3. `docs/first-stable-release-boundary.md` 仍然要求我们不要把单条 real-worker success 误读成默认稳定面承诺。

因此，下一步默认不应再起新的 runtime hardening 切片，而应先处理“如何解释这次成功”的边界问题。

## 候选方向

### A. 受控 real-worker payload adoption judgment

做什么：

1. 明确一次成功 live rerun 在当前 preview / dogfood 口径下意味着什么。
2. 规定继续 dogfood 所需的最小证据门，而不是直接升级为稳定面声明。
3. 让 `LLMWorker` real payload path 的当前可用性表述与 `docs/first-stable-release-boundary.md` 对齐。

为什么是现在：

1. 当前最缺的不是更多本地实现，而是如何安全解释已经拿到的正向 real signal。
2. 若跳过这个判断，后续容易在一次成功后过早扩大对 real-worker 路径的默认承诺。

依据：

- `review/live-payload-rerun-verification-2026-04-16.md`
- `design_docs/stages/planning-gate/2026-04-16-live-payload-rerun-verification.md`
- `docs/first-stable-release-boundary.md`

风险：低到中。

### B. HTTPWorker failure fallback schema alignment

做什么：

1. 只处理 `HTTPWorker` 本地 failure fallback 与当前 `Subagent Report` schema 的一致性。
2. 不改变远端成功态透传边界。

为什么仍可做：

1. 它与本次 `LLMWorker` live success 基本正交。
2. 这是一个低风险、局部一致性切片。

依据：

- `docs/subagent-schemas.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/Project Master Checklist.md`

风险：低。

### C. 暂不进入新实现，只记录 adoption/backlog judgment

做什么：

1. 暂时不进入新的实现或验证切片。
2. 只把本次 live success 对 backlog 与 dogfood 口径的影响写清楚。

为什么可选：

1. 当前没有新的 implementation bug 被暴露。
2. 若你希望先压缩文档口径，这是一条更保守的停点。

依据：

- `review/live-payload-rerun-verification-2026-04-16.md`
- `docs/first-stable-release-boundary.md`
- `design_docs/direction-candidates-after-phase-35.md`

风险：低。

## 当前推荐

我当前倾向于优先进入 **A. 受控 real-worker payload adoption judgment**。

原因：

1. 这次 live rerun 已经给出正向 signal，但还不足以直接上升成默认稳定面声明。
2. 此时继续写代码的收益低于先把 adoption 边界说清楚。
3. 只有先完成这一步，后续才知道应该继续积累 dogfood 证据，还是转去处理别的 real-worker 一致性问题。