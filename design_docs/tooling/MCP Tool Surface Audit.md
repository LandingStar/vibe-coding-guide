# MCP Tool Surface Audit

> 长期有效的 MCP 接口治理文档
> 来源：B-REF-7（Claude best practices — consolidate related operations）
> 审计日期：2026-04-18
> 审计范围：`src/mcp/server.py` + `src/mcp/tools.py` 全部 11 个 tools（含 `analyze_changes` 统一入口）

## 工具清单

| # | Tool Name | 参数数量 | 核心职责 | 领域 |
|---|-----------|---------|---------|------|
| 1 | `governance_decide` | 2 (input_text*, scope_path) | PDP→PEP 治理链 | 治理核心 |
| 2 | `check_constraints` | 0 | C1-C8 约束状态 | 治理核心 |
| 3 | `get_next_action` | 0 | 基于项目状态推荐下一步 | 工作流导航 |
| 4 | `writeback_notify` | 1 (phase_description*) | 阶段完成通知 + 自动推进 | 工作流导航 |
| 5 | `get_pack_info` | 2 (scope_path, level) | Pack 信息查询 | Pack 信息 |
| 6 | `governance_override` | 5 (action*, constraint, reason, scope, override_id) | 临时规则豁免 CRUD | 治理辅助 |
| 7 | `query_decision_logs` | 4 (trace_id, decision, intent, limit) | 决策日志查询 | 审计/可观测 |
| 8 | `impact_analysis` | 3 (changed_files, changed_symbols, max_depth) | 依赖图传播分析 | 变更分析（别名） |
| 9 | `coupling_check` | 2 (changed_files, changed_symbols) | 耦合注解检查 | 变更分析（别名） |
| 10 | `analyze_changes` | 3 (changed_files, changed_symbols, max_depth) | 统一变更分析 | 变更分析 |
| 11 | `promote_dogfood_evidence` | 10 (symptoms*, ...) | Dogfood 全链路 pipeline | Dogfood |

（`*` = required）

## 职责分组

### Group A: 治理核心（必须独立）
- `governance_decide` — 主入口，每次重要操作前调用
- `check_constraints` — 状态检查，与 governance_decide 中的约束检查有重叠但调用时机不同

**分析**：`governance_decide` 内部已调用 `check_constraints`。但 `check_constraints` 作为独立工具有明确的独立使用场景（上下文恢复、session 开始时），保持独立是合理的。

**结论：保持独立** ✅

### Group B: 工作流导航
- `get_next_action` — 推荐下一步
- `writeback_notify` — 阶段完成后推荐下一步

**分析**：两者都返回 "下一步推荐"，但触发时机完全不同：
- `get_next_action`：被动查询（"我不知道该做什么了"）
- `writeback_notify`：主动通知（"我刚完成了 X"），附带 checkpoint 写入和 planning-gate 扫描

**重叠度**：输出格式有重叠（都包含 instruction + files_to_update），但触发语义不同。如果合并为一个带 `mode: "query" | "notify"` 的工具，会增加参数复杂度而不减少调用次数。

**结论：保持独立** ✅

### Group C: Pack 信息
- `get_pack_info` — 单独的 pack 信息查询

**分析**：独立且职责单一。`governance_decide` 的返回值中也包含 `pack_info`，但 `get_pack_info` 支持 level 控制和独立调用（无需提供 input_text）。

**结论：保持独立** ✅

### Group D: 治理辅助
- `governance_override` — 三个子操作通过 `action` 参数复用一个 tool

**分析**：这是一个正确的合并示例 — register/revoke/list 共享 override 的领域概念，用 `action` 参数区分比拆成 3 个 tools 更好。

**结论：已正确合并** ✅

### Group E: 审计/可观测
- `query_decision_logs` — 决策日志查询

**分析**：独立且职责单一。不与其他 tool 重叠。

**结论：保持独立** ✅

### Group F: 变更分析 ⚠️ **可合并候选**
- `impact_analysis` — 依赖图传播
- `coupling_check` — 耦合注解匹配

**分析**：
- 两者的输入参数**完全相同**：`changed_files` + `changed_symbols`
- 两者的使用场景**完全重叠**："我改了这些文件/符号，还需要改什么？"
- 实际使用中，agent 几乎总是**同时调用两者**
- 两者的底层数据源不同（baseline_graph.json vs coupling_annotations.json），但这是实现细节

**合并建议**：合并为 `analyze_changes`，在输出中分两个 section 返回：
```json
{
  "impact": { "direct": [...], "transitive": [...] },
  "coupling_alerts": [...]
}
```

**状态：已实施** ✅ — `analyze_changes` 已添加为统一入口；旧工具名保留为向后兼容别名。

### Group G: Dogfood Pipeline
- `promote_dogfood_evidence` — 全链路 dogfood pipeline

**分析**：这是最重的 tool（10 个参数），但它封装了一条完整的 4 步 pipeline（evaluate → build → assemble → dispatch），遵循了"合并相关操作"的原则。参数多是因为 pipeline 本身的领域复杂度，不是过度拆分。

**结论：保持独立** ✅（但参数量需关注）

## 功能重叠矩阵

| Tool A ↓ / Tool B → | governance_decide | check_constraints | get_next_action | writeback_notify |
|---------------------|-------------------|-------------------|-----------------|------------------|
| **governance_decide** | — | 内部调用 ⚠️ | 无 | 无 |
| **check_constraints** | 被调用 | — | 内部调用 ⚠️ | 内部调用 ⚠️ |
| **get_next_action** | 无 | 内部调用 | — | 输出格式重叠 |
| **writeback_notify** | 无 | 内部调用 | 输出格式重叠 | — |

