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

合并判断：

- 不并入 `localTrajectory`：`localTrajectory` 是 agent-owned lifecycle mutation tool，写 `.codex/progress-graph/local-work-trajectory.json`；`schedulerSubmitTasks` / `schedulerProjection` / `schedulerRunOnceAndProject` 都是 scheduler-owned surface，不应让 Local Work Trajectory 成为调度权威。
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
- 当 explicit binding-ref preflight 由 operator workflow 或 admission wrapper 启用时，admission ledger/readback 可携带 compact `binding_reference_summary`，只记录 counts、task/ref ids 与 errors，不保存 raw supervisor storage binding evidence JSON 或 raw binding payload。
- `doc-based-coding scheduler seed-dogfood-fixture --fixture binding-consumer` 提供 CLI/deterministic fixture：写入一个 compact supervisor storage binding artifact 与一个 consuming scheduler submission。MCP 侧暂不新增 seed tool；使用既有 `schedulerOperatorWorkflow(inspectBindingRefs=true, admit=true)` 消费该 fixture 并验证 ledger readback。

## 2026-06-19 增量：Scheduler Operator Workflow Tool

新增 MCP tool：

| Tool Name | 参数 | 核心职责 | 领域 |
|-----------|------|---------|------|
| `schedulerOperatorWorkflow` | `artifactId`, `version`, `inspectBindingRefs`, `admit`, `runLoop`, `refreshProjection`, `artifactStorePath`, `admissionLedgerPath`, `snapshotPath`, `eventLogPath`, `mergeGateEventLogPath`, `projectionOutputPath`, `evidenceId`, `evidencePath`, `runtimeProvider`, `maxTicks`, `maxRunsPerTick`, `maxRuntimeFailures`, `allowDuplicateAdmission`, `replaceExisting`, `actor`, `timestamp`, `guideContext`, `sourceGraphId`, `sourceNodeId` | 共享显式 operator workflow：读取 ExchangeArtifact admission candidates，可按 opt-in flag 对 exact artifact/version 执行只读 supervisor storage binding refs inspection，再按 opt-in flag admit、运行 bounded fake scheduler loop 并写 evidence、刷新 scheduler projection，然后读取 Host Evidence presentation；返回 per-step status | 调度 operator workflow / Host UX 收敛 |

合并判断：

- 不替代 `admitExchangeArtifact`：`schedulerOperatorWorkflow` 是组合型 operator surface；`admitExchangeArtifact` 仍是精确 admission 的最小写工具。
- 不替代 `schedulerBindingReferenceInspect`：统一 workflow 的 `inspectBindingRefs` 是 admission 前组合步骤；单独 read-only binding-ref inspection 仍保留为低层检查面。
- 当 `inspectBindingRefs` 与 admission 同时启用时，workflow admission result 与 admission ledger record 会保留 compact `binding_reference_summary`，用于 admission 后 readback。
- 不替代 `schedulerProjection`：统一 workflow 的 projection 步骤是 opt-in 串联动作；单独刷新 projection 仍需要保持独立只读投影写面。
- 不替代 `schedulerRunOnceAndProject`：统一 workflow 走 bounded daemon-loop + evidence readback 产品路径；`schedulerRunOnceAndProject` 仍是早期 one-pass fake-runtime smoke surface。
- 不并入 `localTrajectory`：统一 workflow 只写 scheduler-owned snapshot/event-log、admission ledger、scheduler-loop evidence 与 scheduler-derived projection artifact；不会写 agent-owned `.codex/progress-graph/local-work-trajectory.json`。
- `runtimeProvider` 当前仍只允许 `fake`。真实 Qoder 或其他 provider 必须继续走 host-owned runtime injection / permission evidence gate。
