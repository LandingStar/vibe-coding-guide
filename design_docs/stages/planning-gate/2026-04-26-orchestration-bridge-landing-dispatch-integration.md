# Planning Gate — Orchestration Bridge Landing Dispatch Integration

> 日期: 2026-04-26
> 状态: PAUSED
> 关联方向分析: `design_docs/orchestration-bridge-landing-dispatch-integration-direction-analysis.md`

> 中断说明: 2026-04-26 用户将主线显式切换到 `project progress multi-graph` 能力；本 gate 尚未完成 Slice 1，因此暂停于 dispatch contract 入口，等待新主线告一段落后再恢复。

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

当前状态：Slice 1 设计草案已创建为 `design_docs/orchestration-bridge-landing-dispatch-integration-slice1-draft.md`。

### Slice 2 — Dispatch helper implementation

- 新增最小 landing dispatch helper / protocol
- handoff、escalation、review intake 统一从此处下发
- 固定最小成功/失败返回面

当前状态：未开始。

### Slice 3 — Targeted tests completion

- 新增 dispatch targeted tests
- 覆盖 handoff dispatch、escalation dispatch、review intake dispatch 三类路径

当前状态：未开始。

## 5. Validation gate

- dispatch tests 通过
- dispatch tests 与现有 runtime bridge/orchestration tests 联合通过

## 6. Stop condition

- 当 dispatch contract、helper 与 targeted tests 都已落地并通过窄验证后停止
- 不在本 gate 内进入 daemon/runtime