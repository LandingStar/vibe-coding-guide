# Real-Worker Payload Adoption Judgment — 2026-04-16

## 文档定位

本文件记录 `Real-Worker Payload Adoption Judgment` 的收口结果，用来明确：

1. 基于当前单次成功 live rerun，当前可以安全说什么。
2. 当前还不能安全说什么。
3. 若要扩大 adoption wording，最小额外证据门是什么。
4. 在本轮判断过程中，哪些 dogfood 流程已表现出后续可抽象固化的价值。

## 当前可安全表述的判断

基于 `review/live-payload-rerun-verification-2026-04-16.md` 中已经归档的三层证据，当前可以安全说：

1. `LLMWorker` 受控 real-worker payload path 已获得 **1 条正向 live signal**。
2. 这条正向 signal 同时成立于 raw response、final report 与 payload-derived writeback 三层，而不是只停留在 schema-valid 顶层 JSON。
3. 当前 `LLMWorker Live Payload Contract Hardening` 至少已在一条受控 real-model path 上得到正向验证。
4. 因此，`LLMWorker` real-worker payload path 当前可以继续作为 **受控 dogfood 路径** 被观察和积累证据。

## 当前不能安全表述的判断

当前仍不能安全说：

1. real-worker payload path 已成为默认稳定面。
2. `LLMWorker` real-worker payload path 已经具有普遍可重复性。
3. 一次成功已经足以替代更高层的 adoption / stability judgement。
4. 本次 `LLMWorker` 成功可以外推到 `HTTPWorker` 或其他 real-worker 路径。

## 最小额外证据门

若后续想把当前 wording 从“已有 1 条正向 live signal”扩大到“受控 real-worker payload path 具有可重复 dogfood 能力”，最小额外证据门应为：

1. 在 **不新增 runtime code、schema 或 worker 语义变更** 的前提下，再执行 **1 条独立的受控 live rerun**。
2. 新 rerun 继续保持窄 `allowed_artifacts` 边界，不扩大为开放式 dogfood。
3. 新 rerun 仍需同时满足三层证据：
   - raw response 返回合法 payload
   - final report 保持 schema-valid，且不依赖 guard-rejection 降级来掩盖 drift
   - payload-derived writeback 真实命中允许边界内目标文件
4. 若追加 rerun 未满足上述三层证据，应先把差异归档为新 dogfood signal，而不是扩大 adoption wording。

## 对 `docs/first-stable-release-boundary.md` 的解释

本轮 judgment **不会**改变 `docs/first-stable-release-boundary.md` 对 real worker adapters 的大边界：

1. real worker adapters 仍不属于默认稳定面。
2. 当前新增的只是一个更窄的中间口径：
   - `LLMWorker` payload path 已有 1 条正向 live signal
   - 但仍只适合受控 dogfood，不适合直接升级为默认稳定依赖

## 本轮观察到的可抽象流程

在 adoption judgment 的 1、2 两步里，当前已经能看到 3 类值得后续抽象固化的流程：

1. **证据收集 bundle**
   - preflight
   - raw response
   - final report
   - writeback outcome

2. **dogfood 问题分类**
   - transport / credential / endpoint 问题
   - contract drift / schema drift
   - output guard rejection
   - writeback boundary failure

3. **反馈整合面**
   - 将单次 dogfood 证据、已知问题与下一方向候选绑定到同一文档闭环中

这些都已足以证明：后续把 dogfood 的证据收集、问题收集、反馈整合收口成一个组件或 skill，是合理 backlog，而不是空泛愿望。

## Backlog 决定

因此，本轮把以下需求继续保留在 backlog，而不立即实现：

1. dogfood 证据收集组件或 skill
2. dogfood 问题收集组件或 skill
3. dogfood 问题反馈整合组件或 skill

当前判断：

1. 这是合理的后续方向。
2. 但优先级仍低于先满足上文定义的“最小额外证据门”。

## 结论

本轮 adoption judgment 已经把当前边界说清楚：

1. 当前可以安全说“受控 real-worker payload path 已获得 1 条正向 live signal”。
2. 当前不能安全说“real-worker payload path 已成为默认稳定面”。
3. 若要扩大 wording，最小额外证据门是再拿到 1 条在无新 runtime 改动前提下的独立受控 live success。
4. dogfood evidence / issue / feedback integration 已被确认是合理 backlog，但不应抢在最小额外证据门之前进入实现。