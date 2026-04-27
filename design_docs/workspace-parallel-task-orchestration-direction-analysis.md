# 方向分析 — 同工作区任务并行编排（Workspace Parallel Task Orchestration）

## 背景

当前平台已经正式承认子 agent、handoff、subgraph、team、swarm 等协作概念，但运行时的默认口径仍然是 `supervisor-worker`。这在单切片 delegation 上是足够的；一旦进入“同工作区多个任务并行推进”或“分发式开发”场景，就会立刻暴露出一个更底层的问题：

- 平台并不是单纯“还没加并行执行”；
- 平台当前把 delegation 建模成了**单合同、单执行、单回报、单次 review**；
- 因此“多个任务同时跑”缺少可落脚的执行原语、合并点与治理边界。

用户这次提出的诉求，实质上不是要一个局部 async patch，而是要回答三个问题：

1. 当前为什么不支持同工作区多任务并行
2. 行业内已有哪几类成熟模式
3. 平台后续应该先补哪一层，而不是直接把 `team/swarm` 写成实现

本文只做方向分析，**不进入实现**。

## 现状结论

### 结论 1：当前运行时仍是单 delegation 语义

当前最直接的代码证据有四层：

1. `src/pdp/delegation_resolver.py`
   - `_select_mode()` 只会落到 `supervisor-worker`、`handoff`、`subgraph`
   - `team/swarm` 没有可被选中的运行时路径
2. `src/collaboration/modes.py`
   - `CollaborationMode` 只有 `WORKER`、`HANDOFF`、`SUBGRAPH`
   - `TEAM`、`SWARM` 仍是 reserved comments，而不是 executor protocol
3. `src/pep/executor.py`
   - `_execute_delegation()` 只构建一个 contract，并分派给一个 mode executor
   - `_execute_worker_mode()` 直接执行一次 `worker.execute(contract)`
   - `_execute_handoff_mode()` 与 `_execute_subgraph_mode()` 也都是单 child 执行
4. `src/collaboration/subgraph_mode.py`
   - 只有单 subgraph context、单 delta capture、单次 merge_result
   - 还没有 fan-out / barrier / multi-child merge 的结构

换句话说，当前运行时支持的是“选一种协作模式去跑一个子流程”，不支持“同时创建多个子流程并协调它们的依赖、状态、写集与验收”。

### 结论 2：文档 / schema 已先行，但 runtime 没跟上

当前仓库已经有明显的“概念先行、执行未跟上”现象：

- `docs/subagent-management.md` 与 `docs/core-model.md` 已经承认 `team/swarm/subgraph` 是平台概念
- `docs/specs/subagent-contract.schema.json` 的 `mode` 已允许 `worker/handoff/team/swarm/subgraph`
- `src/subagent/contract_factory.py` 也保留了 `team/swarm` 的 mode 映射

但与此同时：

- `delegation_resolver` 不会把决策真正选到 `team/swarm`
- `Executor` 也没有多合同、多 worker、多结果的执行模型
- `Review State Machine`、write-back、handoff 持久化仍按单结果假设工作

这说明当前真正的缺口不是“有没有把 enum 写出来”，而是“有没有把并行协作变成一等 runtime primitive”。

### 结论 3：同工作区并行的关键缺口不是线程，而是治理原语

若平台要支持“同工作区多任务并行”，至少还缺以下能力：

1. 任务图原语
   - 子任务 identity
   - dependency / blocked-by / barrier
   - sequential / parallel / conditional progression
2. 调度与准入
   - 谁可以并发启动
   - 哪些任务必须串行
   - 如何表达限流、取消、暂停、恢复
3. 状态与命名空间
   - child context namespace
   - checkpoint / persistence policy
   - 同一子图是否允许并行重入
4. 写集与冲突控制
   - `allowed_artifacts` 需要从声明升级为运行时硬约束
   - 需要 disjoint write set、lock 或 merge barrier
   - 需要把冲突分成自动合并、人工 review、阻塞三类
5. 多 child 的 review / write-back 汇聚
   - 单 report -> 多 child report 聚合
   - 单 handoff -> task-group outcome / escalation bundle
   - 单次 review -> grouped review / partial approve / join gate
6. tracing / audit / write-back 贯通
   - 当前 tracing 与 write-back 已有断裂风险
   - 并行后如果没有 parent-child lineage 与 merge event，审计会更弱

因此，当前“不支持并行”的根因是：**平台还没有定义 parallel-safe governance contract**。

## 为什么现有基础还不够

当前最接近并行基础的是 `subgraph`，但它只解决了“隔离子流程”的一半问题。