| Tool A ↓ / Tool B → | impact_analysis | coupling_check |
|---------------------|-----------------|----------------|
| **impact_analysis** | — | 输入完全相同 ⚠️ |
| **coupling_check** | 输入完全相同 ⚠️ | — |

## 合并建议总结

| 建议 | 涉及 Tools | 行动 | 优先级 | 破坏性 |
|------|-----------|------|--------|--------|
| **合并变更分析工具** | impact_analysis + coupling_check → `analyze_changes` | ✅ 已实施 | 中 | 低（旧名保留为别名） |
| **保持治理核心独立** | governance_decide + check_constraints | 不合并 | — | — |
| **保持导航独立** | get_next_action + writeback_notify | 不合并 | — | — |
| **关注参数膨胀** | promote_dogfood_evidence (10 params) | 监控但不改 | 低 | — |

## 整体评价

当前 10 个 tools 的拆分总体**合理**：

- **7/10 tools 职责清晰、不可合并**
- **1 组** (impact_analysis + coupling_check) 存在明确的合并机会（输入完全相同 + 使用场景重叠）
- **1 个** (governance_override) 已正确使用了 action 参数合并模式
- **1 个** (promote_dogfood_evidence) 参数较多但领域复杂度要求如此

对比 Claude best practices 的"consolidate related operations"原则：
- 当前 surface 没有严重的过度拆分问题
- 唯一明确的合并点是变更分析工具
- 如果未来新增 tools，应优先考虑是否可以作为现有 tool 的参数扩展

## 长期演进建议

1. **合并 impact_analysis + coupling_check**（可在后续切片实施）
2. **如果新增"pack 验证"工具**（validate_description + validate_pack_organization），应合并为一个 `validate_pack` 工具
3. **考虑为 governance_decide 添加 `include_pack_info: bool` 参数**，减少 agent 需要额外调用 get_pack_info 的情况
4. **promote_dogfood_evidence 的参数**：如果 pipeline 继续变复杂，考虑接受一个结构化的 `config` 对象而非平铺参数

## 2026-06-17 增量：Scheduler Tools

新增 MCP tool：

