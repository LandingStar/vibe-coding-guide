# Planning Gate — Project Progress Doc-Loop Projection And Snapshot Persistence

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-multi-graph-foundation-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-multi-graph-foundation.md` 已完成。

当前已经有：

1. `tools/progress_graph/model.py` 的 authority data model
2. `tools/progress_graph/query.py` 的薄查询面
3. snapshot-backed history chain 与 cross-graph readiness foundation

但当前还没有真实 consumer 把 doc-loop 文档状态投影成 progress graph，因此这套模型仍主要是空 foundation。

当前最直接的真实来源是：

1. `.codex/checkpoints/latest.md`
2. `design_docs/stages/planning-gate/`
3. `design_docs/Project Master Checklist.md`

## 2. Scope

本 gate 只处理：

1. doc-loop 文档到 `ProgressMultiGraphHistory` 的最小投影 contract
2. snapshot persistence 到 `.codex/progress-graph/latest.json`
3. projection targeted tests

本 gate 不处理：

1. Graphviz / React Flow export
2. scheduler / daemon / bridge runtime integration
3. 通用 markdown parser framework
4. 历史文档的深度回填与推断式 dependency 恢复

## 3. Working hypothesis

当前最小可行路线应是：

1. 复用 `src/workflow/checkpoint.read_checkpoint()` 解析 checkpoint
2. 为 planning-gate 与 checklist 新增极薄的定向 projection parser，而不是引入通用 markdown parser
3. 先把三类来源各自投影成独立 graph snapshot，再用 cross-graph linkage 保留最关键的关联
4. history 持久化先落到单文件 `.codex/progress-graph/latest.json`，由 `ProgressMultiGraphHistory` 自己保留 snapshot chain

## 4. Slices

### Slice 1 — Projection contract

- 固定 graph ids、source-to-node mapping、status mapping、snapshot persistence path
- 固定 checkpoint / planning-gate / checklist 三类 source 的最小投影边界

当前状态：Slice 1 设计草案已创建为 `design_docs/project-progress-doc-loop-projection-slice1-draft.md`。

### Slice 2 — Projection implementation

- 新增 `tools/progress_graph/doc_projection.py`
- 新增 history load/save helper
- 新增最小 snapshot writer

当前状态：已完成。`tools/progress_graph/doc_projection.py` 已实现 checkpoint / planning-gate / checklist 三类来源的最小 projection 与 history load/write helper。

### Slice 3 — Targeted tests completion

- 新增 doc projection targeted tests
- 覆盖 checkpoint projection、planning-gate status projection、checklist projection、snapshot append persistence

当前状态：已完成。`tests/test_progress_graph_doc_projection.py` 已新增并通过 `2 passed`。

## 5. Validation gate

- projection targeted tests 通过
- 生成的 `.codex/progress-graph/latest.json` 能被 `ProgressMultiGraphHistory.from_json()` 正常读回

当前结果：目标测试 `tests/test_progress_graph_doc_projection.py` 已通过 `2 passed`；真实仓库中的 `.codex/progress-graph/latest.json` 已写出并可被 `load_doc_progress_history()` 读回。

## 6. Stop condition

- 当 doc-loop projection contract、实现与 targeted tests 都已落地并通过窄验证后停止
- 不在本 gate 内进入 UI / scheduler / daemon runtime

当前结果：stop condition 已满足；后续方向已转入 `design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md`。

## 7. Implementation results

本 gate 当前实际落地结果如下。

### 7.1 新增文件与职责

1. `tools/progress_graph/doc_projection.py`
	- 实现 doc-loop projection、history load/write、snapshot append
2. `tests/test_progress_graph_doc_projection.py`
	- 实现 projection targeted tests

### 7.2 已实现能力

当前已经实现：

1. checkpoint projection
	- 复用 `src/workflow/checkpoint.read_checkpoint()`，把 current todo、phase、active planning gate、pending decision 投影成 `checkpoint-current`
2. planning-gate projection
	- 扫描 `design_docs/stages/planning-gate/`，把 gate 文档索引投影成 `planning-gates-index`
3. checklist projection
	- 把 `design_docs/Project Master Checklist.md` 的当前快照和活跃待办投影成 `project-checklist-current`
4. snapshot persistence
	- 把完整 `ProgressMultiGraphHistory` 写入 `.codex/progress-graph/latest.json`
5. history append
	- 重复写入时会沿 `graph_id` 追加 snapshot chain，而不是覆盖成单快照对象
6. cross-graph linkage
	- 当前 checkpoint active planning gate 会与 planning-gate index 中对应 gate 建立 linkage

### 7.3 当前未做的内容

本 gate 明确未进入：

1. direction-analysis / phase map projection
2. Graphviz / React Flow export schema
3. scheduler-facing runtime integration
4. richer dependency inference 或自动 linkage 推断