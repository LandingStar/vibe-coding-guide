# Payload + Handoff Footprint Controlled Dogfood — 2026-04-16

## 文档定位

本文件记录 `Payload + Handoff Footprint Controlled Dogfood` 的实际运行结果，用来区分：

1. 自动化测试已证明的边界。
2. mocked integration 已证明的边界。
3. 真实运行 signal 已暴露的边界与缺口。

## Preflight

- 当前 active canonical handoff: `2026-04-16_0915_llmworker-structured-payload-producer-alignment_stage-close`
- `CURRENT.md` 与 `.codex/checkpoints/latest.md` 的 handoff footprint 一致。
- 当前 PowerShell 会话中没有现成的 LLM 环境变量名；live run 改为从仓库本地凭据文件读取，再仅在进程内注入临时 env var。
- live LLM 目标：DashScope OpenAI-compatible endpoint，model=`qwen-plus`。
- 停止条件：
  - baseline `StubWorker` 路径必须至少跑通一次。
  - live `LLMWorker` 路径必须至少执行一次；即使结果不是 payload writeback success，也要记录真实 signal，而不是继续扩实现。

## Baseline Run — StubWorker

运行方式：通过 `Executor + StubWorkerBackend + WritebackEngine` 在临时目录执行一条 `allowed_artifacts=["docs/controlled-dogfood-stub.md"]` 的真实 payload-derived writeback。

结果：

- review_state: `applied`
- report validation: `valid=true`
- report status: `completed`
- planned payloads: `docs/controlled-dogfood-stub.md` / `update`
- summary writeback 与目标文件写回都成功
- 目标文件内容被更新为受控 markdown payload
- 当前 handoff footprint 与 checkpoint handoff footprint 完全一致

结论：

- 当前 `StubWorker` payload path、`WritebackEngine` payload consumer、以及 latest handoff footprint 恢复入口可以一起成立。
- baseline 链路没有发现新的恢复或写回边界问题。

## Live Run — LLMWorker

运行方式：通过 `Executor + LLMWorker + WritebackEngine` 在临时目录执行一条 live DashScope 请求，`allowed_artifacts=["docs/controlled-dogfood-llm.md"]`。

第一次 live run 结果：

- review_state: `applied`
- report validation: `valid=true`
- report status: `completed`
- `artifact_payloads`: 空
- writeback: 只生成 summary writeback，没有目标 artifact writeback
- verification_results 中出现：`Ignored 1 invalid artifact_payload candidate(s).`

进一步诊断（直接查看 raw response）显示：

- 模型按要求返回了 JSON object。
- payload `path` 正确落在允许范围内：`docs/controlled-dogfood-llm.md`
- 但 payload 使用了当前 schema 不接受的枚举值：
  - `operation="upsert"`
  - `content_type="text/markdown"`

因此归一化后的 `LLMWorker` report 仍然是 schema-valid `completed`，但 payload candidate 被保守丢弃，无法触发 artifact writeback。

## 真实 Signal

当前最重要的真实 signal 不是“LLMWorker 无法工作”，而是：

1. live model 已能稳定返回 schema-valid report。
2. 当前 prompt / response contract 还不足以把 payload candidate 稳定约束到 schema 允许的 operation/content_type 枚举。
3. 现有保守归一化策略按预期阻止了非法 payload 进入 writeback。
4. 因此当前系统更像是“report baseline 已稳定，live payload producer 语义尚未稳定”，而不是“整条真实路径不可用”。

## 区分三类证据

### 测试证明

- `LLMWorker` 成功/失败/降级路径都能返回 schema-valid report。
- mocked `LLMWorker -> payload-derived writeback` 集成链可以打通。
- 全量基线仍为 `942 passed, 2 skipped`。

### Mock 证明

- 在 mocked LLM response 下，单 payload producer 与 writeback 链路可用。

### Real Signal

- live DashScope 返回的 JSON response 会在 payload 语义层偏离 schema 允许枚举，即使顶层 JSON 结构本身正确。
- 当前 live prompt 强度不足以稳定拿到可消费 payload。

## 结论

本轮 controlled dogfood 可以收口，且结论足够明确：

1. `payload + handoff footprint` 的 baseline 已成立。
2. live real-worker 路径已经给出一个具体且可复现的 follow-up 缺口。
3. 下一条默认主线不该继续泛化 dogfood，而应转入一个更窄的 real-worker consistency / contract-hardening 切片。

## 推荐下一方向

### A. LLMWorker live payload contract hardening

- 目标：把 live model 常见的近似枚举值收敛到 schema 允许集合，优先处理 prompt 强化与保守归一化边界。
- 依据：本文件的 live signal、`docs/subagent-schemas.md`、`design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md`
- 当前判断：推荐。

### B. HTTPWorker failure fallback schema alignment

- 目标：补齐另一路 real-worker 的失败态 schema 一致性，但不动远端成功态透传。
- 依据：`docs/subagent-schemas.md` 与当前 dogfood 结果对 real-worker consistency 的提醒。
- 当前判断：可做，但优先级低于 A。