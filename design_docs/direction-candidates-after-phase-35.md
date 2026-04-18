# Direction Candidates — After Phase 35

## 2026-04-16 增量更新 — After Controlled Real-Worker Payload Evidence Accumulation

最近又完成了一条直接承接 `Real-Worker Payload Adoption Judgment` 的窄切片：

- `Controlled Real-Worker Payload Evidence Accumulation`

这意味着平台现在已经同时具备：

1. `LLMWorker` 受控 payload path 的第 2 条独立正向 live signal。
2. raw response、final report 与 payload-derived writeback 三层同时再次成立。
3. 一个已经可以写进权威边界文档的更强口径：`受控 real-worker payload path 已具备最小可重复 dogfood 能力`。

因此，当前主线已经不再是“还要不要继续满足最小额外证据门”，而是“在最小可重复性已经成立后，下一条最值得投入的窄切片是什么”。

### 新候选 A. dogfood evidence / issue / feedback integration direction only

- 做什么：把 dogfood 证据收集、问题收集、反馈整合这条已经重复出现的人工流程，收口成单独方向分析，为后续组件或 skill 切片做准备；本轮先只做方向与边界，不直接实现。
- 依据：
  - [design_docs/dogfood-evidence-issue-feedback-integration-direction-analysis.md](design_docs/dogfood-evidence-issue-feedback-integration-direction-analysis.md)
  - [design_docs/dogfood-evidence-issue-feedback-boundary.md](design_docs/dogfood-evidence-issue-feedback-boundary.md)
  - [design_docs/dogfood-issue-promotion-feedback-packet-contract-direction-analysis.md](design_docs/dogfood-issue-promotion-feedback-packet-contract-direction-analysis.md)
  - [review/real-worker-payload-adoption-judgment-2026-04-16.md](design_docs/../review/real-worker-payload-adoption-judgment-2026-04-16.md)
  - [review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md](design_docs/../review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md)
  - [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md)
- 风险：低。
- 当前判断：**已完成**。candidate A 的全链路已落地：boundary consolidation → issue-promotion / feedback-packet contract（T1-T4 / S1-S3 / 12 字段 / 9+3 字段 / 6×矩阵）→ dry-run 验证 → interface draft（5 结构 + 4 签名）→ `src/dogfood/` 实现（models / evaluator / builder / dispatcher）→ 18 项新测试全部通过 → 全量基线 964 passed, 2 skipped。产出文档：
  - [design_docs/dogfood-promotion-packet-interface-draft.md](design_docs/dogfood-promotion-packet-interface-draft.md)
  - [review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md](review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md)
  - [review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md](review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md)
  - [design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md](design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md)（DONE）
  - [design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md](design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md)（DONE）

### 新候选 B. HTTPWorker failure fallback schema alignment

