# Project Progress Multi-Graph Direction Analysis

## 背景

当前仓库已经具备两类相邻但不等价的资产：

1. `design_docs/` 中按 planning-gate / direction-analysis 组织的推进历史
2. `tools/dependency_graph/` 中按代码符号关系组织的依赖图工具

但用户当前提出的是第三类对象：

- 一组能表达**项目推进历史与未来推进空间**的多图系统
- 图之间可以完全独立，也可以通过 typed edge 产生联动
- 图既要能展示给用户，也要能作为主 agent / 子 agent / 调度层的参考面
- 节点团应可被抽象成大节点，但原始节点必须保持可索引、可展开

因此，这不是把现有 `dependency_graph` 多加几种 edge kind 就能解决的问题，而是需要一个独立的 `progress-graph` foundation。

## 可直接借鉴的现成结果

### 1. DAG + partial order

- `workflow` / `dependency` edge 最自然的数学基础是 DAG 与 partial order
- 现成算法直接可借：topological sort、topological layers、ready frontier
- 对本项目的意义：主 agent 可以据此判断“哪些方向已经 ready、哪些仍被依赖阻塞”

### 2. Connected components / SCC / condensation

- 多图独立性可直接借 connected components 判断
- 若某个局部子图因联动而形成循环依赖或强耦合，可借 SCC + condensation graph 做抽象压缩
- 对本项目的意义：节点团不是“上下文摘要文本”而已，而是一个可逆、可索引的图压缩原语

### 3. Compound graph / cluster graph

- 展示层最自然的现成结果是 cluster / compound graph，而不是自发明 UI 语义
- Graphviz 的 subgraph cluster 是稳定参照；后续若进入交互式 UI，可再借 React Flow / ELK 一类 compound layout
- 对本项目的意义：节点团边缘施工时，可在 cluster 与原始节点之间切换，而不是丢失原始可追溯性

### 4. Snapshot-backed graph history

- “保留推进历史”最稳的最小做法不是 event-sourcing 全家桶，而是 snapshot chain
- 每个 graph 保留 `snapshot_id -> parent_snapshot_id` 链，即可同时支持：
  1. 当前图
  2. 历史版本
  3. 历史回看
  4. 后续再做 delta / replay

## 相关现成方案的借鉴点

### 候选参照 A. LangGraph / state graph

- 值得借：graph-first orchestration、subgraph、interrupt/resume
- 不直接照搬：重量级 runtime、graph API 先行

### 候选参照 B. Multica issue dependency / daemon orchestration

- 值得借：多方向推进最终会需要 dependency graph、wake-up、队列与可靠性
- 不直接照搬：先跳 daemon；当前还应先固定 foundation 与 query 面

### 候选参照 C. 当前仓库 `tools/dependency_graph/`

- 值得借：独立 package、可序列化模型、查询接口、JSON snapshot
- 不直接照搬：它的 node/edge kind 过于 code-symbol specific，不适合作为 progress graph 的 authority model

## 候选路线

### A. snapshot-backed progress multigraph foundation（推荐）

- 做什么：新建独立 `tools/progress_graph/`，固定：
  1. 多图 + 当前图指针
  2. typed nodes / edges
  3. history snapshot chain
  4. ready frontier / topological layers / independent graph groups
  5. cluster-based condensed view
- 依据：
  - [tools/dependency_graph/model.py](tools/dependency_graph/model.py)
  - [design_docs/stages/planning-gate/2026-04-15-type-dependency-graph-extraction.md](design_docs/stages/planning-gate/2026-04-15-type-dependency-graph-extraction.md)
  - [design_docs/workspace-parallel-task-orchestration-direction-analysis.md](design_docs/workspace-parallel-task-orchestration-direction-analysis.md)
  - [review/langgraph-langchain.md](review/langgraph-langchain.md)
  - [review/multica/02-direction-and-weaknesses.md](review/multica/02-direction-and-weaknesses.md)
- 风险：中。
- 当前判断：**推荐**。因为它能先回答“这个图最小应该长什么样、能被谁消费”，而不需要立刻绑定 UI 或 daemon runtime。

### B. extend current dependency_graph into a generic project graph

- 做什么：直接把 `tools/dependency_graph/` 泛化成项目进度图系统
- 风险：中到高。
- 当前判断：不推荐作为第一刀。因为它会把“代码依赖图”和“推进历史图”两套语义混在一起，后续查询和 authority boundary 会变脏。

### C. jump directly to first-class graph UI + scheduler runtime

- 做什么：直接做用户可视化图 + 主/子 agent 调度器 + 历史压缩/展开交互系统
- 风险：高。
- 当前判断：长期成立，但不适合作为第一刀。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 这条需求的最小阻塞面不是 UI，而是 authority data model
2. 这条需求的最小阻塞面也不是 full scheduler，而是 scheduler/query 可消费的 graph primitive
3. 现成数学工具已经足够清楚：workflow/dependency 用 DAG，独立图用 connected components，压缩/抽象用 cluster 与 condensation