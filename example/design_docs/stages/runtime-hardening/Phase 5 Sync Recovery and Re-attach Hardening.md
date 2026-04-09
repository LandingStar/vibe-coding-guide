# Phase 5 Sync Recovery and Re-attach Hardening

## 1. 文档定位

本文件记录 `Phase 5` 的正式落地范围与验收边界。

本阶段只做一条主线：

- **同步恢复与重新附着加固**

确定性矩阵与诊断输出在本阶段只作为：

- 验收支撑面
- 调试支撑面

而不是第二条并列主线。

---

## 2. 本阶段目标

`Phase 5` 聚焦以下事情：

1. 让 `socket` transport 支持**手动断开 -> 重新附着 -> 权威恢复**。
2. 让 `subprocess` transport 与 `socket` transport 在**快照注入能力**上保持一致。
3. 让 `sync / recovery / replay / reject / failed` 在远端 transport 下具备更清晰的验收覆盖。
4. 增强 CLI 诊断输出，显式区分 transport 状态与逻辑恢复状态。

---

## 3. 已实现内容

- `transport/socket_proxy.py`
  - 新增 `disconnect()`
  - 新增 `reconnect()`
  - `transport_report()` 已补：
    - `reconnect_supported`
    - `detail`
    - `connection_generation`
- `transport/subprocess_proxy.py`
  - 新增 `apply_snapshot()`
  - `transport_report()` 已补：
    - `reconnect_supported`
    - `detail`
- `demo/session.py`
  - 新增：
    - `disconnect_transport()`
    - `reconnect_transport()`
  - `SyncStatus` 已补：
    - `replayed_count`
    - `dropped_count`
  - `resync_client_to_server_snapshot()` 已支持显式 `sync_kind`
- `demo/cli.py`
  - 新增：
    - `disconnect`
    - `reconnect`
  - `sync` 输出已包含：
    - `replayed`
    - `dropped`
  - `transport` 输出已包含：
    - `reconnect_supported`
    - `generation`
  - `inject` 在 `subprocess` transport 下已不再崩溃
  - transport 错误已在 CLI 内部转成用户可读输出，不再直接炸出交互循环
- `tests/support/scenario_tools.py`
  - `ScenarioSnapshot.apply_to_server()` 已支持 runtime server 与 proxy server 两种路径

---

## 4. 当前边界

本阶段明确包含：

- socket transport 的**手动**断开、重连、恢复
- attach 既有 server 的恢复路径
- subprocess transport 的快照注入一致性
- recovery 相关远端测试矩阵
- CLI 的 transport / sync 诊断增强

本阶段明确不包含：

- 自动重连策略
- reconnect backoff / timeout policy framework
- 增量快照
- 细粒度 rollback 契约重写
- Timeline 高级动力学
- WebSocket / HTTP / 多客户端房间
- `Core` 契约重写

---

## 5. 验收依据

- 自动化：
  - `tests/integration/test_transport_recovery.py`
  - `tests/integration/test_demo_cli.py`
  - `tests/integration/test_socket_transport.py`
  - `tests/integration/test_subprocess_transport.py`
  - `tests/acceptance/test_phase5_acceptance.py`
- 手动：
  - `Phase 5 Manual Recovery and Reconnect Test Guide.md`

---

## 6. 阶段结论

`Phase 5` 完成后，项目当前已经具备：

- socket 下的手动重连恢复闭环
- subprocess 与 socket 一致的快照注入测试面
- 更清晰的 recovery 诊断输出
- 更强的远端 predictive recovery 回归覆盖

这意味着项目已经从“能运行恢复链”推进到“能较稳定地观测、验证和恢复”。