- 做什么：把 `HTTPWorker` 的本地 error fallback 拉回当前 `Subagent Report` schema，但不改远端成功态透传边界。
- 依据：
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md](design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：低。
- 当前判断：仍值得做，但默认优先级低于候选 A。

### 新候选 C. broader real-worker repeatability evidence

- 做什么：继续收集更多独立受控 live signals，用来判断是否能从“最小可重复 dogfood 能力”继续扩大到更宽泛的 repeatability wording。
- 依据：
  - [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md)
  - [review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md](design_docs/../review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：中。
- 当前判断：现在还不该默认继续做，因为最小可重复性已经成立，再追加 live rerun 的信息增益已经低于把 dogfood 流程本身抽象出来。

## 2026-04-16 当前 AI 倾向判断（After Controlled Real-Worker Payload Evidence Accumulation）

我当前倾向于直接进入 **新候选 A**。原因是：最小可重复性这条最窄证据门已经被满足，继续追打更多同类 live rerun 的边际收益开始下降；反而是 dogfood 证据/问题/反馈链路已经连续暴露为可抽象流程，更适合作为下一条窄切片候选。

## 2026-04-16 增量更新 — After Real-Worker Payload Adoption Judgment

最近又完成了一条直接承接 `Live Payload Rerun Verification` 的窄切片：

- `Real-Worker Payload Adoption Judgment`

这意味着平台现在已经同时具备：

1. 对当前 `LLMWorker` real-worker payload path 的明确 adoption wording，而不再只停留在“感觉上应该谨慎”。
2. 一条被显式写出的最小额外证据门：若想扩大 wording，需要再拿到 1 条在无新 runtime 改动前提下的独立受控 live success。
3. 对 dogfood 证据收集 / 问题收集 / 反馈整合的抽象需求的明确 backlog 记录。

因此，当前主线已经不再是“继续讨论这次成功算不算稳定”，而是“是否去满足那条最小额外证据门”。

### 新候选 A. controlled real-worker payload evidence accumulation

- 做什么：在无新 runtime code、schema 或 worker 语义变更的前提下，再执行 1 条独立受控 live rerun，用来验证当前正向 signal 是否可重复。
- 依据：
  - [design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md](design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md)
  - [review/real-worker-payload-adoption-judgment-2026-04-16.md](review/real-worker-payload-adoption-judgment-2026-04-16.md)
  - [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md)
- 风险：低到中。
- 当前判断：**推荐**。因为 adoption wording 已经够清楚，当前最有价值的新信息变成了“这条正向 signal 是否还能在无新改动前提下再出现一次”。当前已进一步收口为 planning-gate 草案：`design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`。

### 新候选 B. HTTPWorker failure fallback schema alignment

- 做什么：把 `HTTPWorker` 的本地 error fallback 拉回当前 `Subagent Report` schema，但不改远端成功态透传边界。
- 依据：
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md](design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：低。
- 当前判断：仍值得做，但默认优先级低于候选 A。

### 新候选 C. dogfood evidence / issue / feedback integration direction only

- 做什么：暂不实现组件或 skill，只把 dogfood 证据收集、问题收集、反馈整合的抽象边界整理成单独方向，为后续 backlog 转 gate 做准备。
- 依据：
  - [review/real-worker-payload-adoption-judgment-2026-04-16.md](review/real-worker-payload-adoption-judgment-2026-04-16.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [review/research-compass.md](review/research-compass.md)
- 风险：低。
- 当前判断：已被证明有价值，但默认仍低于候选 A，因为当前最关键的不确定性仍是证据门是否可满足。

## 2026-04-16 当前 AI 倾向判断（After Real-Worker Payload Adoption Judgment）

我当前倾向于直接进入 **新候选 A**。原因是：当前口径边界已经够清楚，继续写 judgment 文档的收益已经下降；最值得追加的新信息是“这条正向 signal 是否能在无新 runtime 改动的前提下再复现一次”。

## 2026-04-16 增量更新 — After Live Payload Rerun Verification

最近又完成了一条直接承接 `LLMWorker Live Payload Contract Hardening` 的窄切片：

- `Live Payload Rerun Verification`

这意味着平台现在已经同时具备：

1. 一条受控 live `LLMWorker` real-model rerun 的正向 runtime signal，而不再只有 schema-valid report baseline。
2. raw response、最终 report 与 payload-derived writeback 三层都能在同一次受控执行里成立。
3. 对当前 hardening 的最重要验证已经拿到，但也同时暴露出新的边界问题：这次成功到底应如何被解释，而不是是否还要继续修同一段实现。

因此，当前主线已经不再是“继续写 live payload hardening”，而是“如何在不扩大稳定面承诺的前提下解释这次成功”。

### 新候选 A. 受控 real-worker payload adoption judgment

- 做什么：围绕这次 live success 起一条更高层的 adoption / dogfood judgment 切片，明确当前 preview 口径下，一次成功 real-worker payload rerun 到底意味着什么、不意味着什么。
- 依据：
  - [design_docs/live-payload-rerun-followup-direction-analysis.md](design_docs/live-payload-rerun-followup-direction-analysis.md)
  - [review/live-payload-rerun-verification-2026-04-16.md](review/live-payload-rerun-verification-2026-04-16.md)
  - [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md)
- 风险：低到中。
- 当前判断：**推荐**。因为当前最缺的不是新代码，而是对这次正向 real signal 的边界化解释。当前已进一步收口为 planning-gate 草案：`design_docs/stages/planning-gate/2026-04-16-real-worker-payload-adoption-judgment.md`。

### 新候选 B. HTTPWorker failure fallback schema alignment

- 做什么：把 `HTTPWorker` 的本地 error fallback 拉回当前 `Subagent Report` schema，但不改远端成功态透传边界。
- 依据：
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/live-payload-rerun-followup-direction-analysis.md](design_docs/live-payload-rerun-followup-direction-analysis.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：低。
- 当前判断：仍值得做，但默认优先级低于候选 A。

### 新候选 C. 只做 adoption/backlog 记录，不进入新实现

- 做什么：暂不进入新的实现或验证切片，只把本次 live success 对 dogfood 口径与 backlog 优先级的影响写清楚。
- 依据：
  - [design_docs/live-payload-rerun-followup-direction-analysis.md](design_docs/live-payload-rerun-followup-direction-analysis.md)
  - [review/live-payload-rerun-verification-2026-04-16.md](review/live-payload-rerun-verification-2026-04-16.md)
  - [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md)
- 风险：低。
- 当前判断：只在你希望先压缩文档口径时采用；默认优先级低于候选 A/B。

## 2026-04-16 当前 AI 倾向判断（After Live Payload Rerun Verification）

我当前倾向于直接进入 **新候选 A**。原因是：这次 live success 已经足以暂时停止继续写 `LLMWorker` hardening 代码，但还不足以直接上升成默认稳定面承诺；此时最自然的下一步是先把 adoption 边界说清楚。

## 2026-04-16 增量更新 — After LLMWorker Live Payload Contract Hardening

最近又完成了一条直接承接 `After Payload + Handoff Footprint Controlled Dogfood` 候选 A 的窄切片：

- `LLMWorker Live Payload Contract Hardening`

这意味着平台现在已经同时具备：

1. 更硬的 live prompt contract：显式列出允许的 `operation` / `content_type` 枚举，并加入 `upsert`、`text/markdown` 等禁止示例。
2. 极窄的 `content_type` alias normalization：`text/markdown -> markdown`、`text/plain -> text`、`application/json -> json`。
3. 更准确的 report status 语义：若 LLM 主动尝试 payload 但所有 candidate 被 output guard 拒绝，则 `completed` 会下调为 `partial`。
4. 新的验证基线：targeted regression `55 passed, 1 skipped`，全量回归 `946 passed, 2 skipped`。

因此，当前主线已经不再是“继续做 hardening 实现”，而是“用一轮更小的 live rerun 验证刚落地的 contract hardening 是否真正改善真实模型 payload 命中率”。

### 新候选 A. live payload rerun verification

- 做什么：在不继续改实现的前提下，复跑一条 live `LLMWorker` real-model path，验证新的 prompt + normalization + status policy 会落到哪种真实结果：成功触发 artifact writeback，还是更清晰地回落为 `partial`。
- 依据：
  - [design_docs/live-payload-rerun-verification-direction-analysis.md](design_docs/live-payload-rerun-verification-direction-analysis.md)
  - [design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md](design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md)
  - [design_docs/llm-live-payload-contract-hardening-direction-analysis.md](design_docs/llm-live-payload-contract-hardening-direction-analysis.md)
  - [review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md](review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md)
- 风险：低到中。
- 当前判断：**推荐**。因为实现面已经收口，最有价值的新信息变成了“真实模型在新 contract 下会如何表现”。当前已进一步收口为 planning-gate 草案：`design_docs/stages/planning-gate/2026-04-16-live-payload-rerun-verification.md`。

### 新候选 B. HTTPWorker failure fallback schema alignment

- 做什么：把 `HTTPWorker` 的本地 error fallback 拉回当前 `Subagent Report` schema，但不改远端成功态透传边界。
- 依据：
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md](design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：低。
- 当前判断：仍值得做，但默认优先级低于候选 A。

### 新候选 C. driver / adapter backlog-recording only

- 做什么：继续压缩低优先级 driver / adapter / 转接层边界为文档切片，不进入新的 real-worker 实现。
- 依据：
  - [docs/driver-responsibilities.md](docs/driver-responsibilities.md)
  - [docs/plugin-model.md](docs/plugin-model.md)
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md) §Driver / Adapter / 转接层 Backlog
- 风险：低。
- 当前判断：只在你希望暂停 real-worker follow-up 时采用；默认优先级低于候选 A/B。

## 2026-04-16 当前 AI 倾向判断（After LLMWorker Live Payload Contract Hardening）

我当前倾向于直接进入 **新候选 A**。原因是：当前实现面已经够窄、够完整，再继续推实现只会增加猜测；而 live rerun 会立刻告诉我们这轮 hardening 对真实 payload writeback 命中率到底有没有帮助。

## 2026-04-16 增量更新 — After Payload + Handoff Footprint Controlled Dogfood

最近又完成了一条直接承接 `After LLMWorker Structured Payload Producer Alignment` 候选 A 的窄切片：

- `Payload + Handoff Footprint Controlled Dogfood`

这意味着平台现在已经同时具备：

1. `StubWorker` baseline payload path 的真实 runtime 证明，而不是只停留在测试里。
2. latest canonical handoff footprint 与 checkpoint 的恢复入口一致性证明。
3. 一条 live DashScope `LLMWorker` runtime signal：真实模型可以返回 schema-valid `completed` report，但 payload candidate 仍可能漂移到 schema 不接受的枚举值。

因此，继续泛化 dogfood 的收益已经开始下降。当前最有价值的新增信息不是“还要不要继续观察”，而是“live producer 语义现在具体卡在哪个窄边界上”。这使得下一方向比前一轮更明确：应优先修 real-worker contract consistency，而不是继续做宽泛 dogfood。

### 新候选 A. LLMWorker live payload contract hardening

- 做什么：针对 live model 常见的近似枚举值漂移，收紧 prompt 合同，并评估是否在保守前提下引入更窄的 normalization（例如只接受有限同义值映射），目标是让 live `artifact_payloads` 更稳定落入当前 schema 允许集合。
- 依据：
  - [review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md](review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md)
  - [design_docs/llm-live-payload-contract-hardening-direction-analysis.md](design_docs/llm-live-payload-contract-hardening-direction-analysis.md)
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md](design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md)
- 风险：中。
- 当前判断：**推荐**。因为真实 signal 已经指出了具体缺口，继续 dogfood 的边际收益低于修这个窄边界。

### 新候选 B. HTTPWorker failure fallback schema alignment

- 做什么：把 `HTTPWorker` 的本地 error fallback 拉回当前 `Subagent Report` schema，但不改远端成功态透传边界。
- 依据：
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md](review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：低。
- 当前判断：仍值得做，但默认优先级低于候选 A。

### 新候选 C. driver / adapter backlog-recording only

- 做什么：继续压缩低优先级 driver / adapter / 转接层边界为文档切片，不进入新的 real-worker 实现。
- 依据：
  - [docs/driver-responsibilities.md](docs/driver-responsibilities.md)
  - [docs/plugin-model.md](docs/plugin-model.md)
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md) §Driver / Adapter / 转接层 Backlog
- 风险：低。
- 当前判断：只在你希望暂时停止 real-worker follow-up 时采用；默认优先级低于候选 A/B。

## 2026-04-16 当前 AI 倾向判断（After Payload + Handoff Footprint Controlled Dogfood）

我当前倾向于直接进入 **新候选 A**。原因是：dogfood 已经完成它最有价值的职责，即把“真实问题到底在哪里”暴露出来。现在再继续观察，不会比直接修复 live payload contract consistency 更有信息增益。

## 2026-04-16 增量更新 — After LLMWorker Structured Payload Producer Alignment

最近又完成了一条直接承接 After P4 候选 A 的窄切片：

- `LLMWorker Structured Payload Producer Alignment`

这意味着平台现在已经同时具备：

1. `LLMWorker` 的 schema-valid `Subagent Report` baseline，而不再依赖额外顶层字段 `llm_response`。
2. 一条受控的真实模型 producer 路径：`LLMWorker` 在 JSON response contract 下可选地产出最多 1 个 `artifact_payloads` candidate。
3. 非结构化模型响应的保守 fallback：返回 schema-valid `partial` report，而不是 invalid report。
4. 一条 mocked delegation -> `LLMWorker` -> payload-derived writeback 闭环。

因此，producer-side 主线已经不再停留在 StubWorker 或 HTTP 透传证明可用的状态。继续马上沿 producer 方向硬扩多 payload、宽 dogfood 或更复杂 prompt/template，会明显快于当前信号积累速度；相比之下，当前更自然的下一方向重新回到受控 dogfood 与 real-worker consistency follow-up 的取舍。

