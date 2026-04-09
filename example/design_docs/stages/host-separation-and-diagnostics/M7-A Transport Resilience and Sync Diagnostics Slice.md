# M7-A Transport Resilience and Sync Diagnostics Slice

## 1. 文档定位

本文件记录 `M7` 的第一个实际落地切片。

`M7-A` 的目标很窄：

- 不碰 Timeline
- 不扩内容
- 先把 transport 诊断与同步观测能力补成正式接口

---

## 2. 本阶段目标

`M7-A` 只做以下几件事：

1. 给 transport 增加更明确的错误分类。
2. 给 session / CLI 暴露 transport 状态与 ping 能力。
3. 补最小的 acceptance 与回归测试。

---

## 3. 已实现内容

- 新增 `transport/errors.py`
  - `TransportError`
  - `TransportConnectionError`
  - `TransportProtocolError`
- `subprocess_proxy.py` 与 `socket_proxy.py` 已支持：
  - `ping()`
  - `transport_report()`
- `ServerHost` 已支持：
  - `ping()`
  - `transport_report()`
- `LocalBattleSession` 已支持：
  - `transport_status()`
  - `ping_transport()`
- CLI 已新增：
  - `transport`
  - `ping`
- `main()` 现在会把 transport 层异常按可读错误返回到终端。
- `CLI Command Reference.md` 与 `help` 已同步覆盖这两个新指令。

---

## 4. 当前边界

本阶段明确包含：

- transport 观测
- transport 健康检查
- socket / subprocess / local 三种模式下的统一输出

本阶段明确不包含：

- reconnect 自动化
- 断链恢复策略
- websocket transport
- Timeline 主线

---

## 5. 验收依据

- 自动化：
  - `tests/integration/test_demo_cli.py`
  - `tests/acceptance/test_m7a_acceptance.py`
  - `tests/core/test_command_reference.py`
- 手动 smoke：
  - `client.console_app --transport socket`
  - 在 CLI 中运行 `transport`
  - 在 CLI 中运行 `ping`

---

## 6. 阶段结论

`M7-A` 完成后，项目已经不再只能“看到同步结果”。

当前 CLI 已可以直接看到：

- 当前 transport 模式
- 当前 endpoint
- 当前连接状态
- server 进程所有权
- 当前 authority ping 结果

这为后续真正推进 reconnect、timeout、Timeline 接入提供了稳定的观测底座。
