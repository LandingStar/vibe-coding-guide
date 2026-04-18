# 子 Agent 研究综合报告

## 文档定位

本文件综合以下 5 类来源，形成子 agent 方向的全景分析与可行动建议：

1. **5 份外部产品研究**：LangGraph、OpenAI Agents SDK、AutoGen、CrewAI、Semantic Kernel
2. **VibeCoding-Workflow 项目分析**：`review/vibecoding-workflow-sakura1618.md`
3. **内部设计文档**：`design_docs/subagent-management-design.md`
4. **平台权威文档**：`docs/subagent-management.md`、`docs/delegation-decision.md`、`docs/escalation-decision.md`
5. **Gap 分析**：`design_docs/subagent-tracing-writeback-direction-analysis.md`

---

## 1. 当前实现状态总览

| 核心对象 | 文档 | 代码实现 | 状态 |
|----------|------|---------|------|
| Delegation Decision | ✅ | ✅ executor 路由 | 部分（缺 PDP 生成逻辑） |
| Supervisor | ✅ | ✅ 由 Executor 代表 | 内嵌 |
| Worker | ✅ | ✅ Protocol + LLMWorker/HTTPWorker/StubWorker | **完整** |
| Subagent Contract | ✅ | ✅ ContractFactory.build() | **完整** |
| Subagent Report | ✅ | ✅ ReportValidator.validate() | **完整** |
| Handoff | ✅ | ✅ HandoffBuilder.build() | **完整** |
| Escalation | ✅ | ✅ EscalationNotifier Protocol | **完整** |
| Review State | ✅ | ✅ ReviewStateMachine 6×7×8 | **完整** |

**结论**：8 个核心对象中 6 个完整实现，1 个内嵌，1 个部分实现。子 agent 管理的基本管道已贯通。

---

## 2. 外部研究模式映射

### 2.1 已采纳的模式

| 外部模式 | 来源 | 我们的实现 |
|----------|------|-----------|
| Supervisor-Worker 默认 | LangGraph, CrewAI | ✅ Executor = Supervisor, Protocol Worker |
| Handoff 一等原语 | OpenAI SDK, AutoGen | ✅ HandoffBuilder 独立组件 |
| 结构化 Report | CrewAI | ✅ report_schema + ReportValidator |
| Review 状态机 | CrewAI (approve/reject/revise/escalate) | ✅ ReviewStateMachine 6 states |
| Contract-as-boundary | LangGraph (subgraph isolation) | ✅ Contract 包含 scope/allowed_artifacts/out_of_scope |
| 渐进上下文装载 | OpenHands | ✅ 主 agent always-on, 子 agent 只装合同 refs |
| 升级条件显式化 | OpenAI SDK (tripwire), CrewAI | ✅ EscalationNotifier + 5 个触发条件 |

### 2.2 部分采纳但有差距

| 外部模式 | 来源 | 现状 | 差距 |
|----------|------|------|------|
| Subgraph namespace 隔离 | LangGraph | 骨架存在 (SubgraphMode) | 未实际运行，无 namespace scoping |
| 多源 Plugin 发现 | Semantic Kernel (native/OpenAPI/MCP) | Worker 有 LLM/HTTP 两种后端 | 无统一注册表、无动态发现、无 MCP worker |
| Handoff validator 独立 | OpenAI SDK (guardrails ≠ tripwires) | 无 | handoff 无独立 validator，依赖通用 review |
| Trace 端到端 | OpenAI SDK, LangGraph | 有 AuditLogger + TraceContext | **5 个断裂点 (Gap A-E)**，trace 在 writeback 阶段断裂 |

### 2.3 未采纳（已评估并决定暂缓）

| 外部模式 | 来源 | 决定 | 理由 |
|----------|------|------|------|
| Group Chat / Swarm 默认 | AutoGen | ❌ 不作默认 | 不适合 coding governance 主路径 |
| 并行子 agent | OMO (VibeCoding blog) | 📋 记录 | 有价值但超出当前 dogfood 阶段 |
| 独立 Milestone Reviewer 角色 | VibeCoding-Workflow | ❌ 不采纳 | 客户端不支持模式切换 |
| 编排模式运行时切换 | Semantic Kernel | 📋 记录 | 前置条件：先有 adapter-registry |

---

## 3. Trace Gap 状态（已验证）

来源：`design_docs/subagent-tracing-writeback-direction-analysis.md`