### 新候选 A. payload + handoff footprint controlled dogfood

- 做什么：先不继续扩实现面，而是用当前 Stub + LLMWorker payload path 与 latest handoff footprint 做一轮受控 dogfood，观察真实 signal，再决定是否继续扩 producer 语义或补 real-worker follow-up。
- 依据：
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md](design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md)
- 风险：低到中。
- 当前判断：**推荐**。真实模型路径的最小 producer 已经成立，此时先观察 signal，比继续马上宽扩 prompt / payload 语义更稳。

### 新候选 B. HTTPWorker report fallback schema alignment

- 做什么：把 `HTTPWorker` 的本地 error fallback 对齐到当前 `Subagent Report` schema，只处理失败态一致性，不改远端成功态透传边界。
- 依据：
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md](design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：低。
- 当前判断：值得做，但默认优先级低于候选 A，因为当前暴露的是 real-worker 失败态一致性缺口，而不是 producer 主线仍未打通。

### 新候选 C. driver / adapter backlog-recording only

- 做什么：不立刻进入新实现，而是把 `driver / adapter / 转接层` 的剩余低优先级边界再压缩成一条更窄的 backlog-recording 文档切片。
- 依据：
  - [docs/driver-responsibilities.md](docs/driver-responsibilities.md)
  - [docs/plugin-model.md](docs/plugin-model.md)
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md) §Driver / Adapter / 转接层 Backlog
- 风险：低。
- 当前判断：只在你希望先继续文档收口、暂不进入新的验证或实现切片时才值得做；默认优先级低于候选 A/B。

## 2026-04-16 当前 AI 倾向判断（After LLMWorker Structured Payload Producer Alignment）

我当前倾向于直接进入 **新候选 A**。原因是：真实模型路径的最小 first-party producer 已经打通，下一步最有价值的不再是继续追加语义复杂度，而是先看当前 payload path 与 latest handoff footprint 在受控 dogfood 下能产生什么真实 signal。若现在继续硬扩实现，更容易把多 payload、prompt 细化、更多 real-worker 边界一次性卷回来。

## 2026-04-15 增量更新 — After P4

最近又完成了一条直接承接 A1 后续方向的窄切片：

- `Handoff Authority-Doc Footprint (P4)`

这意味着平台现在已经同时具备：

1. 从 `.codex/handoffs/CURRENT.md` 统一提取 latest canonical handoff pointer 的共享 helper。
2. `checkpoint` 的 dedicated `Current Handoff` 结构段，以及稳定的读写/校验路径。
3. `safe_stop_writeback` / `writeback_notify()` 返回的 `current_handoff_footprint` contract。
4. Checklist / Phase Map 上与当前 safe stop 对齐的 compact handoff footprint，而不是只在 `.codex/handoffs/` 内部留下痕迹。

因此，P4 关注的 Gap E 已经从“handoff 存在，但 authority-doc footprint 不清晰”转为“latest canonical handoff 已有统一 pointer contract”。继续沿审计方向硬扩，会很快跨入 history ledger、额外 event type 或更宽的 tracing redesign；这些都不再适合作为默认下一步。相比之下，当前更自然的下一方向重新回到了 producer-side 主线与受控 dogfood 取舍。

### 新候选 A. LLMWorker structured payload producer alignment

- 做什么：让 `LLMWorker` 在受控 prompt / response contract 下产出 `artifact_payloads`，把当前已经由 StubWorker 打通的 first-party producer 路径扩展到真实模型输出。
- 依据：
  - [design_docs/subagent-research-synthesis.md](design_docs/subagent-research-synthesis.md)
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md](design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md)
- 风险：中高。会把 prompt 设计、结构化解析、模型稳定性与 payload 边界一起拉进当前主线。
- 当前判断：**推荐**。A1 已完成最小 first-party producer，P4 又补齐了 safe-stop/handoff footprint；现在最自然的下一条实现主线就是把 producer 从 Stub 扩到真实模型路径。

### 新候选 B. payload + handoff footprint controlled dogfood only

- 做什么：先不继续扩实现，只用当前的 StubWorker payload path 与 latest handoff footprint 合同做受控 dogfood，观察真实 signal，再决定是否进入 LLM producer。
- 依据：
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/stages/planning-gate/2026-04-15-p4-handoff-authority-doc-footprint.md](design_docs/stages/planning-gate/2026-04-15-p4-handoff-authority-doc-footprint.md)
- 风险：低。
- 当前判断：这是保守 fallback；适合在你想先观察真实使用信号，而不是继续扩代码面时采用。

### 新候选 C. driver / adapter backlog-recording only

- 做什么：不立刻进入新实现，而是把 `driver / adapter / 转接层` 的剩余低优先级边界再压缩成一条更窄的 backlog-recording 文档切片。
- 依据：
  - [docs/driver-responsibilities.md](docs/driver-responsibilities.md)
  - [docs/plugin-model.md](docs/plugin-model.md)
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md) §Driver / Adapter / 转接层 Backlog
- 风险：低。
- 当前判断：只在你希望先继续文档收口、暂不进入新的实现切片时才值得做；默认优先级低于候选 A/B。

## 2026-04-15 当前 AI 倾向判断（After P4）

我当前倾向于直接进入 **新候选 A**。原因是：A1 已经补齐了最小 first-party producer，P4 又补齐了 safe-stop/handoff authority footprint；两条收口后，producer 主线里唯一仍明显缺位的就是 `LLMWorker` 的结构化 payload 产出。若现在继续沿审计方向扩，只会把范围拉向 ledger 或更宽的 tracing redesign，收益明显低于把真实模型路径补齐。

## 2026-04-15 增量更新 — After A1

最近又完成了与 P3 主线直接相连的一条窄切片：

- `StubWorker Payload Producer Alignment (A1)`

这意味着平台现在已经同时具备：

1. `WritebackEngine.plan()` 对 `report.artifact_payloads` 的真实消费链。
2. 一条默认 first-party producer 路径：`StubWorkerBackend` 会在受控条件下产出 1 个 payload candidate。
3. 与 runtime 能力一致的官方示例 report，以及实例包内的 schema 校验覆盖。

因此，P3 主线已经不再停留在“只有测试与远端 HTTP 透传证明可用”的状态。继续沿 producer 方向往下扩到 `LLMWorker`，会立刻把 prompt 设计、结构化解析和模型稳定性带进来；这比刚完成的 A1 明显更宽。相比之下，之前被延后的 P4 审计主线现在重新具备了更合理的进入时机。

### 新候选 A. 转入 P4：Handoff 审计痕迹 / authority-doc footprint

- 做什么：处理 handoff、checkpoint 与 authority docs 之间的 trace footprint，让 safe-stop 与长期权威文档之间留下更明确、可回溯的审计面。
- 依据：
  - [design_docs/subagent-research-synthesis.md](design_docs/subagent-research-synthesis.md)
  - [design_docs/subagent-tracing-writeback-direction-analysis.md](design_docs/subagent-tracing-writeback-direction-analysis.md)
  - [design_docs/tooling/Session Handoff Standard.md](design_docs/tooling/Session Handoff Standard.md)
- 风险：中。会重新触碰 safe-stop bundle、checkpoint 与 authority docs 的同步边界。
- 当前判断：**推荐**。P3 的 consumer + minimal producer 闭环已经成立，此时回到 P4 审计主线，比继续立刻扩 LLM producer 更稳。

### 新候选 B. LLMWorker structured payload producer alignment

- 做什么：让 `LLMWorker` 开始在受控 prompt / response contract 下产出 `artifact_payloads`，把 first-party producer 从 stub 扩到真实模型调用路径。
- 依据：
  - [design_docs/subagent-research-synthesis.md](design_docs/subagent-research-synthesis.md)
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md](design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md)
- 风险：中高。会直接把结构化解析、prompt 约束与模型稳定性卷入当前主线。
- 当前判断：值得做，但应晚于 P4 或至少晚于一轮受控 dogfood。

### 新候选 C. payload path controlled dogfood only

- 做什么：先不扩实现面，继续用 StubWorker 的最小 producer 路径做受控 dogfood，收集真实 signal，再决定是否扩到 LLM producer 或回到 P4。
- 依据：
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md](design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md)
- 风险：低。
- 当前判断：这是保守 fallback；适合在你想先观察真实使用信号时采用。

## 2026-04-15 当前 AI 倾向判断（After A1）

