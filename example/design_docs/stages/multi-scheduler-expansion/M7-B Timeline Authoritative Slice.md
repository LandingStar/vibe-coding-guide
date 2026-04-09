# M7-B Timeline Authoritative Slice

## 1. 文档定位

本文件记录 `M7` 的第二个实际落地切片。

`M7-B` 的目标仍然保持很窄：

- 只接入 `Timeline` 的 authoritative 主线
- 不碰 predictive / replay / resync 的 Timeline 适配
- 不扩内容，不重写 transport，不修改 `Core` 契约

---

## 2. 本阶段目标

`M7-B` 只做以下几件事：

1. 新增最小 `TimelineDriver`，支持开局建 AV 表、相对快进、开窗、关窗与推进到下一行动者。
2. 新增 authoritative client 所需的 Timeline projection。
3. 为 host / CLI / transport 增加显式 driver 选择入口。
4. 补最小的本地、socket、subprocess 回归与 CLI 验收。

---

## 3. 已实现内容

- 新增 `standard_components/drivers/timeline/driver.py`
  - authoritative only
  - 初始速度建表
  - 相对快进
  - `TIMELINE_ADVANCE -> WINDOW_START -> TURN_START`
  - `WINDOW_END -> TURN_END -> TIMELINE_ADVANCE -> WINDOW_START -> TURN_START`
  - `export_state() / import_state()`
  - `sync_projection_state() / import_projection_state()`
- 新增 `standard_components/drivers/timeline/projection.py`
  - authoritative client 可从事件恢复：
    - `current_time`
    - `action_values`
    - `current_turn_actor_id`
    - `current_turn_window_id`
    - `current_turn_binding_token`
- 新增 driver-neutral 调度投影读取：
  - `standard_components/drivers/projection_state.py`
- `project_config.py / config.json`
  - 已增加 `drivers.timeline`
  - 默认 driver 仍保持 `classical_turn`
- `project_setup.py`
  - 新增 `make_timeline_driver()`
  - 新增按 `driver_name` 显式选择 driver / projection 的装配路径
- `demo/cli.py`
  - 新增 `--driver classical_turn|timeline`
  - `status` 不再写死成 `Round`
- `server/stdio_app.py` / `server/socket_app.py`
  - 已支持 `--driver`
- `transport/subprocess_proxy.py` / `transport/socket_proxy.py`
  - 已支持在拉起 server 时透传 `--driver`
- CLI 测试工具补强：
  - `inject ... time ...`

---

## 4. 当前边界

本阶段明确包含：

- `basic_combat`
- authoritative local / subprocess / socket
- Timeline 下的最小 turn-like 窗口生命周期
- Timeline authoritative 的 CLI 可见状态

本阶段明确不包含：

- Timeline predictive
- Timeline replay / resync 特化
- 动态速度变化
- 拉条 / 推条 / 插队
- `ScheduleAdjustEvent` / `WindowGrantEvent` 的 Timeline 主线解释
- 多窗口并存与复杂超量排序

---

## 5. 验收依据

- 自动化：
  - `tests/components/test_timeline_driver.py`
  - `tests/integration/test_timeline_projection.py`
  - `tests/integration/test_socket_transport.py`
  - `tests/integration/test_subprocess_transport.py`
  - `tests/acceptance/test_m7b_acceptance.py`
- 手动 smoke：
  - `client.console_app --driver timeline`
  - `client.console_app --driver timeline --transport socket`
  - CLI 中运行 `status`
  - CLI 中运行 `attack slime`
  - CLI 中运行 `inject client time 1500`
  - CLI 中运行 `resync`

---

## 6. 阶段结论

`M7-B` 完成后，项目已经不再只有 `classical_turn` 一条调度主线。

当前已具备：

- 与现有窗口协议兼容的 Timeline authoritative driver
- authoritative client 下可见的 Timeline 调度状态
- 通过 local / subprocess / socket 选择 Timeline 的最小宿主链

下一步若继续进入 `M7-C`，应只处理：

- Timeline predictive
- Timeline replay / resync
- Timeline 下更稳定的 token / binding / recovery 语义