| Tool Name | 参数 | 核心职责 | 领域 |
|-----------|------|---------|------|
| `schedulerSubmitTasks` | `snapshotPath*`, `eventLogPath*`, `batch`, `batchId`, `tasks`, `title`, `summary`, `artifactId`, `artifactVersion`, `producer`, `timestamp`, `replaceExisting` | 将结构化 scheduler task batch submission 提交到 scheduler-owned snapshot/event log；复用 `scheduler_submission` exchange-artifact intake；不运行任务、不刷新 projection、不写 local trajectory | 调度任务提交 / 调度状态 |
| `schedulerProjection` | `snapshotPath*`, `schedulerEventLogPath`, `mergeGateEventLogPath`, `outputPath`, `trajectoryId`, `title`, `guideContext`, `sourceGraphId`, `sourceNodeId` | 从 scheduler snapshot 与可选 JSONL history 写出 scheduler-derived trajectory projection artifact | 调度可观测 / Progress Graph |
| `schedulerRunOnceAndProject` | `snapshotPath*`, `eventLogPath*`, `mergeGateEventLogPath`, `outputPath`, `maxRuns`, `timestamp`, `runtimeProvider`, `guideContext`, `sourceGraphId`, `sourceNodeId` | 显式读取 persisted scheduler snapshot/event log，执行一次 bounded fake-runtime scheduler pass，写回 snapshot，并刷新 scheduler-derived trajectory projection artifact；`runtimeProvider` 当前只允许 `fake` | 调度执行烟测 / 调度可观测 |
| `schedulerLifecycleControl` | `action*`, `controlPath*`, `snapshotPath`, `eventLogPath`, `daemonId`, `runId`, `timestamp`, `staleAfterSeconds`, `nowEpochSeconds` | 读写 scheduler daemon lifecycle control file；只做 deterministic control-file operation，不运行 provider、不刷新 projection、不写 local trajectory | 调度 lifecycle control |
| `schedulerLifecycleRunOnce` | `controlPath*`, `runtimeProvider`, `timestamp`, `maxTicks`, `maxRunsPerTick`, `maxRuntimeFailures` | 在 lifecycle state 允许时执行一次 bounded fake-runtime lifecycle-gated loop；paused/cancelled/stopped/stale 会跳过 scheduler mutation；`runtimeProvider` 当前只允许 `fake` | 调度 lifecycle execution |
| `schedulerLifecycleHarness` | `controlPath*`, `runtimeProvider`, `timestamp`, `maxCycles`, `maxLoopFailures`, `maxTicks`, `maxRunsPerTick`, `maxRuntimeFailures`, `staleAfterSeconds`, `nowEpochSeconds`, `policyCancelled`, `deadlineEpochSeconds`, `maxAttempts`, `retryStopReasons` | 通过 `run_scheduler_daemon_harness_with_policy()` 运行 policy-controlled bounded harness；支持 cancelled/deadline preflight 与 explicit retry stop reasons；不启动 daemon service、不刷新 projection、不执行 cleanup、不写 local trajectory；`runtimeProvider` 当前只允许 `fake` | 调度 lifecycle harness / policy |
| `schedulerDaemonSupervisorStep` | `supervisorId*`, `controlPath*`, `runtimeProvider`, `timestamp`, `sessionId`, `runId`, `hostId`, `requestedBy`, `statusReadbackAt`, `cancellationSource`, `cancellationReason`, `maxCycles`, `maxLoopFailures`, `maxTicks`, `maxRunsPerTick`, `maxRuntimeFailures`, `staleAfterSeconds`, `nowEpochSeconds`, `policyCancelled`, `deadlineEpochSeconds`, `maxAttempts`, `retryStopReasons` | 通过 `run_scheduler_daemon_supervisor_step()` 运行一轮 host-managed supervisor step；在 policy-controlled bounded harness 外增加 supervisor/session/run identity、cancellation-source metadata 与 lifecycle status readback；不启动 daemon service、不刷新 projection、不执行 cleanup、不写 local trajectory；`runtimeProvider` 当前只允许 `fake` | 调度 daemon supervisor / policy |
| `schedulerSupervisorDogfoodWorkflow` | `fixture`, `artifactId`, `version`, `artifactStorePath`, `admissionLedgerPath`, `snapshotPath`, `eventLogPath`, `controlPath`, `runtimeProvider`, `maxCycles`, `maxLoopFailures`, `maxTicks`, `maxRunsPerTick`, `maxRuntimeFailures`, `maxAttempts`, `retryStopReasons`, `allowDuplicateAdmission`, `replaceExisting`, `actor`, `timestamp`, `createdAt`, `daemonId`, `lifecycleRunId`, `supervisorId`, `sessionId`, `runId`, `hostId`, `requestedBy`, `statusReadbackAt` | 运行 deterministic fake-runtime supervisor dogfood workflow：seed fixture -> exact admission -> lifecycle start -> supervisor step -> final readback；不启动 daemon service、不刷新 projection、不执行 cleanup、不写 local trajectory；`runtimeProvider` 当前只允许 `fake` | 调度 daemon supervisor / dogfood workflow |
| `schedulerBindingReferenceInspect` | `artifactId*`, `version*`, `artifactStorePath` | 只读检查一个 exact stored scheduler submission artifact 中的 `supervisor_storage_binding_artifact` refs；复用 `inspect_supervisor_storage_binding_artifact_refs_for_submission()` 与 per-task validation，返回 `supervisor_storage_binding_reference_inspection` 产品；不 admit task、不写 scheduler snapshot/event log、不写 admission ledger、不读 raw evidence JSON、不刷新 projection、不写 local trajectory | 调度 admission preflight / binding refs readback |
| `agentExchangeMailbox` | `agentId*`, `artifactStorePath`, `includeArchived` | 只读构建某个 agent 的 ExchangeArtifact mailbox：inbox / outbox / related / actionable；复用 `inspect_agent_exchange_mailbox()`，敏感或 redaction-required artifact 只暴露元数据与 part types，不暴露 raw preview payload；不写 scheduler state、不改 ExchangeArtifact lifecycle、不写 admission ledger、不刷新 projection、不运行 provider、不写 local trajectory | agent coordination readback / ExchangeArtifact routing |
| `agentExchangeHistory` | `agentId`, `correlationId`, `artifactStorePath`, `includeArchived` | 只读构建 ExchangeArtifact communication history summary：participant/lifecycle counts、causality edges、compact log entries；支持 agent/correlation 过滤，敏感或 redaction-required artifact 不暴露 raw text/structured payload；不写 scheduler state、不改 ExchangeArtifact lifecycle、不写 admission ledger、不刷新 projection、不运行 provider、不写 local trajectory | agent coordination history / ExchangeArtifact readback |
| `agentExchangeActionCandidates` | `agentId`, `candidateType`, `artifactStorePath`, `admissionLedgerPath`, `includeArchived` | 只读构建 ExchangeArtifact action-candidate bridge：识别 `scheduler_submission_candidate` / `review_candidate` / `handoff_candidate` / `blocker_candidate` / `merge_candidate`，并返回 structured reasons、relation/ref/contract/admission clues；复用 store inspection 的 scheduler admission candidate 规则；敏感或 redaction-required artifact 不暴露 raw text/structured payload；不 admit task、不开 review、不写 handoff、不改 ExchangeArtifact lifecycle、不写 admission ledger、不刷新 projection、不运行 provider、不写 local trajectory | agent coordination action-candidate readback |
| `agentExchangeActionCandidateDecide` | `candidateId*`, `dispositionArtifactId*`, `actor*`, `disposition*`, `artifactStorePath`, `dispositionVersion`, `reason`, `targetSurface`, `replacementArtifactId`, `replacementVersion`, `timestamp`, `replaceExisting` | 为一个已存在 action candidate 写入标准 disposition ExchangeArtifact，支持 `accept` / `reject` / `defer` / `supersede`；只新增/替换 disposition artifact，不 admit task、不开 review、不写 handoff、不解析 merge gate、不改 source ExchangeArtifact、不写 admission ledger、不刷新 projection、不运行 provider、不写 local trajectory | agent coordination action-candidate disposition |
| `agentExchangeAcceptedSchedulerCandidateConsume` | `dispositionArtifactId*`, `dispositionVersion*`, `snapshotPath*`, `eventLogPath*`, `artifactStorePath`, `admissionLedgerPath`, `allowDuplicateAdmission`, `replaceExisting`, `validateBindingArtifactRefs`, `markConsumedOnSuccess`, `actor`, `timestamp` | 消费一个 accepted `scheduler_submission_candidate` disposition，并通过既有 exact-version admission helper 写 scheduler snapshot/event-log 与 admission ledger；拒绝非 accepted、非 scheduler candidate 或 target surface 不匹配的 disposition；不创建 disposition、不 admit 非 scheduler candidate、不开 review、不写 handoff、不解析 merge gate、不运行 provider、不刷新 projection、不写 local trajectory | agent coordination scheduler-candidate consumer |
| `agentExchangeAcceptedReviewCandidateConsume` | `dispositionArtifactId*`, `dispositionVersion*`, `artifactStorePath`, `actor` | 消费一个 accepted `review_candidate` disposition，并将其转换为现有 review intake payload；拒绝非 accepted、非 review candidate 或 target surface 不匹配的 disposition；不创建 disposition、不 admit scheduler task、不写 handoff、不解析 merge gate、不运行 provider、不刷新 projection、不写 local trajectory | agent coordination review-candidate consumer |
| `agentExchangeAcceptedHandoffCandidateConsume` | `dispositionArtifactId*`, `dispositionVersion*`, `handoffDir*`, `artifactStorePath`, `actor` | 消费一个 accepted `handoff_candidate` disposition，并将其转换为 schema-valid Handoff payload 后通过 handoff consumer 写入指定 handoff 目录；拒绝非 accepted、非 handoff candidate 或 target surface 不匹配的 disposition；不创建 disposition、不 admit scheduler task、不开 review、不解析 merge gate、不运行 provider、不刷新 projection、不写 local trajectory | agent coordination handoff-candidate consumer |
| `agentExchangeAcceptedMergeCandidateConsume` | `dispositionArtifactId*`, `dispositionVersion*`, `snapshotPath*`, `gateId*`, `approved*`, `artifactStorePath`, `mergeGateEventLogPath`, `reason`, `actor`, `resolvedAt`, `timestamp` | 消费一个 accepted `merge_candidate` disposition，并要求调用者显式提供 scheduler merge gate id 和 approved/rejected 决策；通过既有 `resolve_scheduler_merge_gate()` 更新 scheduler snapshot，可选写 merge-gate event log；拒绝非 accepted、非 merge candidate 或 target surface 不匹配的 disposition；不从 relation 推断 gate、不 admit scheduler task、不开 review、不写 handoff、不运行 provider、不刷新 projection、不写 local trajectory | agent coordination merge-candidate consumer |
| `agentExchangeAcceptedBlockerCandidateConsume` | `dispositionArtifactId*`, `dispositionVersion*`, `snapshotPath*`, `taskId*`, `reason*`, `artifactStorePath`, `eventLogPath`, `actor`, `timestamp` | 消费一个 accepted `blocker_candidate` disposition，并要求调用者显式提供 scheduler task id 和 blocker reason；更新 scheduler snapshot，可选写 `task_blocked` scheduler event；拒绝非 accepted、非 blocker candidate 或 target surface 不匹配的 disposition；不从 relation 推断 task、不 admit scheduler task、不开 review、不写 handoff、不解析 merge gate、不运行 provider、不刷新 projection、不写 local trajectory | agent coordination blocker-candidate consumer |
| `consumeWorkerTrajectoryReport` | `reportPath*`, `callerRole`, `actor`, `currentEventId`, `title`, `eventKind`, `startIfMissing`, `trajectoryTitle`, `guideContext` | leader/main/supervisor 侧消费一个 worker `Subagent Report.trajectory_update`：读取 report JSON、校验 `docs/specs/subagent-report.schema.json`，仅将 `append` / `advance` / `block` / `wait` / `resume` / `close` / `none` 映射为 leader-owned Local Work Trajectory mutation；拒绝 worker/subagent caller roles；不运行 provider、不写 scheduler state、不消费 ExchangeArtifact lifecycle | Local Work Trajectory / worker report consumer |
| `agentExchangeReply` | `sourceArtifactId*`, `sourceVersion*`, `replyArtifactId*`, `producer*`, `text`, `structured`, `replyVersion`, `artifactStorePath`, `kind`, `intent`, `audience`, `createdAt`, `replaceExisting` | 在本地 ExchangeArtifact store 中创建一个 exact-version reply artifact；记录 `causality.replies_to` / `caused_by` 与 compact `log` part，默认回复给 source producer；只写 ExchangeArtifact store，不 admit task、不运行 provider、不写 admission ledger、不刷新 projection、不写 local trajectory | agent coordination writeback / ExchangeArtifact reply |
| `agentExchangeTransition` | `artifactId*`, `version*`, `targetState*`, `actor*`, `artifactStorePath`, `reason`, `timestamp` | 将一个 exact stored ExchangeArtifact version 转为 `accepted` / `rejected` / `consumed` / `superseded` / `archived` 并追加 compact `log` part；目标状态已满足时幂等返回 `changed=false`；只写 ExchangeArtifact store，不 admit task、不运行 provider、不写 admission ledger、不刷新 projection、不写 local trajectory | agent coordination lifecycle / ExchangeArtifact state |
| `schedulerStorageBindingArtifactPublish` | `evidencePath*`, `artifactStorePath`, `artifactId`, `version`, `producer`, `audience`, `createdAt`, `replaceExisting` | 将一个 durable `supervisor_storage_binding_evidence` summary 投影为 compact exact-version ExchangeArtifact 并写入本地 ExchangeArtifact store；不 admit task、不运行 provider、不创建 agent home/scratch、不写 scratch manifest、不把 raw binding payload 嵌入 exchange artifact、不刷新 projection、不写 local trajectory | 调度 storage binding artifact publishing |
| `schedulerOperatorDogfoodClosure` | `fixture`, `artifactId`, `version`, `artifactStorePath`, `admissionLedgerPath`, `snapshotPath`, `eventLogPath`, `mergeGateEventLogPath`, `projectionOutputPath`, `evidenceId`, `evidencePath`, `runtimeProvider`, `maxTicks`, `maxRunsPerTick`, `maxRuntimeFailures`, `replaceExisting`, `inspectBindingRefs`, `markConsumedOnSuccess`, `actor`, `timestamp`, `createdAt`, `guideContext`, `sourceGraphId`, `sourceNodeId` | 运行 deterministic fake-runtime operator dogfood closure：seed fixture -> binding-ref inspection -> exact admission -> consumed lifecycle marking -> bounded fake scheduler loop evidence -> scheduler projection refresh -> Host Evidence presentation readback；不运行 live provider、不启动 daemon service、不执行 cleanup、不创建 agent home/scratch、不写 local trajectory；`runtimeProvider` 当前只允许 `fake` | 调度 operator dogfood closure |
| `schedulerGuideWorkerLocalOrchestration` | `artifactStorePath`, `admissionLedgerPath`, `snapshotPath`, `eventLogPath`, `trajectoryId`, `guideAgentId`, `workerAgentId`, `artifactIdPrefix`, `workerInstructions`, `maxParallelLanes`, `maxWaves`, `replaceExisting`, `allowDuplicateAdmission`, `timestamp`, `runtimeProvider`, `waveExecutionMode`, `workspaceRoot`, `scratchRoot` | 运行 fake-runtime guide-worker local trajectory orchestration：guide instruction artifact -> worker scheduler batch -> exact admission -> lane-limited scheduling wave -> fake/mock worker execution；`workerInstructions` 支持结构化自定义任务与 runtime-level `workerRuntimeProvider` 字段；MCP 入口拒绝非 fake worker provider，host-authorized Python runtime registry 才能注入 Qoder 等 provider；`waveExecutionMode=serial|threaded` 控制 wave executor invocation 与 deterministic merge；不刷新 projection、不创建 agent home/scratch、不写 local trajectory | 调度 guide-worker orchestration / Codex MCP |