我当前倾向于直接进入 **新候选 A**。因为 A1 已经把最小 first-party producer 补齐，继续往 producer 方向扩会立刻跨进 LLM 结构化输出问题；而 P4 审计痕迹此前之所以优先级落后，主要是因为 P3 主线还没闭环。现在这个前提已经消失了。

## 2026-04-15 增量更新 — After true P3

最近连续完成了 4 条与子 agent 主线直接相关的窄切片：

- `Handoff Recovery Hardening`
- `Handoff Validator 独立化（P2)`
- `Subagent Report richer writeback payload（P3-prep)`
- `artifact_payloads -> WritebackPlan Mapping（P3)`

这意味着 P3 的“消费端”已经真正落地：`WritebackEngine.plan()` 现在会在 `review_state=applied` 时消费 `report.artifact_payloads`，并把合法 payload 转成真实 `WritebackPlan`。但当前 first-party 产出端仍然偏弱：默认 Stub / LLM / example 路径还没有把 `artifact_payloads` 作为常态产出面，P3 的新管道目前主要由定向测试与远端 HTTP payload 透传覆盖。

因此，当前最合理的下一方向不再是继续补消费者，而是决定要不要先把**产出端对齐**补成最小闭环，或者转去做更偏审计面的 P4。

### 新候选 A. Payload-producing worker / example alignment

- 做什么：为至少一条 first-party 路径补齐 `artifact_payloads` 产出能力，例如 StubWorker、LLM prompt/template 或官方 example，让平台自带路径能真实打通 `contract -> report.artifact_payloads -> WritebackPlan -> writeback` 闭环。
- 依据：
  - [design_docs/subagent-research-synthesis.md](design_docs/subagent-research-synthesis.md)
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/stages/planning-gate/2026-04-15-artifact-payload-writeback-plan-mapping.md](design_docs/stages/planning-gate/2026-04-15-artifact-payload-writeback-plan-mapping.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md) 的持续 dogfood 主线
- 风险：中。需要控制产出 payload 的可信度、边界与 example 语义，不应把 directive 级复杂度顺手带进来。
- 当前判断：**推荐**。P3 已把消费链打通，如果 first-party 产出端不跟上，这条新管道会长期停留在“测试已覆盖、默认路径未使用”的状态。

### 新候选 B. 转入 P4：Handoff 审计痕迹 / authority-doc footprint

- 做什么：处理 handoff 与长期权威文档之间的审计留痕问题，让 handoff / checkpoint / authority docs 之间留下更明确的 trace footprint。
- 依据：
  - [design_docs/subagent-research-synthesis.md](design_docs/subagent-research-synthesis.md) §P4
  - [design_docs/subagent-tracing-writeback-direction-analysis.md](design_docs/subagent-tracing-writeback-direction-analysis.md) Gap E
  - [design_docs/tooling/Session Handoff Standard.md](design_docs/tooling/Session Handoff Standard.md)
- 风险：中。会重新触碰 safe-stop bundle、checkpoint 与 authority docs 的同步语义，范围比“只补产出端”更分散。
- 当前判断：值得做，但优先级低于候选 A。因为 P3 的直接后续价值仍然取决于是否有 first-party producer 真正使用它。

### 新候选 C. payload path controlled dogfood only

- 做什么：先不新增实现，只在当前实现上继续做受控 dogfood，观察 `artifact_payloads` 写回路径是否出现真实 regression / gap signal，再决定是否起新 gate。
- 依据：
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md) 的持续 dogfood 待办
  - [review/research-compass.md](review/research-compass.md) 当前研究空白已基本关闭，适合回到信号驱动模式
  - 最近几个切片中暴露出的现实问题都来自实际使用而非纸面分析
- 风险：低。
- 当前判断：这是保守 fallback。如果你想先压低实现风险，它是合理选项；但它也会把 true P3 继续留在“已可用但默认路径未充分消费”的状态。

## 2026-04-15 当前 AI 倾向判断（After true P3）

我当前倾向于直接进入 **新候选 A**。原因很简单：P3 已经把消费链和安全边界收口完成，但默认 first-party 产出链还没跟上；这会让刚完成的 writeback path 主要停留在测试与远端透传场景里。相比之下，直接跳去做 P4 审计增强，短期内对 P3 主线的闭环价值反而更低。

## 2026-04-15 增量更新 — After P3-prep

最近连续完成了 3 条与子 agent 主线直接相关的窄切片：

- `Handoff Recovery Hardening`
- `Handoff Validator 独立化（P2)`
- `Subagent Report richer writeback payload（P3-prep)`

这意味着此前阻塞真正 P3 的 contract 缺口已经被补上：`Subagent Report` 现在已有可选 `artifact_payloads`，可以安全表达 `path` / `content` / `operation` / `content_type`，不再只能靠 `changed_artifacts` 做模糊描述。

因此，当前最合理的下一方向不再是继续补 report schema，而是回到 [design_docs/subagent-research-synthesis.md](design_docs/subagent-research-synthesis.md) 中的 **P3 / P4** 分叉，并以新落地的 payload contract 作为前提。

### 新候选 A. 真正进入 P3：`artifact_payloads` → `WritebackPlan` 自动映射

- 做什么：让 `Executor` / `WritebackEngine` 开始消费 report 中的 `artifact_payloads`，把它们转换成真实 `WritebackPlan`，但第一版仍只允许 `create` / `update` / `append`，且不引入 directive 级操作。
- 依据：
  - [design_docs/subagent-research-synthesis.md](design_docs/subagent-research-synthesis.md) §P3
  - [design_docs/subagent-tracing-writeback-direction-analysis.md](design_docs/subagent-tracing-writeback-direction-analysis.md) Gap B
  - [design_docs/stages/planning-gate/2026-04-15-subagent-report-writeback-payload.md](design_docs/stages/planning-gate/2026-04-15-subagent-report-writeback-payload.md)
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
- 风险：中。需要在自动映射前补清楚 path 归一化、`allowed_artifacts` 边界和 writeback-safe 限制。
- 当前判断：**推荐**。这是用户已明确选择过的主线，且刚完成的 P3-prep 就是为它解锁前置 contract。

### 新候选 B. 转入 P4：Handoff 审计痕迹 / authority-doc footprint

- 做什么：处理 handoff 在权威文档与长期追踪面上的留痕问题，把 handoff 发生与相关 trace 进一步纳入长期可回溯状态面。
- 依据：
  - [design_docs/subagent-research-synthesis.md](design_docs/subagent-research-synthesis.md) §P4
  - [design_docs/subagent-tracing-writeback-direction-analysis.md](design_docs/subagent-tracing-writeback-direction-analysis.md) Gap E
  - [design_docs/tooling/Session Handoff Standard.md](design_docs/tooling/Session Handoff Standard.md)
- 风险：中。会重新触碰 handoff / checkpoint / 状态面同步，范围比当前 P3 主线更分散。
- 当前判断：可做，但优先级低于 P3。因为 P3 现在已经具备明确前置，而 P4 仍偏向审计增强。

### 新候选 C. 先做 payload dogfood / worker 产出对齐小切片

- 做什么：不立即消费 payload，而是先让更多 worker / example / template 能稳定产出 `artifact_payloads`，再观察真实 dogfood 信号。
- 依据：
  - [docs/subagent-schemas.md](docs/subagent-schemas.md)
  - [design_docs/stages/planning-gate/2026-04-15-subagent-report-writeback-payload.md](design_docs/stages/planning-gate/2026-04-15-subagent-report-writeback-payload.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md) 的持续 dogfood 主线
- 风险：低。
- 当前判断：这是保守选项，但会延后真正的 P3 收口；只有在你想先压低消费路径风险时才值得选。

## 2026-04-15 当前 AI 倾向判断

我当前倾向于直接进入 **新候选 A**，原因很简单：用户已经明确拒绝过 manifest-only 的保守替代路线，并批准了 richer payload 前置切片；现在这个前置已完成，再绕去做新的保守小步，收益会明显低于继续收口真正的 P3。

## 背景

Phase 35 已完成。原 `v1.0.0` 已降级为 preview 定位，当前最新可分发版本为 `v0.9.3`。

在此之后，本仓库又完成了多项 post-v1.0 的窄 scope 标准化工作：

