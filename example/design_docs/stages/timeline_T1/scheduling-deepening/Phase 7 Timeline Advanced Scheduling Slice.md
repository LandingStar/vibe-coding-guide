# Phase 7 Timeline Advanced Scheduling Slice

## 1. 文档定位

本文件记录 `Phase 7` 的正式落地范围与验收边界。

本阶段只做一条主线：

- **Timeline 下的首个主动调度操作切片**

更具体地说，就是：

- `ScheduleAdjustEvent`
- `ADVANCE + NORMALIZED_PERCENT`

其它调度操作、窗口插入与恢复深化不在本阶段展开。

---

## 2. 本阶段目标

`Phase 7` 只回答一个问题：

**当业务层发出调度器调整事件时，`timeline` 要如何稳定、确定性地解释它。**

本阶段聚焦以下事情：

1. 让 `timeline` runtime 正式支持 `ScheduleAdjustEvent`
2. 只支持：
   - `operation_kind = ADVANCE`
   - `value_unit = NORMALIZED_PERCENT`
3. 提供一条最小 demo 触发路径
4. 让 projection / predictive / replay 能正确观察并重放这条链
5. 给 CLI 补最小可观察面，确保手测无需只看日志

---

## 3. 数学与语义收束

本阶段对 `NORMALIZED_PERCENT` 做了明确收束：

- 以 [[Scheduling Adjustment and Window Grant Protocol|调度调整与窗口授予协议]] 为准
- 按**完整调度周期**解释，而不是按“当前剩余 AV”解释

在 `timeline` 中，本阶段采用：

```text
delta_action_value = full_cycle_action_value * (percent / 100)
adjusted_action_value = current_action_value - delta_action_value
```

其中：

- `full_cycle_action_value = base_distance / current_speed`
- `current_speed` 仍由 attribute service 求值

这意味着：

- `25%` 拉条会减少目标一个完整周期的 `25% AV`
- 允许目标被拉过零
- 当多个实体 `AV <= 0` 时，行动权选择按 [[timeline system|时间轴文档]] 中的超量距离规则处理，而不是只看原始 AV

---

## 4. 已实现内容

- `standard_components/drivers/timeline/driver.py`
  - 新增 `SCHEDULE_ADJUST` runtime 支持
  - 新增 `apply_schedule_adjust()`
  - 新增 `ADVANCE + NORMALIZED_PERCENT` 校验
  - 新增超量距离优先的 due actor 选择
- `standard_components/drivers/projection_state.py`
  - timeline projection 现在暴露 `action_values`
- `demo/basic_combat.py`
  - 新增 `PULL` 指令
  - `PULL` 会发出 `SCHEDULE_ADJUST`
- `demo/session.py`
  - 新增：
    - `make_pull()`
    - `submit_pull()`
    - `predict_pull()`
- `demo/cli.py`
  - 新增 `pull [target_id]`
  - `status` 在 timeline 下现在显示 `AV`
  - 命令结算消息现在会输出最小 schedule adjust 结果
- `demo/command_reference.py`
  - 已同步新增 `pull`
  - `status` 的说明已同步补 `AV`

---

## 5. 当前边界

本阶段明确包含：

- `ScheduleAdjustEvent` 的 timeline runtime 支持
- 仅支持：
  - `ADVANCE`
  - `NORMALIZED_PERCENT`
- 一个最小 demo 命令：
  - `pull`
- authoritative 下的 AV 重算与排序更新
- projection / predictive / replay 的最小兼容
- 至少一条远端 smoke

本阶段明确不包含：

- `DELAY`
- `DRIVER_NATIVE`
- `WindowGrantEvent`
- cut-in / 绝对插队 / 额外窗口
- 自动重连、增量快照、rollback 契约改写
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
  - `tests/acceptance/test_phase7_acceptance.py`
- 手动：
  - `Phase 7 Manual Timeline Advanced Scheduling Test Guide.md`
- 统一验证门：
  - `design docs/Verification Gate and Phase Acceptance Workflow.md`

---

## 7. 阶段结论

`Phase 7` 完成后，项目已经不只具备：

- timeline 的动态速度变化

还具备：

- timeline 下首个主动调度操作的正式解释

这意味着：

- `timeline` 已经从“被动响应速度变化”推进到“主动调整未来顺位”
- 当前调度协议、projection 与 predictive/replay 结构已经证明可继续承接下一层复杂度
- 后续若继续深化，要么进入更复杂的调度语义，要么转向同步/恢复深化；不宜在本阶段继续堆更多 operation 或窗口插入语义
