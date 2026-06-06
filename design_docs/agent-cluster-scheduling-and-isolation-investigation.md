# Agent Cluster Scheduling And Isolation Investigation

> Date: 2026-06-06
> Status: investigation / recommendation

## Context

本调查承接当前 Local Work Trajectory 多线 UI 绑定后的下一层问题：

1. 多线图已经能表达局部工作中的线、节点、开线、merge 和依赖。
2. 但当前多线图仍只是工作轨迹展示，不是 agent 集群调度系统。
3. 在进入真实多线 agent 之前，需要先让调度系统具备最小功能，并明确上下文隔离、可编辑区域隔离和执行隔离的边界。

本文件只做调研和架构建议，不进入实现。

## Current Project Baseline

当前仓库已经有几层可复用基础：

1. `docs/host-interaction-model.md` 已固定四层模型：Core Contract、Portable Runtime、Interaction Adapter、Host UX。调度器应属于 Portable Runtime 或其上方的 orchestration layer，不应落在 VS Code UI 或 Codex adapter 私有层。
2. `docs/subagent-management.md` 固定默认协作模式为 `supervisor-worker`，`team` / `swarm` 不是默认主路径。
3. `docs/subagent-schemas.md` 已允许 parent-side companion objects：`TaskGroup`、`ParallelChildTask`、`ChildExecutionRecord`、`MergeBarrierOutcome`、`GroupedReviewOutcome`。
4. `src/collaboration/subgraph_mode.py` 已有 namespace、state snapshot、delta merge 的逻辑隔离模型。
5. `design_docs/subagent-context-isolation-evaluation.md` 已指出当前主要是合同级、prompt 级和 delta merge 级隔离；它不是 OS / filesystem 级强制沙箱。

当前关键缺口：

1. 没有独立 scheduler lifecycle。
2. 没有可运行队列、依赖唤醒、取消、暂停、重试和资源限流。
3. `allowed_artifacts` / shared-review zone 能表达写入边界，但不能阻止一个真实进程或 agent 在共享工作区里越界编辑。
4. 没有按 agent 风险分档的 sandbox profile。

## Existing Solution Scan

### LangChain / LangGraph

LangChain 当前 multi-agent 文档把 multi-agent pattern 明确拆成 subagents、handoffs、skills、router 和 custom workflow，并强调 multi-agent design 的中心是 context engineering，即决定每个 agent 能看到什么信息。它对本项目最有价值的是：

1. Subagents / router 这类 centralized control 模式比 peer-to-peer chat 更贴近本项目的 supervisor-managed governance。
2. Handoffs 适合表达控制权转移，但不应成为默认的任务调度语义。
3. Custom workflow 可承接 deterministic logic + agentic behavior，说明调度器应先有任务图/状态图，而不是只靠自然语言协商。
4. context engineering 与本项目的 line-level context scope、required refs 和 redaction policy 高度同构。

不适合直接照搬的部分：

1. LangGraph 不是文件编辑权限系统。
2. 它的 state isolation 不等于 workspace / shell / secret / network isolation。

Source: https://docs.langchain.com/oss/python/langchain/multi-agent

### Google ADK

ADK 2.0 文档把 agent workflow 分为 graph workflows、dynamic workflows、collaborative workflows 和 template workflows，其中 template workflow 包括 sequence、loop、parallel。它对本项目的启发是：

1. 多 agent 不一定先做 swarm；可以先做结构化 workflow。
2. 固定模板和图式 workflow 可以并存。
3. workflow 的收益包括 predictable flow、reliability、responsibility separation、limited data context。

不适合直接照搬的部分：

1. ADK 的 workflow 关注 agent application 组织，不解决本项目的 doc-loop authority、allowed artifacts、write-back gate。
2. 它不是 coding workspace 的强隔离模型。

Source: https://adk.dev/workflows/

### AutoGen AgentChat

AutoGen 的 Teams 明确提供 `RoundRobinGroupChat`、`SelectorGroupChat`、`MagenticOneGroupChat` 和 `Swarm` 等 team preset，并提供 reset、stop、termination condition 等生命周期控制。