- 形成了 [design_docs/tooling/Dual-Package Distribution Standard.md](design_docs/tooling/Dual-Package Distribution Standard.md)
- 固定了平台 runtime 包与官方实例包的职责边界
- 固定了安装态 MCP 接入原则、最小兼容原则与最小验证门
- 最新又完成了状态面一致性收口：Checklist / Phase Map / CURRENT / checkpoint 已统一到 `v0.9.3` preview 口径，仓库已回到无 active planning-gate 的 safe stop

这意味着下一步不应重新发散讨论“大方向”，而应从权威文档与当前实现缺口中选择一个可执行的窄切片。

## 来源

- [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md) 中的 post-v1.0 待办与当前活跃风险
- [design_docs/tooling/Dual-Package Distribution Standard.md](design_docs/tooling/Dual-Package Distribution Standard.md) 中已固定、但尚未落地的安装分发标准
- [docs/project-adoption.md](docs/project-adoption.md) 与 [docs/pack-manifest.md](docs/pack-manifest.md) 中尚未固定的安装/分发/兼容空白
- [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md) 中仍保留为后续方向的 N5 / checks 贯通议题
- [review/research-compass.md](review/research-compass.md) 中关于版本化 pack manifest 与 distribution 路径的研究空白
- 当前实现现实：官方实例脚本已可作为 adoption 工具存在，但还没有安装态入口、打包元数据与统一 validator/check 消费协议

## 候选方向

### A. 双发行包实现切片

- 做什么：把“双发行包标准”落成最小可安装实现，至少补齐 runtime 包与官方实例包的打包元数据、入口归属、package data 装载和最小 smoke 验证。
- 依据：
  - [design_docs/tooling/Dual-Package Distribution Standard.md](design_docs/tooling/Dual-Package Distribution Standard.md)
  - [docs/project-adoption.md](docs/project-adoption.md) 当前仍未固定安装器协议
  - [docs/pack-manifest.md](docs/pack-manifest.md) 当前仍未固定安装与发布流程
- 前置：双发行包标准已完成，可直接进入窄 scope planning-gate。
- 风险：中。会同时触及 Python packaging、入口暴露、package data 与安装后 smoke 验证。
- 当前状态：已完成。双包 wheel 构建通过、干净 venv 安装验证通过（runtime CLI + 实例 CLI + 资产可发现性全部正常）；原 `v1.0.0` 产物后续已降级为 preview 口径，当前最新产物为 `release/doc-based-coding-v0.9.3.zip`。残留 CI/CD 自动化属于运维层，暂缓至发布目标确定后。

### B. 官方实例 validator/check 契约收口切片

- 做什么：把官方实例包中的 `validators` / `checks` / `scripts` 三类能力收口成稳定可消费契约，明确哪些脚本要暴露 `validate(data) -> dict` 一类的 registry 调用面，哪些保留为独立命令。
- 依据：
  - [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md) 中 N5（Script-style validator 语义升级）与 checks 字段直连的遗留议题
  - [docs/pack-manifest.md](docs/pack-manifest.md) 中 `validators` / `checks` / `scripts` 的能力声明边界
  - 当前运行时现实：`get_pack_info` 仍将两个官方实例校验脚本列为 skipped validator
- 前置：不依赖完整打包实现，可先做协议与消费面收口。
- 风险：中。若定义过重，会把本应独立的 adoption 命令错误塞进 runtime validator 语义。
- 当前状态：已完成。官方实例 self-check 脚本已从 `validators` 边界中收回到 `scripts`。

### C. 兼容元数据与版本声明切片

- 做什么：把 runtime 包与官方实例包之间的兼容关系变成机器可读的声明面，明确“包管理层约束”和“pack 语义层约束”分别放在哪里。
- 依据：
  - [design_docs/tooling/Dual-Package Distribution Standard.md](design_docs/tooling/Dual-Package Distribution Standard.md) 已固定兼容声明层级
  - [docs/pack-manifest.md](docs/pack-manifest.md) 仍未固定版本兼容策略
  - [review/research-compass.md](review/research-compass.md) 仍将“版本化 pack manifest 规范”列为研究空白
- 前置：不必等完整打包实现，但最好与安装元数据设计一起推进。
- 风险：中高。若先做过深设计，容易在实际包布局与入口成形前重复修订。
- 当前状态：已完成。官方实例 pack manifest 已使用 `runtime_compatibility` 补齐语义层兼容声明，并与 Python 包依赖范围对齐。

### D. MCP pack info 刷新一致性切片

- 做什么：修正或显式文档化 MCP 长生命周期进程对 pack metadata 的刷新时机，避免 manifest 已更新而 `get_pack_info` 仍返回旧缓存。
- 依据：
  - 当前切片实现中，fresh `Pipeline.info()` 已反映新 manifest 边界，但当前 MCP `get_pack_info` 仍返回旧的 `validators`/`skipped_details` 缓存
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md) 当前要求上下文恢复与状态读取应以 workspace 现实为准
- 前置：无。

## 2026-04-18 增量更新 — After VS Code Extension P0+P1

最近完成了一条重大方向切片：

- **VS Code Extension P0+P1**：完整 Extension 骨架（15 个 TypeScript 文件）+ MCP stdio client + Constraint Dashboard TreeView + GovernanceInterceptor 接口 + CopilotLLMProvider 骨架 + Activity Bar 图标 + F5 调试配置

这意味着平台现在已经同时具备：

1. 可 F5 启动的 VS Code Extension，Activity Bar 显示治理图标
2. MCPClient 通过 stdio 连接 Python MCP Server，复用全部 11 个 MCP 工具
3. Constraint Dashboard TreeView 实时展示 C1-C8 约束状态
4. 接口预留：GovernanceInterceptor（文件写入/终端命令/agent 行为拦截）、ReviewPanel、LLMProvider（Copilot 集成）、AgentSession（多 agent 递归治理数据模型）

### 新候选 A. F5 端到端验证 + Extension 发布准备

- 做什么：在 Extension Host 中实际启动插件，验证 MCP Server 连接、Constraint Dashboard 显示、Activity Bar 交互；修复实际运行中的问题；准备 `vsce package` 打包。
- 依据：
  - [design_docs/stages/planning-gate/2026-04-18-vscode-extension-p0-p1.md](design_docs/stages/planning-gate/2026-04-18-vscode-extension-p0-p1.md)
  - [design_docs/plugin-distribution-marketplace-direction-analysis.md](design_docs/plugin-distribution-marketplace-direction-analysis.md)
- 风险：低。
- 当前判断：**推荐**。骨架已编译通过，下一步是真实运行验证。

### 新候选 B. Pack Explorer TreeView (P2)

- 做什么：新增 TreeView 展示 pack 拓扑（层级化 tree topology），调用 MCP `get_pack_info` 工具。
- 依据：
  - [design_docs/hierarchical-pack-topology-direction-analysis.md](design_docs/hierarchical-pack-topology-direction-analysis.md)
  - [docs/pack-manifest.md](docs/pack-manifest.md)
- 风险：低。
- 当前判断：自然的下一个 UI 组件，优先级仅次于 A。

### 新候选 C. 真实 GovernanceInterceptor 实现

- 做什么：替换 PassthroughInterceptor，实现真正的文件写入/终端命令拦截，调用 MCP `governance_decide` 做决策。
- 依据：
  - [design_docs/stages/planning-gate/copilot-integration-runtime-simulation.md](design_docs/stages/planning-gate/copilot-integration-runtime-simulation.md)
  - [docs/platform-positioning.md](docs/platform-positioning.md)
- 风险：中。VS Code API 对文件写入拦截的能力有限。
- 当前判断：核心价值但实施复杂度中等，建议在 A 验证通过后再做。

### 新候选 D. Decision Log Viewer + WebView

- 做什么：新增 WebView 面板展示治理决策日志。
- 依据：
  - [design_docs/decision-logs-direction-analysis.md](design_docs/decision-logs-direction-analysis.md)
- 风险：低到中。
- 当前判断：优先级低于 A/B/C。

### 新候选 E. 递归治理流程图 WebView

- 做什么：用 WebView 可视化多 agent 递归治理链。
- 依据：
  - [design_docs/subagent-tracing-writeback-direction-analysis.md](design_docs/subagent-tracing-writeback-direction-analysis.md)
- 风险：中到高。WebView 实现量较大。
- 当前判断：最具差异化价值，但建议放到 P3 以后。

## 2026-04-18 当前 AI 倾向判断（After VS Code Extension P0+P1）