它已经具备的价值：

- 可以创建独立 namespace 的子上下文
- 可以捕获 delta 并受控合并回 parent
- 语义上天然比 handoff 更接近未来 fan-out/fan-in

但它还不具备：

- 同时启动多个 child subgraph 的调度面
- 多 child 依赖图
- 多 child merge barrier
- 同工作区写集冲突的硬校验
- 针对并行 child 的统一 review / escalation 聚合

所以，`subgraph` 是最有希望的起点，但不是“已经支持并行”。

## 行业可参考模式

### 参照 A — LangGraph Subgraphs：把“分布式开发”建模为稳定子图接口

最有价值的点不是它支持 subgraph，而是它明确把下面两件事写成了规则：

1. **Subgraph interface first**
   - 父图与子图通过输入/输出 schema 交互
   - 这非常适合 distributed development：只要接口稳定，不同团队可以独立推进子图
2. **Persistence mode 决定能否并行**
   - `per-invocation` 是多 agent one-off delegation 的推荐默认值
   - 它支持 parallel calls，同时保持各次调用隔离
   - `per-thread` 适合需要累积记忆的子 agent，但不支持 parallel tool calls，否则会发生 checkpoint namespace conflict

这给本项目一个非常直接的教训：

- 如果要先做并行，第一步应优先选 **per-invocation isolated child tasks**；
- 不应该一开始就把“长期共享状态的子 agent”放进并行范围；
- persistence / namespace policy 不是后补细节，而是并行语义的核心边界。

### 参照 B — AutoGen Teams：team 必须是显式运行时 primitive

AutoGen 的价值在于它没有把 team 视为 prompt pattern，而是明确做成 runtime primitive：

- `RoundRobinGroupChat`
- `SelectorGroupChat`
- `MagenticOneGroupChat`
- `Swarm`

并且它把下面这些生命周期操作都放进 runtime：

- run / stream
- reset
- stop
- resume
- abort
- termination conditions

这说明如果本项目未来真的要把 `team/swarm` 做成一等能力，那么最低要求不是新增 mode 字符串，而是：

- team lifecycle
- team state
- external termination
- result aggregation

都必须由 runtime 接手，而不是留给 prompt 约定。

### 参照 C — CrewAI：manager-worker 之外还需要 flow persistence 与结构化人审

CrewAI 给本项目最重要的启发不是“多 agent 能协作”，而是：

- manager 要负责 assignment、validation、progression
- flow 要有持久状态
- human feedback 不应只是自然语言，而应产出结构化 outcome

这与本项目已有的 `Review State Machine` 很接近，但当前平台还停留在“一个 child result 进入一次 review”。如果未来要并行，review 需要升级为：

- child-level review
- group-level join review
- structured partial completion / blocked / escalate outcome

### 参照 D — Multica：workflow primitives 很快会成为强需求

Multica 的公开 issue / roadmap 信号说明，一旦产品进入真实 agent orchestration 场景，用户会很快要求：

- issue dependencies
- parallel / sequential execution
- agent team
- auto wake-on-resolved

这说明“任务并行”不是边角功能，而是从单 agent 工具走向协作平台的自然拐点。

对本项目的意义是：

- 现在就该把 parallel task orchestration 当成架构问题
- 但不应被需求热度推着直接写大而全 runtime

### 参照 E — OpenHands / Claude Managed Agents：共享工作区可以存在，但必须把上下文、权限、事件拆开

这些系统虽然没有直接给出本项目可照搬的并行 runtime，但提供了两个稳定信号：

1. 共享文件系统并不等于共享上下文
2. permissions / session events / on-demand context loading 必须与 agent 生命周期绑定

这与本项目现有的 `allowed_artifacts`、pack 分层、safe-stop / handoff / audit 约束是兼容的，也说明本项目不必走 peer-to-peer chat 模式，仍然可以坚持 supervisor-managed parallelism。

## 候选演进路径

### 方案 A — 在当前 runtime 上先补“并行安全的 subgraph fan-out/fan-in”（推荐作为第一条实现线）

**思路**：不直接做 full team/swarm runtime，而是把当前 `subgraph` 升级成可并行的最小 orchestration primitive。

**建议边界**：

1. 一个 parent task 可以派生多个 child contracts
2. child 仅允许 `per-invocation` 隔离上下文
3. child 必须声明 disjoint write set
4. parent 通过 barrier 等待 child results
5. merge 只允许：
   - 无冲突自动合并
   - 可解释冲突送 review
   - 高风险冲突阻塞
6. 不允许 shared per-thread memory child 并发重入

**优点**：

