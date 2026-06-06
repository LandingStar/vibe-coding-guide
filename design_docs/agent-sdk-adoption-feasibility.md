# Agent SDK Adoption Feasibility

> Date: 2026-06-07
> Status: investigation / recommendation

## Context

本文件接续 `agent-cluster-scheduling-and-isolation-investigation.md`，专门回答一个更窄的问题：

现有 SDK / framework 是否可以被本项目直接使用，或作为 agent 集群调度与隔离系统的底座。

这里的判断对象不是“功能是否丰富”，而是：

1. 是否会侵入本项目的 doc-loop authority。
2. 是否能保持 scheduler state 作为权威状态源。
3. 是否支持 line-level context isolation。
4. 是否能与 `EditScopeLease` / `SandboxProfile` / merge gate 对齐。
5. 是否适合先做本地 MVP，还是应保留为后续 provider。

## Overall Judgment

不建议把任何一个现有 SDK 直接提升为本项目的核心调度器。

推荐策略是：

1. 本项目自有 `TaskGraphScheduler` 继续作为权威调度模型。
2. 外部 SDK 只进入可插拔 provider 层：
   - `AgentRunProvider`
   - `SandboxProvider`
   - `DurableSchedulerBackend`
   - `TraceExportProvider`
3. 第一阶段只实现本地 fake-run / stub-run 闭环。
4. 第二阶段用 1-2 个 SDK 做薄 adapter spike，而不是先绑定某个生态。

原因：这些 SDK 各自解决的问题不同。OpenAI Agents SDK / AutoGen / ADK / LangChain 更偏 agent loop 和 orchestration pattern；Temporal 更偏 durable workflow；E2B / Daytona / OpenHands 更偏 sandbox runtime。没有一个天然承担本项目的 doc-loop governance、authority docs、edit lease、review/write-back merge gate。

## Candidate Matrix

| Candidate | Direct Use | Base-On / Adapter Use | Core Risk | Recommendation |
|---|---:|---:|---|---|
| OpenAI Agents SDK | Medium | High | agent loop/session/tracing 可能绕过本项目调度权威 | 做 `AgentRunProvider` spike，不做 scheduler core |
| Temporal Python SDK | Low now / Medium later | High | 引入 service、worker、deterministic workflow 约束 | 设计上借鉴，后续做 durable backend |
| E2B SDK | Medium | High | 外部云依赖、API key、成本、数据边界 | 做 `SandboxProvider` spike |
| Daytona SDK | Medium | High | 外部云依赖、数据驻留、供应商耦合 | 作为 E2B 的同类备选 spike |
| OpenHands | Low | Medium | 更像完整 coding agent/runtime，不是轻量库 | 作为 external worker 或 sandbox taxonomy 参考 |
| LangChain / LangGraph | Medium | Medium | 易把 workflow state 与本项目 scheduler state 混淆 | 只做 agent workflow provider 研究 |
| Google ADK | Low-Medium | Medium | 生态与部署模型偏 Google agent platform | 借鉴 graph workflow/context，暂不接入 |
| AutoGen AgentChat | Low | Medium | group chat 默认共享上下文，与线隔离冲突 | 只做 team/swarm 行为研究 |
| Ray | Low | Medium | 解决资源调度，不解决 governance/writeback | 后续资源 executor 备选 |

## OpenAI Agents SDK

### What It Gives

OpenAI Agents SDK 提供较少 primitives：agents、agents-as-tools / handoffs、guardrails，并带有 agent loop、function tools、MCP server tool calling、sessions、human-in-the-loop、tracing 和 sandbox agents。

官方文档还明确：当你希望自己掌控 loop、tool dispatch 和 state handling 时，可以直接用 Responses API；当希望 runtime 管理 turns、tool execution、guardrails、handoffs 或 sessions 时，使用 Agents SDK 更合适。

### Fit

适合：

1. 作为 `AgentRunProvider`：执行单个 bounded worker task。
2. 作为 `TraceExportProvider` 的参考：其 tracing 覆盖 LLM generations、tool calls、handoffs、guardrails，也支持自定义 trace processors。
3. 作为 `ContextScope` 的参考：sessions 支持不同 session 维护不同历史，也支持不同 agent 共享同一 session。
4. 作为未来 sandbox agent provider 的候选：其 sandbox reference 有 filesystem、shell、permissions、Docker sandbox 等形态。

不适合：

1. 不应直接作为 `TaskGraphScheduler`。
2. 不应让 SDK session 直接成为本项目 line context authority。
3. 不应默认启用共享 session；共享 session 会削弱 line-level context isolation。
4. 其 tracing 默认可能包含敏感输入/输出；必须由本项目 secret / redaction policy 覆盖。