合并判断：

- 不并入 `localTrajectory`：`localTrajectory` 是 leader/main/supervisor-owned lifecycle mutation tool，写 `.codex/progress-graph/local-work-trajectory.json`；bounded worker / subagent 不直接调用它，而是在 `Subagent Report.trajectory_update` 中提交进度/状态建议，由 leader 审核后写入。`schedulerSubmitTasks` / `schedulerProjection` / `schedulerRunOnceAndProject` 都是 scheduler-owned surface，不应让 Local Work Trajectory 成为调度权威。
- 不并入 `analyze_changes`：输入、数据源与使用时机均不同；`schedulerProjection` 面向运行时调度状态可观测，不是源码变更影响分析。
- `schedulerSubmitTasks` 不并入 `schedulerRunOnceAndProject`：前者只提交任务合同并写 snapshot/event log；后者推进 ready task 执行。提交与执行是 scheduler 生命周期中的两个动作，合并会让 MCP 调用方难以只登记任务而不运行。
- `schedulerSubmitTasks` 不并入 `schedulerProjection`：前者改变 scheduler task graph；后者只刷新只读 projection artifact。两者输出可以串联，但不应共享一个模糊的“刷新/提交”工具。
- `schedulerRunOnceAndProject` 不替代 `schedulerProjection`：前者会推进 scheduler snapshot 与 event log，后者只刷新 projection artifact。两者都不写 agent-owned local trajectory。
- `schedulerRunOnceAndProject` 第一版只暴露 fake runtime / shared-process sandbox smoke path；`runtimeProvider` 是显式 guard 参数，默认/空值/`fake` 才会执行，`qoder` 或未知 provider 会返回 fake-only 错误。真实 Qoder 或多 runtime provider 选择应等 host permission、sandbox 与 adapter registry 入口明确后再扩。
- 当前 fake-only 执行路径已经通过 `build_runtime_registry_from_config()` 构建 `AgentRuntimeAdapterRegistry`，并传入 `RuntimeHostInvocation(surface="mcp-scheduler-run-once")`。成功返回会报告 `runtime_registry_providers=["fake"]`。这只是把 Host wiring seam 提前固定住，不代表 MCP 已允许真实 qoder 执行。
- 当前保留为独立工具是合理的，因为它们分别对应 submit / project / run+project 三个不同 lifecycle action，同时避免把 scheduler mutation 误解为 trajectory mutation。
- 当前端到端冒烟顺序已固化为 `schedulerSubmitTasks -> schedulerProjection -> schedulerRunOnceAndProject`，并由 `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md` 及 bootstrap 副本提供 agent 操作提示；该提示词只用于 scheduler lifecycle 验证，不替代 `localTrajectory`。
- `schedulerLifecycleHarness` 不替代 `schedulerLifecycleRunOnce`：前者是 host-managed bounded harness + policy wrapper，可能执行多个 harness attempts；后者是单次 lifecycle-gated loop。需要只跑一次 lifecycle decision 时保留 run-once，关注 retry/deadline/cancel policy 时使用 harness。
- `schedulerDaemonSupervisorStep` 不替代 `schedulerLifecycleHarness`：前者是在 harness/policy 外增加 host-owned supervisor identity 与 status readback 的调用层；需要纯 policy harness 验证时保留 harness，关注 host supervisor/session/run readback 时使用 supervisor step。
- `schedulerSupervisorDogfoodWorkflow` 不替代 `schedulerDaemonSupervisorStep`：前者是完整 dogfood 序列，会 seed fixture、admit、start lifecycle 并执行 supervisor step；后者是单次 supervisor invocation primitive。验证完整 operator sequence 时用 workflow，验证 supervisor step contract 时保留单步工具。
- `schedulerBindingReferenceInspect` 不替代 `admitExchangeArtifact`：前者是 admission 前的只读 binding-ref inspection，不写 scheduler/admission state；后者是 explicit admission 写工具。存在 supervisor storage binding artifact refs 时，应先 inspect，再由 operator 明确选择是否 admit。
- `agentExchangeMailbox` 不替代 `dbc://exchange-artifacts/bundle`：bundle 是 store-level inspection 和 admission-candidate readback；mailbox 是 per-agent routing/read model，用于回答某个 agent 的 inbox/outbox/related/actionable。两者都只读，但阅读视角不同。
- `agentExchangeMailbox` 不替代 `admitExchangeArtifact` 或 `schedulerBindingReferenceInspect`：mailbox 不执行 admission preflight，不验证 binding refs，不改变 lifecycle，只帮助 agent 找到需要处理的 coordination products。
- `agentExchangeHistory` 不替代 `agentExchangeMailbox`：mailbox 回答“某个 agent 当前应看什么/处理什么”；history 回答“某条 exchange 历史发生了什么、有哪些 causality/log/participant/lifecycle clues”。两者都只读，但一个面向路由，一个面向回放和审计。
- `agentExchangeHistory` 不替代 raw transcript 或 `JsonlCoordinationEventLog`：history summary 从已存 ExchangeArtifact 的 causality 和 compact `log` parts 派生，不保存模型原始消息、tool call transcript 或 runtime trace。
- `agentExchangeActionCandidates` 不替代 `agentExchangeMailbox` 或 `agentExchangeHistory`：action candidates 回答“哪些 communication products 看起来应进入 scheduler/review/handoff/blocker/merge follow-up”；mailbox/history 仍分别负责 per-agent 视角和历史回放。
- `agentExchangeActionCandidates` 不替代 `admitExchangeArtifact`、review intake、handoff builder 或 merge tools：它只返回候选、理由和线索，不执行 mutation。scheduler submission candidate 复用 store inspection 的 admission candidate 判定，但最终 admission 仍必须由 exact-version admission surface 显式执行。
- `agentExchangeActionCandidateDecide` 不替代真实 executor：它只把候选处置写成一个 coordination product，供后续 scheduler/review/handoff/merge surface 显式消费。`accept` 不等于已经 admit/review/handoff/merge。
- `agentExchangeAcceptedSchedulerCandidateConsume` 只覆盖 accepted scheduler submission candidates：它是 disposition -> exact scheduler admission 的窄消费桥，不消费 review/handoff/blocker/merge candidates，也不运行 provider 或刷新 projection。
- `agentExchangeAcceptedReviewCandidateConsume` 只覆盖 accepted review candidates：它是 disposition -> review intake 的窄消费桥，不消费 scheduler/handoff/blocker/merge candidates，也不持久化 review 队列以外的 scheduler-owned 状态。
- `agentExchangeAcceptedHandoffCandidateConsume` 只覆盖 accepted handoff candidates：它是 disposition -> handoff delivery 的窄消费桥，不消费 scheduler/review/blocker/merge candidates；`handoffDir` 是显式必填，以避免隐式写入不清楚的 handoff 位置。
- `agentExchangeAcceptedMergeCandidateConsume` 只覆盖 accepted merge candidates：它是 disposition -> explicit merge gate resolution 的窄消费桥，不消费 scheduler/review/handoff/blocker candidates；`gateId` 和 `approved` 是显式必填，避免从普通 `merges_into` relation 猜测 scheduler-owned gate。
- `agentExchangeAcceptedBlockerCandidateConsume` 只覆盖 accepted blocker candidates：它是 disposition -> explicit task blocking 的窄消费桥，不消费 scheduler/review/handoff/merge candidates；`taskId` 和 `reason` 是显式必填，避免从普通 `blocks` / `waits_for` relation 猜测 scheduler-owned task。
- `consumeWorkerTrajectoryReport` 不替代 `localTrajectory`：它只消费 schema-valid worker report 中的第一版 `trajectory_update` 建议，并保留 leader/main/supervisor authority。复杂 pack、merge、relate、anchor 或 child trajectory 操作仍需要 leader 直接使用 `localTrajectory`。
- `consumeWorkerTrajectoryReport` 不替代 worker report schema：worker 仍只写 `Subagent Report.trajectory_update`，不获得 Local Work Trajectory mutation authority；worker/subagent caller roles 会被拒绝并指向 `docs/worker-trajectory-update-reporting.md`。
- `agentExchangeReply` 不替代 `agentExchangeMailbox`：mailbox 是每个 agent 的只读通信视图；reply 是 exact-version 写侧产品，会新建带 causality/log clues 的 reply artifact。两者组合形成最小读写闭环，但不承担 scheduler admission 或 provider execution。
- `agentExchangeTransition` 不替代 `admitExchangeArtifact` 或 `markConsumedOnSuccess`：transition 只改变一个 exact ExchangeArtifact version 的 coordination lifecycle；admission/consume-on-success 仍属于 scheduler operator/admission 流程，不应由通用 agent lifecycle transition 自动触发。
- `agentExchangeReply` 与 `agentExchangeTransition` 不并入 `schedulerOperatorWorkflow`：它们是 agent coordination store primitives，可被 scheduler/operator 后续消费，但本身不检查 admission candidates、不运行 fake loop、不刷新 projection。
- `schedulerStorageBindingArtifactPublish` 不替代 `schedulerBindingReferenceInspect`：前者把 durable evidence summary 发布成 exact-version binding artifact；后者检查下游 scheduler submission 是否正确引用了该 artifact。发布和引用检查是两个 lifecycle action。
- `schedulerStorageBindingArtifactPublish` 不替代 `schedulerSupervisorDogfoodWorkflow`：supervisor workflow 产出 durable evidence；publish surface 只消费已有 evidence summary 并写 exchange store。它不运行 supervisor step，也不创建真实 agent home/scratch。
- 当 explicit binding-ref preflight 由 operator workflow 或 admission wrapper 启用时，admission ledger/readback 可携带 compact `binding_reference_summary`，只记录 counts、task/ref ids 与 errors，不保存 raw supervisor storage binding evidence JSON 或 raw binding payload。
- `schedulerOperatorDogfoodClosure` 不替代 `schedulerOperatorWorkflow`：前者是完整 deterministic evidence closure，会 seed fixture、admit、mark consumed、run bounded loop、refresh projection 并 read Host Evidence；后者仍是 opt-in operator step composer，用于只验证 candidate inspection、binding-ref inspection、admission、loop 或 projection 中的某个步骤。
- `schedulerOperatorDogfoodClosure` 不替代 `schedulerBindingReferenceInspect` 或 `admitExchangeArtifact`：closure 用于整链狗粮证据闭环；低层 read-only inspection 与 exact admission 工具仍保留为最小可组合 surface。
- `doc-based-coding scheduler seed-dogfood-fixture --fixture binding-consumer` 提供 CLI/deterministic fixture：写入一个 compact supervisor storage binding artifact 与一个 consuming scheduler submission。需要完整 operator closure 时，优先使用 `schedulerOperatorDogfoodClosure` 或 CLI `operator-dogfood-closure`；需要单独验证 admission 前后 readback 时，继续使用 `schedulerOperatorWorkflow(inspectBindingRefs=true, admit=true)` 或低层 inspection/admission tools。
- `doc-based-coding scheduler guide-worker-exchange-dogfood` 是 2026-06-23 新增的 CLI/runtime dogfood surface，不是 MCP tool。它复用已完成的 agent exchange surfaces，串联 guide-created coordination artifact、worker mailbox readback、worker reply、worker scheduler submission candidate、guide disposition，以及 accepted scheduler-candidate consumer。它会写本 slice 拥有的 ExchangeArtifact products、scheduler snapshot/event-log state 与 admission ledger，不运行 live provider、不刷新 projection、不保存 raw transcript、不写 agent-owned Local Work Trajectory。若未来需要 MCP 入口，应开单独 planning gate 并作为同一 runtime helper 的薄 wrapper，而不是在 audit 中预先声明。
- `schedulerGuideWorkerLocalOrchestration` 是 2026-06-24 新增的 Codex-facing MCP thin wrapper；`doc-based-coding scheduler guide-worker-local-orchestration` 仍是同一 runtime helper 的 CLI surface。两者复用 ExchangeArtifact store、exact scheduler admission、scheduler snapshot/event-log、preflight 与 fake runtime adapter，完成 guide instruction artifact -> worker scheduler batch -> lane-limited parallel wave -> fake/mock worker execution 的最小闭环。`parallel_wave` 表示 scheduler 可并行语义：每个 wave 至多从每条 `ContextScope.lane_id` 选择一个 ready worker task；`waveExecutionMode=threaded` 可对 fake/mock runtime invocation 做 wave-level concurrent attempt，但 scheduler state/result merge 仍按 sorted `task_id` 确定性执行。Runtime 层的 `workerRuntimeProvider` 可由 host-authorized Python caller 映射到注入的 Qoder 或 Codex CLI adapter；MCP 入口会提前拒绝非 fake `workerRuntimeProvider`，避免 Codex MCP 直接运行 live provider。MCP 入口接受结构化 `workerInstructions`，也接受 `guideTask` + `plannerLaneSpecs` 让 deterministic guide planner 生成具体 lane-bound worker instructions；字段错误会返回清晰 validation error。它不运行 live provider、不刷新 projection、不保存 raw transcript、不创建 agent home/scratch、不写 agent-owned Local Work Trajectory。
- `doc-based-coding qoder guide-worker-smoke`、`doc-based-coding codex guide-worker-smoke` 与 `run_host_owned_guide_worker_provider_execution()` 是 2026-06-24 新增/扩展的 host-owned provider wrapper，不是 MCP tool。它复用 guide-worker local orchestration helper、host-authorized runtime wiring 与 `RuntimeHostInvocation(surface="host-authorized-adapter")`；Qoder 使用 `RuntimeProviderPermissionGrant(provider="qoder", allow_sdk_client=True)`，Codex CLI 使用 `RuntimeProviderPermissionGrant(provider="codex", allow_process_spawn=True)`。该 wrapper 可运行 `workerRuntimeProvider="qoder"` 或 `workerRuntimeProvider="codex"` 的 lane wave 并写 compact `host_guide_worker_provider_execution_evidence`。该 wrapper 也可承接 deterministic guide planner 的 `GuideWorkerPlanningRequest`；CLI 可用 `--guide-task-title`、`--guide-task-summary` 与 repeatable `--planner-lane` 生成 planned provider workers。`workerInstructions` / `plannerLaneSpecs` 支持 `sandboxProfile`，默认 `shared-process`，host wrapper 可通过 `git_worktree_sandbox_root` 与 `sandbox_allocation_evidence_id` 显式启用 git-worktree allocation receipt evidence。evidence 会包含 planner metadata、generated instructions、per-worker execution receipts、review-only worker writeback receipts 与 git-worktree worker patch artifact refs；writeback receipts 包含 sandbox allocation id、sandbox provider、output artifact ref、artifact delta changed refs、`patch_artifact_ref` 与 `merge_review_state=review_required`。git-worktree patch proposals 会写入 ExchangeArtifact store，使用 `intent=request_merge` / `merges_into` relation 接入既有 `merge_candidate` readback；`agentExchangeActionCandidates` 对该 product type 的建议 surface 为 `workerPatchReview`。`doc-based-coding scheduler consume-worker-patch-review` 是后续新增的 CLI/operator consumer，不是 MCP tool：它只消费 accepted worker patch proposal disposition，并显式执行 `check` / `apply` / `reject`；`apply` 要求调用者提供 source workspace 并使用 `git apply --check` + `git apply`，`reject` 不运行 git apply。`doc-based-coding scheduler preflight-worker-patch-composition` 也是 CLI/operator surface，不是 MCP tool：它读取多个 exact worker patch proposal artifacts，在临时 workspace 中按调用者顺序运行 `git apply --check` / `git apply`，报告首个失败 patch 与 touched-path collisions，但不突变 source workspace、不写 disposition、不自动排序、不解决冲突。该 wrapper、patch consumer 与 composition preflight 均保持 MCP fake-only，不接受 raw token 值，不刷新 projection，不保存 raw transcript，不创建 persistent agent home，不自动 apply/merge worker worktree patch，不自动清理 sandbox，不写 agent-owned Local Work Trajectory；readiness-negative 时应在 ExchangeArtifact store、scheduler state/event log、evidence 写入前 fail closed。