| Gap | 描述 | 当前状态 |
|-----|------|---------|
| **A** | trace_id 在 writeback 阶段断裂 | ✅ **已修复** — executor.py L531 传递 trace_id + audit_logger |
| **B** | Report → writeback plans 映射缺失 | ⚠️ 未修复 — 子 agent report.changed_artifacts 不参与 writeback |
| **C** | ExecutionResult 不保存 trace_id/delegation_mode | ✅ **已修复** — _result() 包含两字段 |
| **D** | 缺少 audit event_type | ✅ **已修复** — 10 个 event_type 完整覆盖 |
| **E** | Handoff 不在权威文档留审计痕迹 | ⚠️ 未修复 |

**结论**：原 P1（Gap A+C+D）已在之前 phase 中修复。剩余 Gap B 和 E 优先级较低。

---

## 4. 可行动建议（按优先级排序）

> 注：原 P1（Gap A+C+D Trace 连通）已在之前 phase 修复，以下重新排序。

### P1 — Worker Registry + Adapter 统一注册（原 P2 → 升为 P1）

**理由**：当前 Worker 有 3 种后端 (LLM/HTTP/Stub)，但无统一注册、发现、生命周期管理机制。Semantic Kernel 的 multi-source plugin 和 LangGraph 的 namespace scoping 都指向这个方向。这也是 BL-2 adapter-registry 的原定目标。

**范围**：
- Worker 注册表：namespace scoping + 按 capability 查询
- Adapter 抽象：统一 LLM/HTTP/MCP worker 的接口
- 动态发现：支持运行时注册/注销

**前置**：无（trace 已连通）

**来源**：Semantic Kernel multi-source plugin, LangGraph namespace

### P2 — Handoff Validator 独立化（原 P3 → 升为 P2）

**理由**：OpenAI SDK 明确区分 guardrails（输入保护）和 tripwires（失败快速退出），handoff 需要独立验证器而非复用通用 review。当前 handoff 没有独立 validator。

**范围**：
- Handoff acceptance schema 验证
- Handoff 前置条件检查（scope 清晰性、context 完整性）
- 独立于 ReviewStateMachine 的 handoff-specific guard

**前置**：P1

**来源**：OpenAI Agents SDK guardrails/tripwires 分离

### P3 — Report → Writeback Plans 自动映射（Gap B）

**理由**：子 agent report 中的 `changed_artifacts` 当前无法自动流入 writeback 管道，需要手工映射。

**前置**：dogfood 验证是否有实际需求

**来源**：Gap B

### P4 — Handoff 审计痕迹（Gap E）

**理由**：handoff 发生时不在权威文档留痕，长期追踪不可溯。优先级低于 P1-P3。

**来源**：Gap E

---

## 5. 对 BL-2 Adapter-Registry 的影响

BL-2 的原始目标是构建 adapter-registry。基于本次研究 + Gap A/C/D 已修复的事实：

1. **P1 即为 BL-2** — 将 adapter-registry 扩展为 Worker Registry + Adapter：
   - 从 Semantic Kernel 借鉴 multi-source plugin 发现
   - 从 LangGraph 借鉴 namespace scoping
   - 统一现有 3 种 Worker 后端到同一注册模型
2. **P2 可作为 P1 的下一个 slice** — handoff validator 是 adapter-registry 的自然延伸

**推荐切片顺序**：P1 → P2（每个一个 planning gate）

---

## 6. 与 VibeCoding-Workflow 的交叉借鉴

| VibeCoding 模式 | 借鉴点 | 当前状态 |
|-----------------|--------|---------|
| Orchestrator/Executor/Reviewer 三角色 | 我们用 Executor + Worker + ReviewStateMachine 覆盖 | ✅ 已覆盖 |
| Run Budget（200 tool calls 上限） | 我们用 AD-2 tool-call-budget | ✅ 已采纳 |
| Anti-Drift 8 条 → AD-1~AD-5 | 覆盖率 4/8 直接 + 4/8 已有等效 | ✅ 已采纳 |
| OMO 并行子 agent | SubgraphMode 骨架存在 | 📋 记录 |

---

## 开放问题

1. Worker Registry 的 namespace 设计是否需要支持多层级（project → pack → instance），还是先做扁平注册？
   - **决定**：先做扁平注册。多层级 namespace 记录为 future item。
2. Handoff validator 是否要求 pack 级可插拔，还是先内建固定逻辑？
3. 是否需要支持 MCP Worker（通过 MCP 协议调用远程 worker），还是先只统一现有 LLM/HTTP/Stub？
   - **决定**：P1 先统一现有 3 种。MCP Worker 记录为 future item。

## Future Items（已确认需要但不在当前切片）

- **FR-MCP-Worker**：MCP Worker 后端 — 通过 MCP 协议调用远程 worker，扩展 WorkerAdapter 注册
- **FR-NS-Hierarchy**：多层级 namespace — 支持 project → pack → instance 层级查询与隔离
