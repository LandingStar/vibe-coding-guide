# Planning Gate — Orchestration Bridge Landing Dispatch Integration

> 日期: 2026-04-26
> 状态: COMPLETED
> 关联方向分析: `design_docs/orchestration-bridge-landing-dispatch-integration-direction-analysis.md`
> 后续方向分析: `design_docs/orchestration-bridge-landing-dispatch-integration-followup-direction-analysis.md`

> 恢复说明: 2026-04-28 用户已按未执行议案视角重新审查候选，并明确选择恢复本 gate；当前从既有 Slice 1 草案继续推进 landing dispatch contract，不回到 post-release 候选待选状态。

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-consumer-wiring.md` 已完成。

当前已经存在：

1. `BridgeLandingArtifact`
2. 现有 consumer payload 映射
3. handoff validator / escalation notifier / waiting_review 对齐 payload

因此当前最明显的空洞是：

- landing consumer payload 还没有统一的 dispatch/delivery contract

## 2. Scope

本 gate 只处理：

1. landing dispatch contract
2. 最小 dispatch helper / protocol 实现
3. dispatch targeted tests

本 gate 不处理：

1. daemon queue / persistence / replay runtime
2. executor 主流程大改写
3. 更厚的 landing history runtime

## 3. Working hypothesis

当前最小可行路线应是：

1. handoff、escalation、review intake 统一走一层 landing dispatch helper
2. 这一层只负责把 payload 交给现有 delivery surface，不重新定义 governance 对象
3. dispatch contract 稳定后，再决定是否进入 daemon/runtime

## 4. Slices

### Slice 1 — Landing dispatch contract

- 固定 consumer payload 到 delivery surface 的映射
- 明确 handoff consumer protocol 缺口如何最小补齐
- 明确 review intake 如何接现有 waiting_review surface

当前状态：已完成；Slice 1 设计草案已固定三类 owner surface：handoff 需要显式 consumer protocol、escalation 直接落 `EscalationNotifier.notify()`、reviewer_takeover 通过薄的 review-intake adapter 对齐现有 `waiting_review` / `FeedbackAPI` surface，并明确统一 delivery result contract。

### Slice 2 — Dispatch helper implementation

- 新增最小 landing dispatch helper / protocol
- handoff、escalation、review intake 统一从此处下发
- 固定最小成功/失败返回面

当前状态：已完成并接到真实 owner surface；`src/runtime/orchestration/landing_dispatch.py` 已新增统一 dispatch helper、显式 handoff / review-intake protocol，以及 success/failure 归一化返回面，并已通过 `FileHandoffConsumer` 复用 executor handoff JSON 持久化语义、通过 `FeedbackAPIReviewIntakeConsumer` 接到现有 `FeedbackAPI.register()` pending review surface。

### Slice 3 — Targeted tests completion

- 新增 dispatch targeted tests
- 覆盖 handoff dispatch、escalation dispatch、review intake dispatch 三类路径

当前状态：已完成；`tests/test_runtime_orchestration_landing_dispatch.py` 已新增 7 个 dispatch targeted tests，并与 `tests/test_runtime_orchestration_landing_consumers.py` 联合通过（10 passed）；进一步扩大到 `tests/test_runtime_orchestration*.py` 相关 6 文件的 orchestration 联合验证也已通过（30 passed）。

## 5. Validation gate

- dispatch tests 通过
- dispatch tests 与现有 runtime bridge/orchestration tests 联合通过

当前状态：已满足；owner-surface wiring 后的 dispatch helper 已通过 `tests/test_runtime_orchestration_landing_dispatch.py`、`tests/test_runtime_orchestration_landing_consumers.py` 与 `tests/test_runtime_orchestration*.py` 窄范围联合验证。

## 6. Stop condition

- 当 dispatch contract、helper 与 targeted tests 都已落地并通过窄验证后停止
- 不在本 gate 内进入 daemon/runtime

当前结果：stop condition 已满足；当前 gate 已按边界完成，后续方向已转入 `design_docs/orchestration-bridge-landing-dispatch-integration-followup-direction-analysis.md`，而不是在本 gate 内继续扩大 runtime 范围。