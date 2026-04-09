# Phase 9 Timeline Delay Slice

## 1. 文档定位

本文件记录 `Phase 9` 的正式落地范围与验收边界。

本阶段只做一条主线：

- **Timeline 下 `DELAY + NORMALIZED_PERCENT` 的首个对称调度切片**

它建立在 `Phase 7` 已完成的 `ADVANCE + NORMALIZED_PERCENT` 之上，但不继续扩展到窗口授予、插队或更复杂的 cut-in 语义。

---

## 2. 本阶段目标

`Phase 9` 只回答一个问题：

**`ScheduleAdjustEvent(operation_kind=DELAY, value_unit=NORMALIZED_PERCENT)` 在 timeline 下如何稳定、确定性地解释。**

本阶段聚焦以下事情：

1. 让 `timeline` runtime 正式支持 `DELAY`
2. 继续只支持：
   - `value_unit = NORMALIZED_PERCENT`
3. 提供一条最小 demo 触发路径
4. 让 authoritative / projection / predictive / replay 都能闭环观察并重放这条链
5. 给 CLI 补最小可观察面，确保无需只看日志

---

## 3. 数学与语义收束

本阶段延续 `Phase 7` 对 `NORMALIZED_PERCENT` 的定义：

- 仍按完整调度周期解释，而不是按当前剩余 `AV`

在 `timeline` 中，本阶段采用：

```text
delta_action_value = full_cycle_action_value * (percent / 100)
adjusted_action_value = current_action_value + delta_action_value
```

其中：

- `full_cycle_action_value = base_distance / current_speed`
- `current_speed` 仍由 attribute service 求值

这意味着：

- `50%` delay 会把目标的未来行动窗口推远半个完整周期
- 当前轮结束后，若被 delay 的目标已被推到其它实体之后，下一行动者会相应改变
- 本阶段仍不引入额外窗口，只改变未来排序

---

## 4. 已实现内容

- `standard_components/drivers/timeline/driver.py`
  - `SCHEDULE_ADJUST` 现已同时支持：
    - `ADVANCE`
    - `DELAY`
  - `DELAY` 仍只接受：
    - `NORMALIZED_PERCENT`
- `demo/basic_combat.py`
  - 新增 `DELAY` 指令
  - `DELAY` 会发出 `SCHEDULE_ADJUST(operation_kind=DELAY)`
- `demo/session.py`
  - 新增：
    - `make_delay()`
    - `submit_delay()`
    - `predict_delay()`
- `demo/cli.py`
  - 新增：
    - `delay [target_id]`
  - `SCHEDULE_ADJUST` 消息现会区分：
    - `advanced`
    - `delayed`
- `demo/command_reference.py`
  - 已同步新增 `delay`
- `design docs/CLI Command Reference.md`
  - 与 `demo/command_reference.py` 保持同步
- 验证增强
  - 已补非对称注入恢复测试，覆盖：
    - `Phase 6` 的速度变化链
    - `Phase 7` 的 `pull`
    - `Phase 8` 的 timeline recovery

---

## 5. 当前边界

本阶段明确包含：

- `timeline` 下的 `DELAY + NORMALIZED_PERCENT`
- 一个最小 demo 命令：
  - `delay`
- authoritative / projection / predictive / replay 的最小闭环
- 至少一条远端 smoke
- CLI / 手测 / acceptance / 帮助同步

本阶段明确不包含：

- `WindowGrantEvent`
- cut-in / 插队 / 额外窗口
- `DRIVER_NATIVE`
- 增量快照
- rollback 契约重写
- 第二个 demo slice
- transport 平台化改造

---

## 6. 验收依据

- 自动化：
  - `tests/components/test_timeline_driver.py`
  - `tests/integration/test_timeline_projection.py`
  - `tests/integration/test_timeline_prediction.py`
  - `tests/integration/test_subprocess_transport.py`
  - `tests/integration/test_demo_cli.py`
  - `tests/acceptance/test_phase9_acceptance.py`
- 手动：
  - `Phase 9 Manual Timeline Delay Test Guide.md`
- 统一验证门：
  - `design docs/Verification Gate and Phase Acceptance Workflow.md`

---

## 7. 阶段结论

`Phase 9` 完成后，项目已经具备：

- `timeline` 下首个对称的主动调度操作对
  - `ADVANCE`
  - `DELAY`
- `delay` 对未来行动顺位的可观测影响
- 对称调度操作在 authoritative / projection / predictive / replay / 远端 smoke 下的闭环

这意味着：

- `timeline` 已经不只会把目标拉近，也能把目标推远
- 当前主动调度协议已经具备继续进入更复杂窗口语义前的最小对称性
- 若继续深化，下一层更自然的是：
  - `WindowGrantEvent`
  - 或更复杂的 cut-in / 额外窗口

因此 `Phase 9` 应在这里收口，而不是继续把窗口授予或恢复深化混入同一阶段。
