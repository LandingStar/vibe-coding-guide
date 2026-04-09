# Phase 6 Timeline Dynamic Speed Slice

## 1. 文档定位

本文件记录 `Phase 6` 的正式落地范围与验收边界。

本阶段只做一条主线：

- **Timeline 的动态速度变化切片**

同步/恢复深化与确定性矩阵在本阶段只作为：

- 验收支撑面
- 调试支撑面

而不是并列主线。

---

## 2. 本阶段目标

`Phase 6` 聚焦以下事情：

1. 让 `timeline` driver 正式响应已提交的 `SpeedChangedEvent`。
2. 让动态速度变化通过既有 attribute / effect 管线进入时间轴，而不是手写旁路逻辑。
3. 让 projection / predictive / replay 主线在这个窄切片下保持正确。
4. 给 CLI 补一条最小可观察技能与调试入口，便于手测。

---

## 3. 已实现内容

- `standard_components/drivers/timeline/driver.py`
  - 新增 `SPEED_CHANGED` 运行时支持
  - 新增 `apply_speed_changed()`
  - `_full_action_value_for()` 已切到 attribute service 的有效速度
- `project_setup.py`
  - timeline runtime 现在会安装 `install_timeline_runtime_support()`
- `standard_components/effects/controller.py`
  - 新增 `HASTE` effect builder
  - 速度类 effect 在 authoritative / prediction 画像下会派发 `SPEED_CHANGED`
  - 速度类 effect 过期移除时也会派发 `SPEED_CHANGED`
- `demo/basic_combat.py`
  - 新增 `HASTE` 指令
  - `APPLY_EFFECT` 已接入 `HASTE`
- `demo/session.py`
  - 新增：
    - `make_haste()`
    - `submit_haste()`
    - `predict_haste()`
- `demo/cli.py`
  - 新增 `haste`
  - `status` 现在显示 `SPD`
  - `inject` 现在支持 `speed`
- `demo/command_reference.py`
  - 已同步新增 `haste`
  - `inject` 的支持字段已补 `speed`

---

## 4. 当前边界

本阶段明确包含：

- `timeline` 下的动态速度变化
- `SpeedChangedEvent` 的 committed rescale
- `HASTE` 这一个最小触发路径
- projection / predictive / replay 下的速度变化正确性
- CLI 的最小调试入口与手测支持

本阶段明确不包含：

- 拉条 / 推条
- `ScheduleAdjustEvent`
- `WindowGrantEvent`
- cut-in / 插队 / 额外窗口
- 自动重连、增量快照、rollback 契约重写
- 速度冻结 / 解冻完整模型
- 第二个 demo slice

---

## 5. 验收依据

- 自动化：
  - `tests/components/test_timeline_driver.py`
  - `tests/integration/test_timeline_projection.py`
  - `tests/integration/test_timeline_prediction.py`
  - `tests/integration/test_demo_cli.py`
  - `tests/acceptance/test_phase6_acceptance.py`
- 手动：
  - `Phase 6 Manual Timeline Dynamic Speed Test Guide.md`
- 统一验证门：
  - `design docs/Verification Gate and Phase Acceptance Workflow.md`

---

## 6. 阶段结论

`Phase 6` 完成后，项目已从“timeline 已接入主线”推进到“timeline 可以处理首个调度动力学变化”。

这意味着：

- `timeline` 不再只是固定速度的主线
- attribute / effect / timeline 三者已出现第一条正式闭环
- 后续若继续深化调度系统，可以再单独切更窄的拉条/推条或高级调度切片