对本项目的参考价值：

1. 如果 `team` / `swarm` 进入实现，必须是 runtime primitive，而不只是 mode 字符串。
2. team lifecycle 至少需要 run、stream/observe、reset、stop/resume、termination condition。
3. Swarm 的 handoff pattern 可作为“控制权转移”的参考，但不是默认调度模型。

不适合直接照搬的部分：

1. AutoGen group chat 默认强调共享消息上下文；这与本项目强调线/工作切片的上下文隔离存在张力。
2. 它更像协作对话框架，不是编辑权、文件锁、merge barrier、sandbox 体系。

Sources:

- https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html
- https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html

### OpenAI Agents SDK

Agents SDK 提供 Agent / Runner / tools / guardrails / handoffs / sessions / tracing。它对本项目的参考价值：

1. Handoff 可以作为 agent specialization 和 authority transfer 的显式事件。
2. Sessions 说明“上下文持久化”应是可配置项，而不是所有 agent 默认共享同一历史。
3. Tracing 默认覆盖 LLM generations、tool calls、handoffs、guardrails 等事件，这与本项目的 audit / Local Work Trajectory 很契合。
4. Sandbox agent API 中出现 permissions、filesystem、shell、Docker sandbox 等形态，可作为未来薄适配参考。

不适合直接照搬的部分：

1. SDK 不是项目调度器；它不会替本项目判断 doc authority、planning-gate、allowed_artifacts 和 write-back。
2. session sharing 如果不受控，会削弱本项目想要的 line-level context isolation。

Sources:

- https://openai.github.io/openai-agents-python/handoffs/
- https://openai.github.io/openai-agents-python/sessions/
- https://openai.github.io/openai-agents-python/tracing/
- https://openai.github.io/openai-agents-python/ref/sandbox/permissions/

### Temporal

Temporal 的核心价值是 durable workflow：workflow execution 有 event history，可在 crash、network failure 或长时间运行后恢复；外部副作用应放在 Activity，workflow replay 要保持 deterministic。Python SDK 支持 child workflow、parent close policy、retry / error handling。

对本项目的参考价值：

1. 调度状态应持久化，event history 是恢复和审计的核心。
2. 子任务可以建模为 child workflow；父任务负责关闭策略、取消、等待和 join。
3. retries、timeouts、failure classification 应是一等调度语义。

不适合第一阶段直接接入的部分：

1. Temporal 是重型依赖，会引入独立 service、worker、task queue 和 deterministic workflow 约束。
2. 当前项目更需要先证明本地 agent task graph / lease / sandbox profile 的最小语义。

Sources:

- https://docs.temporal.io/workflows
- https://docs.temporal.io/develop/python/workflows/child-workflows
- https://docs.temporal.io/develop/python/best-practices/error-handling

### Ray

Ray Core 提供 tasks / actors 和资源调度，task 或 actor 可声明 CPU、GPU、自定义资源。它适合大量并行计算或长期 actor。

对本项目的参考价值：

1. `ResourceRequirement` 应作为 scheduler admission 的一部分。
2. actor 模型可类比长期 agent session，但不应作为第一阶段默认。

不适合直接照搬的部分：

1. Ray 解决的是分布式执行和资源调度，不解决本项目的 governance、doc authority、edit lease 和 merge review。

Source: https://docs.ray.io/en/latest/ray-core/scheduling/resources.html

### Kubernetes Jobs

Kubernetes Job 提供 completions、parallelism、indexed job、backoffLimit、activeDeadlineSeconds、TTL cleanup 等成熟批处理语义。

对本项目的参考价值：

1. `.spec.parallelism = 0` 可以表达暂停，parallelism 可以表达并发上限。
2. completion count / indexed tasks 可以表达固定子任务集合。
3. backoff / deadline / terminal conditions 是调度器最小状态机应学习的对象。

不适合第一阶段直接接入的部分：

1. K8s 是 process/pod 层调度，不知道 agent context、allowed_artifacts、review gate。
2. 本地单机 dogfood 阶段接入 K8s 过重。