- 与当前 `subgraph_mode` 最接近，路径最短
- 能先覆盖“分发式开发 + 独立子切片 + 同步汇合”这一类最现实需求
- 不需要一步到位定义 peer chat、team role rotation、dynamic speaker selection

**缺点**：

- 不是完整 `team/swarm`
- 仍然要求子任务写集相对独立
- 对长期共享研究 agent 或共享记忆 agent 的支持有限

### 方案 B — 直接把 task graph / team / swarm 做成一等运行时

**思路**：新增 `TaskGraph`、scheduler、dependency edges、team state、join/review aggregation，把 `team/swarm` 从保留字升级成完整运行时能力。

**需要补的核心对象**：

- task graph schema
- child contract batch / task group contract
- scheduler / admission controller
- namespace allocator / lock manager
- group result / join review model
- cancellation / pause / resume / abort protocol

**优点**：

- 长期能力最强
- 可以自然承接 team、swarm、blocked dependencies、auto wake-up

**缺点**：

- scope 最大
- 需要同时改 PDP/PEP、contracts、review、audit、write-back
- 在尚未验证最小并行语义前，极容易抽象过早

### 方案 C — 在 runtime 之上单独建立 orchestration bridge / daemon layer

**思路**：保留当前 runtime 继续专注“单切片治理执行”，把多任务调度、依赖图、并行生命周期放到更高层 orchestration layer；每个 child task 仍然调用当前 runtime 作为治理内核。

**优点**：

- 能保持当前内核克制
- 更贴近 Multica daemon / LangGraph parent graph 的分层思想
- 适合未来跨入口、跨宿主、跨工作区的 distributed development

**缺点**：

- 新增一层 bridge / daemon 复杂度
- 如果 parent orchestration 与 governance contract 没有定义清楚，会出现双重状态机
- 短期内用户感知链路更长

## 推荐

我当前不建议直接进入方案 B。

当前更合理的顺序是：

1. **先用方案 A 证明最小并行语义**
   - 只做 `per-invocation` child subgraph
   - 只允许 disjoint write sets
   - 先定义 fan-out / barrier / merge / review 聚合
2. **同时用方案 C 约束长期架构**
   - 把“治理内核”和“任务编排层”边界先说清楚
   - 避免后续为了支持 team/swarm 把当前 PEP executor 直接膨胀成万能调度器
3. **把方案 B 作为第二阶段目标，而不是第一刀**
   - 等最小并行 contract、冲突模型、review 聚合已经被验证后，再决定是否把 task graph / team runtime 上升为平台核心

原因很直接：

1. 当前最强的真实需求是“并行推进多个相对独立切片”，不是“马上拥有完整 swarm 平台”
2. LangGraph 最有价值的经验就是先把 parallel-safe persistence mode 说清楚
3. AutoGen 最有价值的经验则是：只有当 lifecycle 真要由 runtime 管时，才值得把 team 做成一等 primitive

## 如果进入下一条 planning-gate，建议只做什么

下一条 planning-gate 建议只收口为：

1. 定义 `TaskGroup` 或等价对象的最小 schema
2. 定义 child task identity、parent-child lineage 与 trace event
3. 定义 `allowed_artifacts` 的并行硬约束与冲突分类
4. 定义 `per-invocation` child namespace / checkpoint policy
5. 定义 barrier merge 与 grouped review outcome

下一条 planning-gate 明确不做：

1. 不实现完整 `team/swarm` runtime
2. 不引入长期共享记忆 child 的并发重入
3. 不在第一条切片里做跨工作区分布式调度
4. 不同时改造所有 host / extension 入口

## 参考来源

- `docs/subagent-management.md`
- `docs/core-model.md`
- `docs/subagent-schemas.md`
- `docs/specs/subagent-contract.schema.json`
- `src/pdp/delegation_resolver.py`
- `src/collaboration/modes.py`
- `src/collaboration/handoff_mode.py`
- `src/collaboration/subgraph_mode.py`
- `src/pep/executor.py`
- `src/subagent/contract_factory.py`
- `design_docs/subagent-management-design.md`
- `design_docs/subagent-context-isolation-evaluation.md`
- `design_docs/subagent-tracing-writeback-direction-analysis.md`
- `review/research-compass.md`
- `review/langgraph-langchain.md`
- `review/autogen.md`
- `review/openai-agents-sdk.md`
- `review/claude-managed-agents-platform.md`
- `review/multica/02-direction-and-weaknesses.md`
- `review/multica-borrowing/borrowing-insights.md`
- `review/crewai.md`
- LangGraph Subgraphs 官方文档
- AutoGen Teams 官方文档