### Adoption Shape

建议做一个很薄的 adapter：

```text
TaskGraphScheduler
  -> AgentRunProvider.run(task, context_scope, sandbox_profile)
       -> OpenAI Agents SDK Runner
       -> SubagentReport / artifact_payloads / trace_refs
  -> existing merge / review / write-back
```

第一轮 spike 只验证：

1. 单 task、无共享 session。
2. 输入只来自 `ContextScope.required_refs` 的摘要。
3. 输出必须归一化为 `SubagentReport`。
4. trace 只记录引用，不把 trace dashboard 当本项目 authority。

Source:

- https://openai.github.io/openai-agents-python/
- https://openai.github.io/openai-agents-python/sessions/
- https://openai.github.io/openai-agents-python/tracing/
- https://openai.github.io/openai-agents-python/ref/sandbox/permissions/

## Temporal Python SDK

### What It Gives

Temporal Python SDK 提供 Workflows、Activities、Workers、Client、Child Workflows、Cancellation、Timeouts、Schedules、Timers、Versioning 等 primitives。

它最适合解决：

1. 调度状态持久化。
2. crash/restart 后恢复。
3. retry / timeout / cancellation。
4. long-running workflow。
5. parent-child workflow lifecycle。

### Fit

适合：

1. 作为后续 `DurableSchedulerBackend`。
2. 作为本项目 scheduler state / event history 的设计参考。
3. 作为未来长任务或跨进程 worker 的可靠执行层。

不适合：

1. 不适合作为 MVP 第一刀。
2. 会引入 Temporal service、task queue、worker process、deterministic workflow 编写约束。
3. 它不知道本项目的 authority docs、edit lease、review gate。

### Adoption Shape

短期只借鉴，不直接接入：

```text
Local Scheduler State
  ~= Temporal-like event history
  ~= task state transition log
  ~= retry/cancel/timeout vocabulary
```

中期可做 backend：

```text
TaskGraphSchedulerBackend
  - local_json
  - sqlite
  - temporal
```

Source:

- https://docs.temporal.io/develop/python

## E2B SDK

### What It Gives

E2B 提供 isolated sandboxes，SDK 可启动并管理 sandbox；文档中直接展示了创建 sandbox、运行命令 / code、文件系统、网络、模板、生命周期、metadata、OTel telemetry、MCP gateway 等能力。

### Fit

适合：

1. 作为 `SandboxProvider` 的强候选。
2. 用于高风险 agent：运行代码、安装依赖、联网、处理未知仓库。
3. 用于 remote isolated workspace，而不是共享本地工作区。

不适合：

1. 不应作为调度器。
2. 不应直接暴露给 worker 绕过 `EditScopeLease`。
3. 不能默认把完整 workspace/secrets 上传或挂入。

### Adoption Shape

建议后续 spike：

```text
SandboxProfile(remote-vm, provider=e2b)
  -> create sandbox
  -> upload lease-scoped files only
  -> run command / agent
  -> download patch/report
  -> destroy or persist per policy
```

关键验收：

1. 不上传 `.codex` secret/log。
2. 不上传未授权文件。
3. 输出必须是 patch/report。
4. 网络策略和 API key policy 明确。

Source:

- https://e2b.dev/docs
- https://e2b.dev/docs/quickstart

## Daytona SDK

### What It Gives

Daytona SDK 可创建 sandbox，并在 sandbox 中执行代码/命令。官方 quickstart 覆盖 Python、TypeScript、Ruby、Go、Java 和 API/CLI。

### Fit

与 E2B 类似，适合作为 `SandboxProvider` 备选，尤其用于比较：

1. sandbox 创建/销毁 API。
2. 文件同步和 patch 回收。
3. 网络/凭据/成本模型。
4. 本地开发体验。

不适合：

1. 不应作为调度器。
2. 不应成为唯一 remote sandbox abstraction。

### Adoption Shape

与 E2B 共用同一个 provider contract：

```text
SandboxProvider
  - e2b
  - daytona
  - docker-local
```

Source:

- https://www.daytona.io/docs/

## OpenHands

### What It Gives

OpenHands 是完整 coding agent / runtime 方向，不只是轻量 SDK。其 sandbox 文档明确区分 Docker sandbox、Process sandbox 和 Remote sandbox，并指出 process sandbox 快但没有容器隔离。

### Fit

适合：

1. 借鉴 sandbox provider taxonomy。
2. 作为外部 coding worker 的候选。
3. 研究真实 coding agent 如何组织 command/file/server execution。

不适合：

1. 不适合直接嵌入为本项目核心。
2. 它本身会带一套 agent UX/runtime，容易与本项目 governance core 重叠。

