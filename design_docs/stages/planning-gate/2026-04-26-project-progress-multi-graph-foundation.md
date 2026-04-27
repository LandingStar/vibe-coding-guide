# Planning Gate — Project Progress Multi-Graph Foundation

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-multi-graph-direction-analysis.md`

## 1. Why this gate exists

用户提出新的功能方向：项目需要保留可并发推进、可回溯、可展示、可供多 agent 调度参考的多图推进历史。

当前仓库最接近的资产是：

1. `design_docs/` 的 planning-gate / direction-analysis 历史
2. `tools/dependency_graph/` 的代码依赖图模型与查询接口

但这两者都还不能直接表达：

- 多个独立图
- workflow / dependency / linkage typed edges
- 节点团抽象与展开
- 调度可消费的 ready frontier
- 图快照历史

## 2. Scope

本 gate 只处理 foundation：

1. progress multigraph 的数据模型
2. snapshot-backed history chain
3. DAG / cluster / independent-group query primitive
4. foundation targeted tests

本 gate 不处理：

1. UI 展示层
2. 主 agent / 子 agent 真实调度器集成
3. daemon queue / persistence runtime
4. 自动 cluster suggestion 或复杂 replay 机制

## 3. Working hypothesis

当前最小可行路线应是：

1. 新建独立 `tools/progress_graph/`，不污染 `tools/dependency_graph/`
2. 每个 graph 先按 snapshot chain 保留历史，而不是先做事件总线
3. workflow / dependency 边先强制为 DAG 可查询面，linkage 边保留联动语义但不进入调度拓扑
4. 节点团先由显式 cluster 提供 condensed view；SCC / condensation 作为后续增强参考

## 4. Slices

### Slice 1 — Data model and query contract

- 固定 `ProgressNode` / `ProgressEdge` / `ProgressCluster`
- 固定 `ProgressGraph` / `ProgressMultiGraphHistory`
- 固定 `ready_nodes()` / `topological_layers()` / `independent_graph_sets()` / `build_condensed_view()`

当前状态：Slice 1 设计草案已创建为 `design_docs/project-progress-multi-graph-slice1-draft.md`。

### Slice 2 — Foundation implementation

- 新增 `tools/progress_graph/model.py`
- 新增 `tools/progress_graph/query.py`
- 固定 JSON serialization / deserialization

当前状态：已完成。`tools/progress_graph/model.py` 与 `tools/progress_graph/query.py` 已新增并通过 targeted validation。

### Slice 3 — Targeted tests completion

- 新增 foundation targeted tests
- 覆盖 DAG ready frontier、cycle guard、cluster condensed view、snapshot history、cross-graph readiness

当前状态：已完成。`tests/test_progress_graph.py` 已新增并通过 `6 passed`。

## 5. Validation gate

- foundation tests 通过
- model/query 的 round-trip 与核心 query 结果通过 targeted validation

当前结果：已通过 `tests/test_progress_graph.py`（6 passed）。

## 6. Stop condition

- 当 foundation contract、实现与 targeted tests 都已落地并通过窄验证后停止
- 不在本 gate 内进入 UI / scheduler / daemon runtime

当前结果：stop condition 已满足；后续方向已转入 `design_docs/project-progress-multi-graph-foundation-followup-direction-analysis.md`。

## 7. Architecture

当前实现采用四层结构，而不是把“历史保留”“图查询”“展示压缩”“跨图联动”混在一个对象里：

### 7.1 Value object layer

最底层是不可变 value objects：

1. `ProgressNode`
2. `ProgressEdge`
3. `ProgressCluster`
4. `CrossGraphEdge`

这里的职责是固定 authority data shape：

- node 表达一个推进节点，当前支持 `task` / `milestone` / `decision` / `reference`
- edge 表达同图内关系，当前支持 `workflow` / `dependency` / `linkage`
- cluster 表达可压缩的节点团，保留 member ids，允许 collapsed display
- cross-graph edge 表达不同 graph 当前快照之间的联动或阻塞关系

这样做的目的，是把“图是什么”与“图怎么被查询、展示、调度消费”分开，避免后续 consumer 直接依赖 ad-hoc dict。

### 7.2 Single-graph layer

`ProgressGraph` 负责单张图当前快照的 ownership：

1. graph identity：`graph_id` / `snapshot_id` / `parent_snapshot_id`
2. same-graph node / edge / cluster storage
3. same-graph invariant check
4. same-graph query primitive

这里的核心判断是：

- `workflow` / `dependency` 是 ready frontier 的阻塞边
- `linkage` 是联动边，但不进入当前调度拓扑
- cluster 只做压缩/展示语义，不改写原始节点身份

因此单图层同时提供：

1. `predecessors()` / `successors()`
2. `ready_nodes()`
3. `topological_layers()`
4. `cluster_boundary()`
5. `build_condensed_view()`
6. `check_invariants()` / `validate()`
7. `summary()` / `to_dict()` / `from_dict()` / JSON round-trip

其中最关键的约束有两个：

1. `workflow` + `dependency` 视角必须形成 DAG；若出现循环，`validate()` 会失败
2. cluster member 必须存在，且一个 node 不能属于多个 cluster

### 7.3 Multi-graph history layer

`ProgressMultiGraphHistory` 负责多图与历史链：

1. 按 `snapshot_id` 保存全部快照
2. 按 `graph_id -> current_snapshot_id` 保存当前图指针
3. 保存 cross-graph edge
4. 提供 history chain 与跨图 ready 计算

这层没有把历史做成 event bus，而是采用 snapshot chain：

1. `add_snapshot()` 校验 parent snapshot 与 graph identity
2. `history_for(graph_id)` 返回从旧到新的快照链
3. `independent_graph_sets()` 用 cross-graph edge 计算当前多图联通分组
4. `global_ready_nodes()` 在单图 ready 的基础上，再检查 cross-graph dependency 是否满足

这里的关键边界是：

- same-graph 拓扑顺序由 `ProgressGraph` 自己维护
- cross-graph 只在 history/current-graph 层汇总，不反向污染单图对象

### 7.4 Thin query surface

`tools/progress_graph/query.py` 刻意保持很薄，只做两件事：

1. 从 JSON snapshot 载入 `ProgressMultiGraphHistory`
2. 暴露稳定的程序化查询入口

当前保留的入口是：

1. `load_history()`
2. `query_graph_summary()`
3. `query_ready_nodes()`
4. `query_independent_graph_sets()`
5. `query_topological_layers()`
6. `query_condensed_view()`

这意味着后续无论是文档投影、Graphviz/React Flow export，还是 scheduler-facing integration，都可以先依赖这组稳定 surface，而不是直接耦合内部字段布局。

## 8. Implementation Results

本 gate 当前实际落地结果如下。

### 8.1 新增文件与职责

1. `tools/progress_graph/__init__.py`
	- 固定 package export surface
2. `tools/progress_graph/model.py`
	- 实现 value objects、single-graph model、multi-graph history、serialization、invariant validation
3. `tools/progress_graph/query.py`
	- 提供薄查询层与 JSON history loader
4. `tests/test_progress_graph.py`
	- 提供 foundation targeted tests

### 8.2 已实现能力

当前已经实现并可直接复用的能力包括：

1. snapshot-backed graph history
	- 同一 graph 可通过 `parent_snapshot_id` 保留历史链
2. typed same-graph edges
	- `workflow` / `dependency` / `linkage` 已显式区分
3. cross-graph dependencies
	- 不同 graph 之间可以建立 directed typed edge
4. ready frontier
	- 单图 `ready_nodes()` + 多图 `global_ready_nodes()`
5. deterministic topology
	- `topological_layers()` 提供稳定拓扑层次输出
6. cluster-based coarsening
	- `build_condensed_view()` 可把显式 cluster 压成 display node，同时保留 member mapping
7. independent graph grouping
	- `independent_graph_sets()` 可识别当前多图中的独立图组
8. JSON round-trip
	- graph 与 history 都可 `to_dict()` / `from_dict()` / `to_json()` / `from_json()`

### 8.3 已验证结果

当前 targeted tests 已覆盖并通过以下行为：

1. `ready_nodes()` 与 `topological_layers()` 对 `workflow` / `dependency` 的基本顺序判断
2. `validate()` 对循环 `workflow` / `dependency` 边的拒绝
3. `build_condensed_view()` 对 cluster 压缩后边界边的保留
4. `history_for()` 对 snapshot parent chain 的保留
5. `independent_graph_sets()` 对 cross-graph linkage 的分组判断
6. `global_ready_nodes()` 对 cross-graph dependency 的阻塞判断

当前验证结果：`tests/test_progress_graph.py` 为 `6 passed`。

### 8.4 当前未做的内容

为保持第一刀收敛，本 gate 明确没有进入以下内容：

1. 不做文档源到 graph snapshot 的自动投影
2. 不做 Graphviz / React Flow export schema
3. 不做 scheduler / daemon / bridge runtime 集成
4. 不做自动 cluster suggestion、SCC auto-coarsening 或 replay engine
5. 不做更厚的事件流或 event-sourcing runtime

### 8.5 当前判断

当前实现结果已经足以作为 progress history 的 authority foundation。它还不是最终用户可见系统，但已经把最关键的底座固定下来了：

1. graph identity 与 history identity 已分开
2. workflow/dependency 与 linkage 已分开
3. raw node 与 condensed cluster view 已分开
4. same-graph query 与 cross-graph readiness 已分开

因此，后续无论先走文档投影、展示导出，还是调度集成，都不需要再回头重写当前 foundation model。