## 2026-06-19 增量：Scheduler Operator Workflow Tool

新增 MCP tool：

| Tool Name | 参数 | 核心职责 | 领域 |
|-----------|------|---------|------|
| `schedulerOperatorWorkflow` | `artifactId`, `version`, `inspectBindingRefs`, `admit`, `runLoop`, `refreshProjection`, `artifactStorePath`, `admissionLedgerPath`, `snapshotPath`, `eventLogPath`, `mergeGateEventLogPath`, `projectionOutputPath`, `evidenceId`, `evidencePath`, `runtimeProvider`, `maxTicks`, `maxRunsPerTick`, `maxRuntimeFailures`, `allowDuplicateAdmission`, `replaceExisting`, `actor`, `timestamp`, `guideContext`, `sourceGraphId`, `sourceNodeId` | 共享显式 operator workflow：读取 ExchangeArtifact admission candidates，可按 opt-in flag 对 exact artifact/version 执行只读 supervisor storage binding refs inspection，再按 opt-in flag admit、运行 bounded fake scheduler loop 并写 evidence、刷新 scheduler projection，然后读取 Host Evidence presentation；返回 per-step status | 调度 operator workflow / Host UX 收敛 |
| `schedulerOperatorDogfoodClosure` | `fixture`, `artifactId`, `version`, `artifactStorePath`, `admissionLedgerPath`, `snapshotPath`, `eventLogPath`, `mergeGateEventLogPath`, `projectionOutputPath`, `evidenceId`, `evidencePath`, `runtimeProvider`, `maxTicks`, `maxRunsPerTick`, `maxRuntimeFailures`, `replaceExisting`, `inspectBindingRefs`, `markConsumedOnSuccess`, `actor`, `timestamp`, `createdAt`, `guideContext`, `sourceGraphId`, `sourceNodeId` | 共享 deterministic operator closure：默认 binding-consumer fixture，串联 seed、binding-ref inspection、exact admission、consume、bounded fake loop、projection refresh 与 Host Evidence readback；返回与 CLI/runtime 相同的 closure summary / authority split | 调度 operator dogfood closure |