Source: https://kubernetes.io/docs/concepts/workloads/controllers/job/

### Docker / OpenHands / E2B / Daytona / Firecracker

这些方案覆盖执行隔离层：

1. Docker 提供 namespace、cgroup、seccomp、AppArmor 等隔离/约束 primitives。
2. OpenHands 把执行环境明确称为 sandbox，支持 Docker sandbox、process sandbox、remote sandbox；其中 process sandbox 明确更快但不安全。
3. E2B 提供云端 isolated sandbox，并建议可按 LLM/user/agent session 运行多个 sandbox。
4. Daytona 提供面向 AI agent 的 sandbox，强调独立 kernel、filesystem、network stack、vCPU/RAM/disk。
5. Firecracker microVM 提供比普通容器更强的 VM 边界，但集成复杂度更高。

对本项目的参考价值：

1. 真实 agent 集群必须把“上下文隔离”和“执行隔离”分开建模。
2. 低风险 agent 可使用 process / shared workspace + patch-only merge；高风险 agent 必须进入 container / remote VM / microVM 档位。
3. secret policy、network policy、mount policy 是 sandbox profile 的一部分，不应散落在 prompt 中。

Sources:

- https://docs.docker.com/engine/security/
- https://docs.docker.com/engine/security/seccomp/
- https://docs.docker.com/engine/security/apparmor/
- https://docs.openhands.dev/usage/runtimes/overview
- https://docs.openhands.dev/overview/faqs
- https://e2b.dev/docs/sdk-reference/code-interpreter-python-sdk/v2.3.0/sandbox
- https://e2b.dev/docs/quickstart/migrating-from-v0
- https://www.daytona.io/docs/
- https://github.com/firecracker-microvm/firecracker

## Design Implications For This Project

### 1. Do Not Replace The Platform With A Multi-Agent Chat Framework

AutoGen / Swarm / collaborative agents 都有价值，但当前项目的主轴是 doc-loop governance、可审计 write-back、authority docs 和 host-neutral runtime。直接把 team chat 框架放进核心，会让共享上下文、自由发言、自然语言 handoff 抢走当前已经建立的 contract / report / review 边界。

建议：agent framework 只能作为某个 WorkerBackend / Host Adapter 的可选实现，不应成为 Core Contract。

### 2. Scheduler Should Be A Small Runtime Layer

建议新增一个薄调度层，暂称 `TaskGraphScheduler`。它不替代 PDP / PEP / Review / WriteBack，只负责：

1. 读取一个工作图。
2. 判断哪些任务 ready。
3. 申请 edit lease 和 sandbox profile。
4. 触发 worker invocation。
5. 收集 report / patch / delta。
6. 把结果送回现有 merge / review / write-back 路径。
7. 写出 trace 和 Local Work Trajectory event。

### 3. Local Work Trajectory Should Remain Projection, Not Authority

Local Work Trajectory UI 适合展示：

1. lane / event / relation。
2. open lane / merge / dependency。
3. 每个局部工作上下文的推进情况。

但 scheduler 的 authority 不应由 UI artifact 反推。正确方向是：

1. Scheduler state 是权威运行状态。
2. Local Work Trajectory 是 scheduler / agent lifecycle 的可视化投影。
3. 用户可通过 UI 看懂状态，但 UI 默认不直接改写 scheduler graph，除非后续专门做控制面。

### 4. Context Isolation And Edit Isolation Need Separate Objects

建议拆成两个 contract：

1. `ContextScope`
   - line_id / context_id
   - required_refs
   - visible_docs
   - prior_summary
   - session_policy: `stateless` / `summarized` / `persistent`
   - redaction_policy
2. `EditScopeLease`
   - allowed_artifacts
   - denied_artifacts
   - lease_owner
   - lease_mode: `read` / `write` / `review-zone`
   - conflict_policy
   - expires_at

这样可以表达用户前面提出的关键点：一条线不一定等于一个真实 subagent，但一定对应一套相对独立的上下文；同时，能不能编辑某些文件是另一层问题。

### 5. Execution Isolation Needs A SandboxProfile