我当前倾向于直接进入 **新候选 A（F5 端到端验证）**。原因是：Extension 的 TypeScript 已经编译通过，但还没有在真实 Extension Host 环境中运行过。用户明确说"未插件化也不便于分发和收集问题"，因此尽快让 Extension 实际可用是当前最高价值方向。A 完成后再推 B（Pack Explorer）或 C（真实 GovernanceInterceptor）。

### 新候选 F. Extension 内置 MCP Server 安装/配置向导 ⚠️ 用户明确提出

- 做什么：Extension 安装后提供从 `release.zip` 直接安装 Python Runtime 的向导流程，包括：
  - 首次激活时检测是否已安装 Python Runtime
  - 如未安装，引导用户选择 release.zip 路径或自动从内嵌资源安装
  - **版本验证（必须一一对应）**：Extension v0.1.0 只能搭配 Python Runtime 特定版本，不兼容不匹配的版本
  - 安装后自动配置 `docBasedCoding.pythonPath` 等路径
  - 提供重装/更新/卸载等生命周期管理
- 依据：
  - 用户反馈："我希望安装插件后能直接从 release.zip 安装并配置一些路径"
  - [design_docs/plugin-distribution-marketplace-direction-analysis.md](design_docs/plugin-distribution-marketplace-direction-analysis.md) — 插件分发方向
  - [design_docs/tooling/Dual-Package Distribution Standard.md](design_docs/tooling/Dual-Package Distribution Standard.md) — 双包分发标准
  - [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md) — release 边界
- 设计要点：
  - Extension manifest 内嵌 `compatible_runtime_version` 字段
  - Python Runtime release.zip 内嵌 `version.json`（包含 runtime 版本和兼容 extension 版本范围）
  - 安装时双向版本校验：Extension 检查 Runtime 版本，Runtime 检查 Extension 版本
- 风险：中。版本锁定策略需要谨慎设计——过严会让升级困难，过松会出兼容性问题。
- 当前判断：高优先级。这是用户明确提出的分发体验需求，直接影响可用性和推广。

### 新候选 G. 跨编辑器/跨 CLI 适配层 ⚠️ 用户明确提出（长期待办）

- 做什么：设计并实现 MCP Server 和/或 Extension 的跨平台适配能力，使其不仅限于 VS Code，还能同时适配：
  - **跨编辑器**：VS Code、Trae（字节跳动 AI IDE）等
  - **跨 CLI/插件**：GitHub Copilot、OpenAI Codex 等 AI 助手
  - MCP 协议本身是编辑器无关的（stdio 传输），因此 Python MCP Server 天然跨平台
  - Extension UI 层（TreeView、WebView）需要为每个编辑器单独适配
  - 需要定义一个 **编辑器适配层抽象**（adapter pattern），把 UI 交互与 MCP 工具调用解耦
- 设计要点：
  - MCP Server（Python）已经是编辑器无关的 — 任何支持 MCP 的客户端都能连接
  - UI 适配层：定义 `EditorAdapter` 接口（TreeView / WebView / Notification / Settings），VS Code 实现为第一个 adapter
  - CLI 适配层：Copilot 通过 MCP tools + instructions 消费，Codex 可能需要不同的 prompt format
  - 长期维护：版本矩阵（Extension 版本 × 编辑器版本 × MCP Server 版本）需要管理
- 依据：
  - 用户反馈："我希望插件或是至少 MCP 能跨编辑器（如同时适配 vscode，trae），跨 CLI 或是插件（如：同时适配 copilot，codex）"
  - [docs/platform-positioning.md](docs/platform-positioning.md) — 平台定位
  - [design_docs/plugin-distribution-marketplace-direction-analysis.md](design_docs/plugin-distribution-marketplace-direction-analysis.md) — 插件分发
  - [design_docs/phase-35-external-skill-interface-direction-analysis.md](design_docs/phase-35-external-skill-interface-direction-analysis.md) — 外部技能接口
- 风险：高。这是一个开始后需要长期维护的内容，每增加一个编辑器/CLI 目标都会增加维护成本。
- 当前判断：**记录为长期待办**。MCP Server 层天然跨平台是好消息；UI 适配层建议在 VS Code 版本稳定后再开始第二个编辑器适配。当前优先级低于 A/F，但战略重要性高。
- 风险：低到中。问题更偏向状态一致性，而不是核心语义错误。
- 当前状态：已完成。长生命周期 `GovernanceTools` 现已按调用刷新 Pipeline，pack state 视图会跟随磁盘变化更新。

### E. Strict Doc-Loop Runtime Enforcement Slice

- 做什么：把当前仍停留在规则/提示词层的 doc-loop 对话约束进一步落到运行时可检查面，至少明确哪些约束可以被机器检查、哪些只能由上层 agent 指令承担，并补齐对应的状态审计或能力边界。
- 依据：
  - 当前 enforcement audit 结果表明，runtime 级 `check_constraints()` 主要仍只检查 C4/C5
  - [design_docs/tooling/Document-Driven Workflow Standard.md](design_docs/tooling/Document-Driven Workflow Standard.md) 与 [AGENTS.md](AGENTS.md) 已明确更严格的对话推进规则
  - 当前用户明确质疑“没有遵循严格的 doc-loop 规则”，且该质疑部分成立
- 前置：无。
- 风险：中。若把对话层约束和项目状态层约束混成一套，会导致职责边界再次模糊。
- 当前状态：已完成。runtime contract 已显式区分 machine-checked 与 instruction-layer 约束边界。

### F. Handoff Model-Initiated Invocation Slice

- 做什么：把 handoff workflow 的调用语义收口到“安全停点下允许 model 主动进入 handoff 分支，且 `generate / accept / refresh current / rebuild` 在未返回 `blocked` 时允许继续执行下一步”。
- 依据：
  - 当前用户最新明确要求：handoff 的构建应可由 model 主动调用，其他指令在不抛 `blocked` 的前提下也应可由 model 执行
  - `design_docs/tooling/Session Handoff Standard.md` 当前仍缺少 model 主动调用与 blocked stop 语义
  - `.codex/handoff-system/docs/Skill Workflow.md` 此前仍保留“若用户明确要求继续轮转”一类旧约束，需要在本切片中统一收口
- 前置：当前仓库已经回到安全停点，且 handoff proto-skill 已具备 `generate / accept / refresh current / rebuild` 四条分支。
- 风险：低到中。若收口不严，可能会放宽到越过安全停点或越过 blocked 停止条件。
- 当前状态：已完成。权威协议、workflow、skill contract 与 bootstrap / example 副本已统一到 model 主动调用 + blocked-only stop 语义；显式 slash 入口仍保留为示例而非唯一触发条件。

### G. 持续 Pre-Release Dogfood / Gap Tracking Slice

- 做什么：继续在真实开发中受控使用 CLI / MCP / Instructions，收集新的 dogfood 反馈，并只把命中的 regression / gap 拉成新的窄 planning-gate。
- 依据：
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md) 当前活跃待办中的“持续 pre-release dogfood：在实际开发中受控使用 CLI / MCP / Instructions，并收集反馈”
  - [docs/official-instance-doc-loop.md](docs/official-instance-doc-loop.md) 当前官方实例使用入口
  - [review/research-compass.md](review/research-compass.md) 中仍保留的研究与借鉴空白
- 前置：当前 safe-stop handoff 已生成，`.codex/handoffs/CURRENT.md` 已指向最新 canonical handoff。
- 风险：低到中。若缺少新信号就硬推实现，容易从“收集反馈”扩成无依据的大改。

### H. 通用外部 Skill 交互接口能力 Slice

- 做什么：把“model 可主动触发外部 skill、skill 在非 `blocked` 结果下可继续流转、slash 入口只是显式路由而非唯一调用面”等规则，收口为与当前项目和单一 handoff skill 解耦的通用接口能力；首个实现可以围绕当前 handoff skill，但最终产物必须能被 driver 侧复用。
- 依据：
  - 用户最新裁决：第 1 点与第 4 点应合并为通用接口能力，先可围绕当前外部 skill 特化固化，但最终要与当前项目和具体 skill 解耦
  - [docs/plugin-model.md](docs/plugin-model.md) 对“平台能力与具体实例/插件分离”的定位
  - [docs/subagent-management.md](docs/subagent-management.md) 当前已定义委派/协作边界，但尚未把“driver 与外部 skill 的交互 contract”标准化为独立能力
