# Planning Gate — Project Progress Legacy Non-Project Numbered Candidate Aggregation

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-non-project-progress-candidate-aggregation-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-non-project-progress-candidate-aggregation.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/doc_projection.py` 已能把非 `project progress` 且采用 `### 新候选 A/B/C` 的 `##` section 纳入 `direction-candidates-global`
2. `direction-candidates-after-phase-35.md` 中仍存在一批尚未进入图面的 legacy non-project sections，它们沿用 `- 候选 1/2/3` 与 section-level `当前倾向`
3. 这些 legacy numbered sections 与现有 parser 的控制路径基本一致，仍应优先作为最小 coverage 扩展，而不是立即进入 plain `### A./B./C.` 或 companion prose 建模

## 2. Scope

本 gate 只处理：

1. `design_docs/direction-candidates-after-phase-35.md` 中标题不含 `project progress`、且 section 内存在 `- 候选 1/2/3` 与 `当前倾向` 的 `##` section aggregation projection
2. 在现有 `direction-candidates-global` graph 中补这些 legacy numbered sections 的 section node + numbered candidate node
3. 继续复用现有 section-level `当前倾向 -> recommended candidate` surface
4. targeted tests 与真实 workspace artifact refresh

本 gate 不处理：

1. plain `### A./B./C.` legacy candidate headings
2. `### 新候选 A/B/C` 之外的 lettered variant 扩展
3. `用户选定下一步` / `当前更窄的入口` / `当前 AI 倾向判断` 等 companion prose projection
4. date ordering / recency semantics 的重新定义

## 3. Working hypothesis

当前最小可行路线应是：

1. 继续复用 `direction-candidates-global` graph，而不是再造 graph id
2. 只要 `##` section 命中 legacy numbered candidate block，就允许 non-project section 进入现有 numbered parser
3. 继续复用 section-level `当前倾向` 作为 recommended candidate surface
4. 先用 targeted tests 锁定 non-project numbered section 的最小节点 contract，再刷新真实 artifacts

## 4. Slices

### Slice 1 — Legacy numbered section contract

- 固定 non-project numbered section selection boundary、candidate node id 与 recommended surface

当前状态：已完成；Slice 1 设计草案已按实现口径收口为 `design_docs/project-progress-legacy-non-project-numbered-candidate-aggregation-slice1-draft.md`。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中扩展 `direction-candidates-global` builder，使 non-project legacy numbered sections 也能进入现有 numbered parser

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已支持 non-project legacy numbered sections 进入现有 numbered parser。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已通过（2 passed），真实 workspace artifacts 已刷新。

## 5. Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- `.codex/progress-graph/latest.json` 能包含新增 legacy non-project numbered section/candidate nodes
- 刷新后的 `.html` / `.dot` 能包含扩展后的 `direction-candidates-global` graph，且不回归已有 project-progress numbered sections 与 new-candidate sections

## 6. Stop condition

- 当 contract、实现、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内扩到 plain `### A./B./C.`、companion prose projection 或 recency 语义重算

## 7. Out-of-scope issue recorded during validation

- `direction-candidates-global` 的 section recency 当前仍受文档物理顺序影响，已登记到 `design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`，不在本 gate 内处理