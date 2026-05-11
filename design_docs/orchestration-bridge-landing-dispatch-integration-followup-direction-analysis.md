# Orchestration Bridge Landing Dispatch Integration Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md` 已完成并关闭。

当前已经具备：

1. `build_landing_consumer_payload()` 已稳定承担 owner-facing payload normalizer
2. `src/runtime/orchestration/landing_dispatch.py` 已把 `handoff`、`escalation`、`review_intake` 三类 payload 统一落到真实 owner surface
3. `handoff` 已通过 `FileHandoffConsumer` 复用 executor handoff JSON 持久化语义；`review_intake` 已通过 `FeedbackAPIReviewIntakeConsumer` 复用现有 `FeedbackAPI.register()` pending review surface
4. `tests/test_runtime_orchestration_landing_dispatch.py`、`tests/test_runtime_orchestration_landing_consumers.py` 与 `tests/test_runtime_orchestration*.py` 相关 6 文件联合验证已通过（30 passed）

因此，当前 orchestration bridge 主线已经不再是“landing payload 能否进入真实 owner surface”，而是：

1. 这条 landing contract 收口后，bridge 上层还缺哪个最小调度 contract
2. 是否应该顺势切到更高一层的 bridge / daemon contract-first 讨论
3. 或者当前应改回 repo 里其它仍未执行的候选，而不是继续停留在 orchestration 线

## 候选路线

### A. Thin Orchestration Bridge / Daemon Contract-First（推荐）

- 做什么：把下一刀收窄为 bridge / daemon 与现有治理内核之间的最小 contract，优先回答 work-item / group-item lifecycle、terminal landing 如何向上回传，以及 bridge 是否只负责调度与恢复，而不直接决定 gate / review 语义
- 依据：
  - `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md`
  - `design_docs/orchestration-bridge-daemon-layer-direction-analysis.md`
  - `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`
- 风险：中。
- 当前判断：**推荐**。因为 landing dispatch 已把 owner surface 缺口收口，当前真正上移出来的问题是“谁来承接更高一层的调度与恢复 contract”，而不是继续在当前 gate 内加更厚的 history/runtime。

### B. Broader Companion Prose Surface Expansion

- 做什么：回到 `project progress` 主线，把 companion prose projection 从 `design_docs/direction-candidates-after-phase-35.md` 的 section-level prose，继续扩到相邻的 follow-up analysis、Checklist 或 Phase Map prose surface
- 依据：
  - `design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md`
  - `design_docs/direction-candidates-after-phase-35.md`
  - `design_docs/Global Phase Map and Current Position.md`
- 风险：中高。
- 当前判断：依然成立，但优先级低于候选 A。因为它会切回 progress-graph 主线并扩大 source boundary，而候选 A 更直接承接刚完成的 landing-dispatch 议案。

### C. Dogfood Evidence / Issue / Feedback Component-or-Skill Integration Backlog

- 做什么：回到 Checklist 中仍未完全收口的 dogfood backlog，但先把“证据收集 / 问题收集 / 反馈整合”重新压成新的组件或 skill 入口，再据此起新的窄 planning-gate
- 依据：
  - `design_docs/dogfood-evidence-issue-feedback-boundary.md`
  - `design_docs/dogfood-pipeline-workflow-integration-direction-analysis.md`
  - `design_docs/Project Master Checklist.md`
- 风险：中高。
- 当前判断：是明确存在的 backlog 主线，但当前仍缺新的窄 gate 边界，因此优先级低于候选 A。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. landing dispatch 已把当前最直接的 delivery 缺口收口，继续留在本 gate 内扩 runtime 会违反已写明的 stop condition
2. `design_docs/orchestration-bridge-daemon-layer-direction-analysis.md` 已明确给出下一层问题：bridge / daemon 应该只承接调度与恢复，而不是继续污染治理内核
3. 候选 B/C 虽仍有价值，但都需要切回另一条主线；相比之下，候选 A 能以最小换线成本延续刚完成的 orchestration 线

如果你现在明确希望切回 `project progress` 或 dogfood backlog，而不是继续沿 orchestration bridge 往上收窄，那么候选 B/C 仍是合理备选；否则，默认推荐应是候选 A。