- 前置：当前 handoff workflow 已证明 model-initiated / blocked-only stop 语义可行，且 safe-stop handoff 已生成。
- 风险：中。若直接把 handoff 特例硬编码成平台 contract，容易把 project-local 经验错误上升为通用规范。
- 备注：用户要求先详细解释“authority -> shipped copies 单源编译 / 漂移检查”这一子问题，再决定它是并入本切片还是作为辅助机制单列。
- 当前状态：已完成。`docs/external-skill-interaction.md`、`src/workflow/external_skill_interaction.py`、pack rules、instructions / MCP surface、official instance reference 与 handoff skill texts 已统一到同一套 external skill interaction contract；`authority -> shipped copies` 也已作为 companion drift-check / distribution rule 落地。

### I. Safe-Stop Writeback Bundle Slice

- 做什么：把 safe-stop 收尾时必做的 handoff generation、`CURRENT.md` refresh、Checklist / Phase Map / direction / checkpoint 同步收口成一个 first-class writeback bundle，而不是依赖本轮这种逐项补写。
- 依据：
  - 用户最新裁决：第 3 点接受并标为 crucial
  - [design_docs/tooling/Document-Driven Workflow Standard.md](design_docs/tooling/Document-Driven Workflow Standard.md) 当前要求验证后回写状态板/阶段文档/协议文档与 handoff，但尚未把 safe-stop close 固化成 bundle 化 contract
  - [design_docs/tooling/Session Handoff Standard.md](design_docs/tooling/Session Handoff Standard.md) 已定义 handoff 分支，却尚未把 safe-stop 的外围状态面同步固定成原子写回能力
- 前置：当前 safe-stop handoff 已能生成并刷新 `CURRENT.md`，说明主流程存在；缺的是 bundled writeback contract。
- 风险：低到中。若 bundle 边界定义不准，可能把本应条件执行的写回强行绑定。
- 优先级：crucial（用户已明确确认）。
- 当前状态：已完成。`src/workflow/safe_stop_writeback.py` 已提供 bundle contract，`writeback_notify()` 现在会返回 required/conditional bundle items 与完整 `files_to_update`，workflow / handoff 协议也已同步到同一口径。

### J. Conversation Progression Contract Stability Slice

- 做什么：把“未经用户显式许可不得主动终止对话”与“遇到选择、审批、方向确认时必须先给分析/倾向判断，再以提问继续交流，必要时使用 `askQuestions`”收口为稳定行为支架，而不只停留在规则文案层。
- 依据：
  - 用户最新明确裁决：该约束“仍不能稳定生效，应当先处理这个”，且处理完之后再按既定 I → H 顺序继续
  - [design_docs/tooling/Document-Driven Workflow Standard.md](design_docs/tooling/Document-Driven Workflow Standard.md) 已定义对话推进规则，但当前 prompt / generator / tool 输出仍缺少可复用的操作支架
  - [design_docs/stages/planning-gate/2026-04-11-strict-doc-loop-runtime-enforcement.md](design_docs/stages/planning-gate/2026-04-11-strict-doc-loop-runtime-enforcement.md) 已明确 runtime 不会自动审查每一轮回复是否满足推进式提问，因此需要另一层稳定机制
- 前置：当前仓库无 active gate，可直接为这一新窄需求起 planning-gate。
- 风险：中。若切片膨胀成完整 conversational rule engine，会偏离本轮“稳定行为支架”目标。
- 优先级：当前最高。用户已明确要求先做，再回到 I / H。
- 当前状态：已完成。正式规则、project-local pack、prompt surfaces、instructions generator、MCP next-step outputs 与 official-instance always_on reference 已统一到 conversation progression contract；针对 `jsonschema` 依赖链受限的 official-instance 全文件回归，当前仍保留环境级验证缺口。

## AI 倾向判断

当前 A、B、C、D、E、F、H、I、J、BL-4、driver/实例分离审查、pack manifest schema 版本化、pre-existing test fix 与 safe-stop handoff generation 均已完成。当前仓库已经没有新的高优先级能力缺口需要立刻进入实现，剩余更像是"持续 dogfood"与"补记后续 backlog 边界"的轻量后续项。

原因是：

1. J、I、H 三条近期高优先级切片已经分别补齐了“对话推进稳定性”“safe-stop 收尾 contract”和“通用 external skill interaction contract”三块关键支架。
2. 当前 Checklist 里剩下的事项，要么是背景性的持续 dogfood，要么是低优先级或纯 backlog 记录，不再构成必须立刻实现的新主线。
3. 因此，更合理的下一步通常不是继续扩实现面，而是先保持 safe stop，并根据用户偏好决定是否要把 backlog 边界再单独文档化一次。

所以按当前信息，我当前倾向是：先回到无 active gate 的 safe stop，把 `G. 持续 Pre-Release Dogfood / Gap Tracking Slice` 作为默认背景主线；只有当用户希望先把 driver / adapter / 转接层 backlog 边界写清时，再开一条轻量文档切片。

## 用户决定

- 状态: `UPDATED`
- 当前已完成方向:
  - `H. 通用外部 Skill 交互接口能力 Slice`：已完成；对应 planning-gate 为 `design_docs/stages/planning-gate/2026-04-12-external-skill-interaction-interface.md`。
- 当前选定方向:
  - `G. 持续 Pre-Release Dogfood / Gap Tracking Slice`：用户已明确选择继续受控 dogfood；当前保持无 active gate，仅在出现真实 regression / gap signal 时再起新的窄 gate。该主线下已顺带完成 `validate` 语义区分、`depends_on` warning-only 校验、`provides` delegation advisory capability check 与 `checks` manifest 直连。
- 当前备选方向:
  - `driver / adapter / 转接层 backlog 记录切片`：若后续需要先把实现边界文档化，可单独起一条轻量文档切片，但不直接进入实现。
  - 所有条件触发 backlog（BL-1/2/3/5）与储备方案（R-1）已迁入 `design_docs/tooling/Backlog and Reserve Management Standard.md` 三层管理模型。
- 已完成方向:
  - `状态面一致性收口`：已完成，Checklist / Phase Map / CURRENT / checkpoint 的当前状态叙事已统一到 `v0.9.3` preview 口径，并恢复到无 active planning-gate 的 safe stop。
  - `J. Conversation Progression Contract Stability Slice`：已完成，已把"非用户许可不终止对话 + 选择/审批时以提问推进"的行为支架稳定到多层载体。
  - `I. Safe-Stop Writeback Bundle Slice`：已完成，已把 safe-stop close 收口为 bundle contract 与 targeted validation。  - `BL-4. 对话中临时规则突破 / 修改能力`：已完成，`temporary_override.py` 提供数据模型与约束分类，`governance_override` MCP tool 支持 register/revoke/list，safe-stop writeback bundle 自动过期。
  - `driver/实例分离审查`：已完成，交叉导入/包配置等边界清晰，唯一违规已修复为 pack-declared `shipped_copies` 动态发现。
  - `pack manifest schema 版本化`：已完成，`manifest_version: "1.0"` + 版本感知 loader + `docs/pack-manifest.md` Schema Versioning 节。
  - `pre-existing test fix`：已完成，全套 669 passed, 0 failures。
  - `validate 命令治理阻塞 vs 运行失败语义区分`：已完成，CLI / MCP / JSON 输出现已显式区分 governance blocked 与 runtime error，C5 在初始化态降级为 warn。
  - `overrides 字段消费`：已完成（方案 A），`PackContext.merged_overrides` + `check_overrides()` + `PrecedenceResolver` explicit_override + `Pipeline.info()` override_declarations / override_warnings + 权威文档 `overrides` 开放问题已回答。方案 C（结构化覆盖）标记为储备方案 R-1。
  - `depends_on 依赖校验`：已完成，未解析依赖以 warning 暴露，并进入 `Pipeline.info().dependency_status`。
  - `provides delegation capability check`：已完成，`RuleConfig.available_capabilities` 已接线，delegation 结果可附带 `capability_warnings` 并自动升级 review。
  - `checks 字段与 manifest 直连`：已完成，`PackRegistrar` 现会自动注册 `check(context)` 脚本，`Pipeline.info()` 暴露 `registered_checks`，`Executor` writeback 前会实际消费这些 checks。
- 已完成配套机制:
  - `authority -> shipped copies` 的单源编译 / 漂移检查：已作为 H 的 companion drift-check / distribution rule 落地。
