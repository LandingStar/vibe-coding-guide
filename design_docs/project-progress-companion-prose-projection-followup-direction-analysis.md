# Project Progress Companion Prose Projection Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已把 pure companion prose sections 纳入 `direction-candidates-global`
2. `用户选定下一步`、`当前更窄的入口` 与 `当前实际下一条 planning-gate` 现已作为 section-local 独立节点进入 graph
3. 当 prose 中存在显式 planning-gate path 时，`actual-next-gate` companion node 已能建立到 `planning-gates-index` 的最小 linkage
4. `tests/test_progress_graph_doc_projection.py` targeted validation 已通过，真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按新 companion prose surface 刷新

用户随后已经明确纠正下一步 framing：当前不是继续沿 `post-release` 收口，而是应从仓库里仍未执行或被中断的真实议案中，重新选择下一条最值得恢复/推进的窄主线。

因此，当前判断标准应改成：

1. 是否是现有文档里仍未执行、被暂停，或仅停留在 backlog 的真实议案
2. 是否已经有足够明确的 contract / slice 入口，能支持下一刀继续推进
3. 是否能在不重新扩成大范围换线的前提下，为当前仓库增加新的确定性

## 候选路线

### A. Resume Paused Orchestration Bridge Landing Dispatch Integration（推荐）

- 做什么：恢复 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md` 这条已暂停的 planning-gate，从现有 Slice 1 入口继续固定 landing dispatch contract，并在后续进入最小 dispatch helper / targeted tests
- 依据：
  - `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md`
  - `design_docs/orchestration-bridge-landing-dispatch-integration-direction-analysis.md`
  - `design_docs/Project Master Checklist.md`
- 风险：中。
- 当前判断：**推荐**。这是一条已经被明确写入文档、且因主线切换而暂停的真实未执行议案；它已经有现成的 gate 与 Slice 1 入口，不需要先重新发明边界。

### B. Broader Companion Prose Surface Expansion

- 做什么：把 companion prose projection 从当前 `design_docs/direction-candidates-after-phase-35.md` 的 section-level prose，继续扩到相邻的 progress-graph source surface，例如 current follow-up analysis、Checklist 或 Phase Map 中与“下一步为何如此选择”直接相关的 companion prose
- 依据：
  - `design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md`
  - `design_docs/project-progress-companion-prose-projection-slice1-draft.md`
  - `design_docs/Global Phase Map and Current Position.md`
- 风险：中高。
- 当前判断：合理，且最贴近刚完成的 progress graph 主线；但它会继续扩大 prose source boundary，而当前还没有现成的新 gate/slice 草案，因此优先级低于候选 A。

### C. Dogfood Evidence / Issue / Feedback Component-or-Skill Integration Backlog

- 做什么：回到 Checklist 中仍未收口的 dogfood backlog，但不直接重新实现已完成的 pipeline；而是先把“证据收集 / 问题收集 / 反馈整合”进一步压成新的组件或 skill 入口方向，并据此起一条新的窄 planning-gate
- 依据：
  - `design_docs/dogfood-evidence-issue-feedback-boundary.md`
  - `design_docs/dogfood-pipeline-workflow-integration-direction-analysis.md`
  - `design_docs/Project Master Checklist.md`
- 风险：中高。
- 当前判断：是明确存在的 backlog 主线，但优先级仍低于候选 A/B；因为当前 backlog 表述已经跨越多轮实现，需要先重切边界，才适合进入新的 gate。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 它是当前证据最强的“未执行议案”：不是抽象 backlog，也不是新的想法，而是一条已存在但被显式暂停的窄 gate
2. 它已有现成的 Slice 1 合同入口，恢复成本低，且不会把当前问题重新扩成大范围方向重审
3. 候选 B 虽然更贴近刚完成的 progress graph 主线，但它需要主动扩大 source boundary；相比之下，候选 A 的控制面更清晰
4. 候选 C 的长期价值成立，但它更像需要重新切 scope 的 backlog 抽象，而不是现在最适合立刻恢复的下一刀

如果你现在明确希望继续沿刚完成的 progress graph 主线推进，而不是切回之前被暂停的 orchestration 线，那么候选 B 会是更合适的备选；否则，默认推荐仍应是候选 A。