### Adoption Shape

若接入，应作为外部 worker：

```text
WorkerBackend(openhands)
  -> receives narrow contract
  -> runs in its own sandbox
  -> returns report/patch only
```

Source:

- https://docs.openhands.dev/openhands/usage/sandboxes/overview

## LangChain / LangGraph

### What It Gives

LangChain multi-agent 文档明确列出 subagents、handoffs、skills、router、custom workflow，并把 context engineering 放在 multi-agent design 中心。它适合研究 pattern 和 context 裁剪。

### Fit

适合：

1. 作为 `AgentRunProvider` 或 `WorkflowProvider` 的备选。
2. 用于构造单个 task 内部的小型 agent workflow。
3. 借鉴 context engineering。

不适合：

1. 不应让 LangGraph state 成为本项目 scheduler state。
2. 不应把 custom workflow 与本项目 `TaskGraphScheduler` 混成一层。

### Adoption Shape

```text
TaskGraphScheduler task
  -> LangGraph-backed WorkerBackend
  -> returns SubagentReport
```

Source:

- https://docs.langchain.com/oss/python/langchain/multi-agent

## Google ADK

### What It Gives

ADK 是多语言 agent framework，提供 graph workflows、multi-agent workflows、template workflows、agent runtime、observability、sessions/memory、A2A Protocol 等。

### Fit

适合：

1. 借鉴 graph workflow 和 context management。
2. 研究 A2A / agent runtime 作为跨 agent 通信参考。

不适合：

1. 当前不适合作为本项目默认依赖。
2. 生态、部署和模型默认路径偏 Google/ADK 平台，不应先绑定。

### Adoption Shape

短期只研究，不接入。若后续要接入，应与 LangGraph 类似，只作为 worker-side workflow provider。

Source:

- https://adk.dev/
- https://adk.dev/workflows/

## AutoGen AgentChat

### What It Gives

AutoGen AgentChat 支持 Teams，包含 `RoundRobinGroupChat`、`SelectorGroupChat`、`MagenticOneGroupChat`、`Swarm` 等 preset。官方文档也提醒 team 适合复杂协作，但比单 agent 需要更多 scaffolding。

### Fit

适合：

1. 研究 team/swarm lifecycle。
2. 研究 termination conditions。
3. 作为“不要默认共享上下文”的反面参考。

不适合：

1. 默认 group chat 共享上下文，与本项目 line-level context isolation 冲突。
2. 不解决 edit lease、merge barrier、doc authority。

### Adoption Shape

不建议第一阶段接入。未来若接入，也只能作为实验性 `CollaborativeWorkerBackend`，并且必须禁用或封装共享上下文。

Source:

- https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html

## Recommended Research Spikes

### Spike 1: OpenAI Agents SDK As AgentRunProvider

Goal:

1. 验证单 task -> SDK runner -> SubagentReport 的映射。
2. 验证 session isolation：每条 line 一个 session，默认不共享。
3. 验证 tracing redaction：敏感数据默认不进入外部 trace。

Decision after spike:

1. 是否允许作为默认 LLM worker upgrade path。
2. 是否只作为 optional provider。

### Spike 2: E2B Or Daytona As SandboxProvider

Goal:

1. 上传一个 lease-scoped temp workspace。
2. 执行简单命令。
3. 回收 patch/report。
4. 确认 secrets / `.codex` / unrelated files 不出边界。

Decision after spike:

1. `SandboxProfile(remote-vm)` 的 provider contract 是否足够。
2. E2B 与 Daytona 谁更适合优先接入。

### Spike 3: Temporal Shape Without Temporal Dependency

Goal:

1. 用本地 JSON/SQLite 模拟 Temporal-like event history。
2. 固定 task transition、retry、timeout、cancellation vocabulary。
3. 不引入 Temporal server。

Decision after spike:

1. 本地 scheduler model 是否足以未来映射到 Temporal backend。

## Final Recommendation

当前最合理路径：

1. 先实现本项目自有 `TaskGraphScheduler` 和本地 event history。
2. 把 SDK 接入点固定为 provider interface，而不是核心依赖。
3. 第一批实际 spike 只选两个：
   - OpenAI Agents SDK: `AgentRunProvider`
   - E2B or Daytona: `SandboxProvider`
4. Temporal 先只借鉴概念，不接入。
5. AutoGen / ADK / LangChain 先作为 pattern research，不作为 MVP dependency。

这样做的好处是：我们可以借到 SDK 的成熟执行能力，但不让任何外部 SDK 接管本项目最核心的调度权威、文档闭环和 merge/write-back 边界。

