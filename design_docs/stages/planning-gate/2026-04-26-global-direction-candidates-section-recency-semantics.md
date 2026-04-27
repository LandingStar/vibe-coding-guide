# Planning Gate — Global Direction-Candidates Section Recency Semantics

> 日期: 2026-04-26
> 状态: COMPLETE
> 来源: `mcp_doc-based-cod2_workflow_interrupt` during `design_docs/stages/planning-gate/2026-04-26-project-progress-legacy-non-project-numbered-candidate-aggregation.md`

## Why this exists

在验证 legacy non-project numbered aggregation 时，发现 `direction-candidates-global` 当前仍以文档物理顺序决定 latest numbered section，而不是按更稳定的时间/语义边界判断。

这会导致：

1. 新近插到文档顶部的 numbered section 进入 graph，但 section status 仍可能显示为 `completed`
2. 当前 `recommended/current` surface 对“最新 section”存在位置敏感性

## Scope

本 gate 只处理：

1. 为 `direction-candidates-global` 定义 section recency source-of-truth
2. 让 latest/current section status 不再直接依赖当前文档物理顺序的“最后一个 numbered section”判定
3. 用 targeted tests 验证顶部新增或前置 numbered section 后，latest section 仍能按收口规则稳定判定
4. 刷新真实 `.codex/progress-graph/latest.json`、`.dot`、`.html`

本 gate 不处理：

1. companion prose projection
2. selected-next-step linkage projection
3. non-numbered / lettered candidate 的额外语义增强
4. graph 展示面的 UI 变更

## Working hypothesis

当前最小可行路线应是：

1. latest section 的 source-of-truth 应优先取自 section title 中的日期语义
2. 当日期相同或缺失时，再以更早的文档位置作为 tie-break，而不是当前“最后出现者获胜”
3. 一旦 latest section 选择规则稳定，现有 numbered candidate status surface 无需改 shape，只需改 latest section 归属

## Slices

### Slice 1 — Recency selection contract

- 固定 `direction-candidates-global` 的 latest section source-of-truth、tie-break 规则与 metadata surface

当前状态：已完成；`design_docs/project-progress-global-direction-candidates-recency-semantics-slice1-draft.md` 已落地为当前实现 contract。

### Slice 2 — Selection implementation

- 在 `tools/progress_graph/doc_projection.py` 中把 latest section 选择从“最后一个 numbered section”改成显式 recency 规则

当前状态：已完成；当前实现已按 section title 日期优先、文档更早位置 tie-break 选择 latest numbered section，并把 `recency_date` 写入 section metadata。

### Slice 3 — Targeted tests and artifact refresh

- 调整 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`pytest tests/test_progress_graph_doc_projection.py -q` 已通过（3 passed），真实 artifact 也已刷新。

## Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- 顶部新增或前置的 numbered section 不再因为物理顺序而错误落成 `completed`
- 真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按新 recency 规则刷新

## Stop condition

- 当 recency contract、实现、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内扩到 prose / linkage / UI 语义

## Result

本 gate 已完成，当前确认结果如下：

1. `direction-candidates-global` 不再把“最后出现的 numbered section”直接当作 latest
2. latest section 会优先取 section title 中的日期语义；当日期相同或缺失时，取更早的文档位置
3. targeted pytest 已新增顶部插入 numbered section 的 probe，并验证通过
4. `.codex/progress-graph/latest.json`、`.dot`、`.html` 已按新 recency 规则刷新