- 已记录但本轮不实施:
  - driver 与外部 skill 交互的标准 / 接口 / 留空转接层 — 已结构化记录为下方 §Driver / Adapter / 转接层 Backlog（BL-1 / BL-2 / BL-3）。
  - 本轮讨论中另外两个仍特化于当前 skill 的后续需求，先记 backlog，不在当前切片实现。
- 当前结论: `所有已知 gap analysis 实现型缺口均已关闭（含 overrides 字段消费）。当前 post-v1.0 backlog 已收窄为纯条件触发项（BL-1/2/3/5）和一条储备方案（R-1），统一由 design_docs/tooling/Backlog and Reserve Management Standard.md 管理。仓库维持 dogfood-only 节奏。`

### K. Completion Boundary Protocol Slice（新增）

- 做什么：针对"完成边界失忆"这一已证实的 conversation progression contract 违规模式，在 pack 规则中新增 `completion_boundary_protocol`（方案 B）并在 copilot-instructions.md 增加静态冗余（方案 A），形成多层叠加防护。
- 依据：
  - 本轮 dogfood 中违规实际发生：overrides 实施完成后，AI 以"你是否还有其他想继续推进的方向，或者本轮可以收尾？"终结，违反 C1
  - 根因诊断：interaction_contract 仅在 AI 主动调用 MCP 工具时注入，完成边界时 AI 跳过工具调用→合约缺席→违规
  - [design_docs/tooling/Document-Driven Workflow Standard.md] 对话推进规则 §95-98 已定义约束
  - [src/mcp/tools.py] `_interaction_contract()` / `get_next_action()` / `writeback_notify()` 已返回合约，但需要强制触发
- 前置：无。
- 风险：低。仅新增 pack 规则字段 + MCP 工具行为 + 静态指令冗余，不改核心架构。
- 优先级：高。已实际违规。
- 渐进加固路径：B+A → R-3 (finalize_response MCP 校验) → R-2 (Chat Participant output gate)
- 当前状态：已完成。pack 规则新增 `completion_boundary_protocol`，`get_next_action()` 新增 `completion_boundary_reminder`，instructions generator 新增 Completion Boundary Rule 静态冗余，Document-Driven Workflow Standard 新增第 6 条。验证门全部通过（779 passed, 2 skipped）。渐进加固后续路径（R-3 → R-2）已登记到 Backlog Standard。

## Driver / Adapter / 转接层 Backlog（结构化记录）

以下条目从 Checklist 待办、direction candidates、Phase 0-35 实现、外部 skill interaction contract 与权威文档中提取，不涉及新 planning-gate，仅为后续方向提供结构化入口。

### 已落地的 Adapter / Bridge 实现

| 组件 | Phase | 位置 | 状态 |
|------|-------|------|------|
| Worker Adapters (LLMWorker, HTTPWorker) | 15 | `src/workers/` | 实验性（依赖外部 API，不纳入默认稳定面） |
| Notification Adapters (Console/File/Webhook) | 13 | `src/pep/notifiers/` | 稳定 |
| Pack Registrar Bridging | 25 | `src/pack/registrar.py` | 稳定 |
| External Skill Interaction Contract | H | `docs/external-skill-interaction.md` | 稳定（含 companion drift-check） |

### 尚未落地的 Backlog 条目

#### BL-1: Driver 职责定义文档

- **做什么**：把当前分散的 "driver" 概念（主 agent 对 external skill 结果的消费逻辑）统一到一份权威设计概述中，定义平台级 driver 的职责边界、输入来源与结果分发路径。
- **依据**：[docs/external-skill-interaction.md](../docs/external-skill-interaction.md) 已固定 skill 侧 contract，但 driver 侧（消费方）的职责仍分散在 pipeline / MCP tools / instructions generator 多处。
- **类型**：纯文档，不涉及代码实现。
- **触发条件**：当 dogfood 出现多 skill 消费场景或 driver 语义不清时触发。
- **优先级**：低。
- **当前状态**：已完成。`docs/driver-responsibilities.md` 定义 driver 角色/职责边界/输入来源/结果分发路径，与 `external-skill-interaction.md` 形成消费方-提供方对称引用，与 `subagent-management.md` supervisor 角色对齐。

#### BL-2: Adapter 分类与统一注册框架

- **做什么**：把现有三类 adapter（Worker / Notifier / Registry Bridge）的加载、发现、版本兼容逻辑抽取为统一描述模型，预留配置驱动的动态选择点。
- **依据**：[docs/plugin-model.md](../docs/plugin-model.md) 已定义插件模型抽象边界，但 adapter 级的统一注册/发现机制仍由各模块自行实现。当前 `PackRegistrar` 动态加载模式可作为模式参考。
- **类型**：设计文档 + 轻量骨架（如决定实施）。
- **触发条件**：当 dogfood 出现"根据 rule config 动态选择 adapter"的场景时触发。
- **优先级**：低到中。
- **依赖**：BL-1 的定义先行。

#### BL-3: 多协议转接层（远期）

- **做什么**：支持多协议 skill 调用（不仅 handoff，还包括远程 WebSocket / gRPC 等），定义内部协议→外部协议的转换、转移、恢复与重试中的协议中立边界。
- **依据**：[example/design_docs/stages/planning-gate/Post-MVP Scope Guardrails and Next-Step Plan.md](../example/design_docs/stages/planning-gate/Post-MVP%20Scope%20Guardrails%20and%20Next-Step%20Plan.md) 中已为 websocket / 远程适配器预留边界。[review/research-compass.md](../review/research-compass.md) 中仍将"版本化 pack manifest 规范"与"distribution 路径"列为研究空白。
- **类型**：设计文档→原型（视需求演进）。
- **触发条件**：当多协议/多格式需求从 dogfood 或外部用户需求中浮现时触发。
- **优先级**：低（超出当前版本规划）。
- **依赖**：BL-1 + BL-2。

### Backlog 与现有权威文档的关系

| 权威文档 | 与 Backlog 的关系 |
|----------|------------------|
| `docs/external-skill-interaction.md` | 已固定 skill 侧 contract；BL-1 补齐 driver 侧定义 |
| `docs/plugin-model.md` | 已固定插件抽象边界；BL-2 补齐 adapter 统一描述 |
| `docs/first-stable-release-boundary.md` | N5 (script-style validator) 与 BL-2 有交集，但互相独立 |
| `design_docs/tooling/Dual-Package Distribution Standard.md` | 打包/分发层面已固定；BL-3 的多协议层在其之上 |
| `design_docs/tooling/Document-Driven Workflow Standard.md` | 已定义对话推进与文档驱动规则；BL-4 补齐对话中临时规则突破的 contract |

#### BL-4: 对话中临时规则突破 / 修改能力

- **做什么**：把当前对话中由用户口头临时授权突破或修改默认行为规则的模式（例如"临时允许你使用 git，但仅限本地指令"），收口为可追溯、可审计、可撤销的 runtime contract，而不是依赖 model 记忆用户口头指令。
- **依据**：
  - 当前对话中用户临时授权修改了默认行为（"现在临时允许你使用 git，但仅限本地指令，禁止动远程"），该授权成功执行但仅靠 model 上下文维持，无持久化、无审计、无自动过期机制。
  - [design_docs/tooling/Document-Driven Workflow Standard.md](design_docs/tooling/Document-Driven%20Workflow%20Standard.md) 已定义 always-on 对话约束，但未区分"可被临时突破的约束"和"不可突破的硬约束"。
  - [docs/governance-flow.md](../docs/governance-flow.md) 已定义治理决策链，但决策链目前面向项目状态（gate / constraint），不面向对话行为层的动态 override。
- **类型**：设计文档 + 可能的轻量运行时支架（如需实施）。
- **触发条件**：当 dogfood 中再次出现用户临时修改行为规则的场景，或对话约束因上下文压缩而丢失临时 override 时触发。
- **优先级**：中。已证明该需求真实存在，但当前口头指令模式尚可工作。
- **依赖**：无硬依赖。与 conversation progression contract（J）有交集。
- **当前状态**：已完成。`src/workflow/temporary_override.py` 提供 `TemporaryOverride` 数据模型与可突破性分类（C1/C2/C3/C6/C7 overridable, C4/C5/C8 non-overridable）；`governance_override` MCP tool 支持 register/revoke/list；safe-stop writeback bundle 自动过期 session/until-next-safe-stop scoped override。