建议引入 `SandboxProfile`，先只做接口和最低档位：

1. `none`
   - 只允许 dry-run / no-write / inspection。
2. `shared-process`
   - 当前进程执行；只适合低风险、无 shell 或无写入任务。
3. `git-worktree`
   - 独立 worktree + patch export；可减少直接覆盖主工作区，但不是安全沙箱。
4. `docker`
   - 容器执行；默认禁用敏感 mount，按 lease 挂载必要路径。
5. `remote-vm`
   - E2B / Daytona / Firecracker-like 后端；用于 untrusted code、联网、依赖安装、高权限命令。

第一阶段可以只实现 `shared-process` 的元数据与 `git-worktree` / `docker` 的接口占位，不需要直接接云端 sandbox。

## Recommended MVP Slice

建议下一步不要直接做“大规模 agent 集群”，而是做一个最小可跑的 scheduler skeleton：

### Scope

1. 新增 scheduler model：
   - `ScheduledTask`
   - `TaskDependency`
   - `SchedulerState`
   - `TaskRunRecord`
   - `ContextScope`
   - `EditScopeLease`
   - `SandboxProfile`
2. 支持任务状态：
   - `proposed`
   - `ready`
   - `running`
   - `waiting`
   - `review_required`
   - `merged`
   - `blocked`
   - `cancelled`
   - `complete`
3. 支持最小调度规则：
   - dependencies 全部满足 -> ready
   - edit lease 不冲突 -> admissible
   - sandbox profile 可用 -> runnable
   - worker 返回 report -> merge gate
4. 支持最小执行后投影：
   - scheduler run record 写入 audit
   - scheduler event 投影到 Local Work Trajectory
   - 不从 Local Work Trajectory 反推调度状态

### First Test Shape

使用 stub worker 或 controlled fake worker 验证：

1. 创建 1 个 parent goal。
2. 创建 3 个 tasks：
   - A: 读取需求并生成设计摘要。
   - B: 在 A 后生成测试草案。
   - C: 在 A 后生成实现草案。
3. B 和 C 的 `allowed_artifacts` 不重叠时可并发 ready。
4. 若 B 和 C 申请同一个 `allowed_artifacts`，scheduler 拒绝并给出 conflict reason。
5. 所有结果只以 report / patch / delta 形式返回父端。
6. Local Work Trajectory 能显示开线、依赖和 merge，但调度状态来自 scheduler state。

### Explicit Non-Goals

1. 不实现真实 swarm / peer-to-peer group chat。
2. 不直接接 Temporal / Ray / K8s。
3. 不接云端 sandbox。
4. 不把 VS Code UI 作为 scheduler authority。
5. 不允许 worker 直接维护 authority docs / handoff / global phase map，除非 `EditScopeLease` 明确授权且父端 merge gate 通过。

## Recommendation

我建议采用“轻量本地 scheduler + 可插拔 sandbox profile + 现有 governance merge gate”的路线：

1. 第一阶段先做 `TaskGraphScheduler` 本地模型和 fake execution loop。
2. 第一阶段就把 `ContextScope`、`EditScopeLease`、`SandboxProfile` 作为对象固定下来，避免后续再返工。
3. 第一阶段不要引入 Temporal；但 scheduler event history 和 task state 设计应向 Temporal 的 durable workflow 思路靠拢，方便未来迁移。
4. 第一阶段不要引入 AutoGen / Swarm 作为核心；如果后续需要，它们应作为 worker backend 或 collaborative worker implementation。
5. 对能够写文件、跑 shell、安装依赖、访问网络或接触 secrets 的高风险 agent，后续必须进入至少 `docker` 档位；更高风险则需要 remote VM / microVM。

换句话说，本项目后续真正需要的不是“多 agent 聊天能力”，而是：

1. 可审计任务图。
2. 可证明的上下文边界。
3. 可执行的编辑租约。
4. 可分档的执行沙箱。
5. 父端控制的 merge / review / write-back。

这与当前 doc-loop 平台方向最兼容，也最不容易把已有治理成果弄散。