合并判断：

- 不替代 `admitExchangeArtifact`：`schedulerOperatorWorkflow` 是组合型 operator surface；`admitExchangeArtifact` 仍是精确 admission 的最小写工具。
- 不替代 `schedulerBindingReferenceInspect`：统一 workflow 的 `inspectBindingRefs` 是 admission 前组合步骤；单独 read-only binding-ref inspection 仍保留为低层检查面。
- `schedulerOperatorDogfoodClosure` 不并入 `schedulerOperatorWorkflow` 参数：closure 有固定 dogfood 证据闭环和默认 binding-consumer fixture，若做成 workflow 的又一个 mode 会让 opt-in step composer 同时承担 fixture seeding、consume 默认、projection/evidence/readback 整链语义，降低工具边界清晰度。
- `schedulerOperatorDogfoodClosure` 不替代 CLI `operator-dogfood-closure`：MCP 是 Codex primary agent-facing surface；CLI 仍是本地/脚本 operator surface，两者复用同一 backend request/result。
- 当 `inspectBindingRefs` 与 admission 同时启用时，workflow admission result 与 admission ledger record 会保留 compact `binding_reference_summary`，用于 admission 后 readback。
- 不替代 `schedulerProjection`：统一 workflow 的 projection 步骤是 opt-in 串联动作；单独刷新 projection 仍需要保持独立只读投影写面。
- 不替代 `schedulerRunOnceAndProject`：统一 workflow 走 bounded daemon-loop + evidence readback 产品路径；`schedulerRunOnceAndProject` 仍是早期 one-pass fake-runtime smoke surface。
- 不并入 `localTrajectory`：统一 workflow 只写 scheduler-owned snapshot/event-log、admission ledger、scheduler-loop evidence 与 scheduler-derived projection artifact；不会写 agent-owned `.codex/progress-graph/local-work-trajectory.json`。
- `runtimeProvider` 当前仍只允许 `fake`。真实 Qoder 或其他 provider 必须继续走 host-owned runtime injection / permission evidence gate。
