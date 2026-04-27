# Planning Gate — Orchestration Bridge Landing Consumer Wiring

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/orchestration-bridge-post-landing-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-integration.md` 已完成。

当前已经存在：

1. `BridgeLandingArtifact`
2. handoff / escalation / reviewer_takeover 三类 landing kind
3. 通过 landing helper 落地的 external-resolution boundary

因此当前最明显的空洞是：

- landing artifact 还没有接到现有 consumer surface

## 2. Scope

本 gate 只处理：

1. landing artifact 到现有 consumer surface 的映射 contract
2. landing consumer payload helper 的最小实现
3. landing consumer targeted tests

本 gate 不处理：

1. daemon queue / persistence / replay runtime
2. executor 主流程改写
3. 更厚的 coordinator / landing 历史状态

## 3. Working hypothesis

当前最小可行路线应是：

1. `handoff` 直接复用正式 Handoff schema surface
2. `escalation` 先复用现有 notifier payload surface
3. `reviewer_takeover` 先复用 waiting_review 对齐的最小 review intake payload

## 4. Slices

### Slice 1 — Landing consumer contract

- 固定 `BridgeLandingArtifact` 到现有 consumer surface 的映射
- 明确 handoff / escalation / reviewer_takeover 各自落在哪个现有对象面
- 明确当前不进入 daemon runtime

当前状态：已完成；contract 已固定在 `design_docs/orchestration-bridge-landing-consumer-wiring-slice1-draft.md` 并落地到 payload helper。

### Slice 2 — Consumer payload helper implementation

- 新增 landing consumer payload helper
- handoff 路径复用 handoff validator
- escalation / review 路径复用现有 notifier / waiting_review 对齐 payload

当前状态：已完成；`src/runtime/orchestration/landing_consumers.py` 已新增 consumer payload helper。

### Slice 3 — Targeted tests completion

- 新增 landing consumer targeted tests
- 覆盖 handoff、escalation、reviewer_takeover 三类 payload

当前状态：已完成；`tests/test_runtime_orchestration_landing_consumers.py` 已覆盖 handoff、escalation、reviewer_takeover 三类 payload。

## 5. Validation gate

- landing consumer tests 通过
- landing consumer tests 与现有 runtime bridge/orchestration tests 联合通过

## 6. Stop condition

- 当 consumer contract、helper 与 targeted tests 都已落地并通过窄验证后停止
- 不在本 gate 内进入 daemon runtime

## 7. Close note

当前 gate 已按边界完成：landing consumer contract、payload helper 与 targeted tests 已落地，并与现有 runtime bridge/orchestration 测试联合通过。下一步转入 `design_docs/orchestration-bridge-landing-dispatch-integration-direction-analysis.md`，处理统一 dispatch/delivery contract。