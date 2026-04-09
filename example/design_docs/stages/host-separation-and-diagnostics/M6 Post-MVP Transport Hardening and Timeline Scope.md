# M6 Localhost Socket Transport and CLI Injection Slice

## 1. 文档定位

本文件记录 `MVP` 验收后的首个 post-MVP 落地切片。

`M6` 的目标不是继续扩 demo 技能，而是把当前的物理 C/S 首切片从 `subprocess + stdio` 推进到真正的 `127.0.0.1` 端口通信，并把错位/恢复调试入口暴露到 CLI。

Timeline driver 在本阶段继续延后，不作为阻塞项。

---

## 2. 本阶段目标

`M6` 聚焦三件事：

1. 提供真实的 localhost socket transport。
2. 允许 client 连接“已存在的独立 server”，而不是只能自动拉起子进程。
3. 通过 CLI 暴露手动注入错位与强制恢复入口，方便后续同步测试。

---

## 3. 已实现内容

- 新增 `server/socket_app.py`
  - 提供基于 `127.0.0.1` 端口的 JSON-lines socket server。
- 新增 `transport/socket_proxy.py`
  - 支持两种模式：
    - 自动拉起 socket server 并连接。
    - attach 到已运行的 socket server。
- 项目入口新增：
  - `tbge-server-socket`
- CLI 已支持：
  - `--transport socket`
  - `--attach-server`
  - `--server-host`
  - `--server-port`
- `demo/session.py` 已支持：
  - socket authoritative 会话
  - socket predictive 会话
  - attach 现有 server 的会话工厂
- CLI 已支持测试注入命令：
  - `inject <client|server|both> <hp|attack|round> ...`
  - `desync ...` 作为 `inject client ...` 的简写
- 当前注入能力可直接用于：
  - 客户端本地错位
  - 仅服务端权威状态变更
  - 双端同时挪动到指定情景

---

## 4. 当前边界

本阶段明确包含：

- 真实 localhost 端口通信
- 独立 server 进程 + 独立 client 进程的 attach 模式
- authoritative / predictive 在 socket transport 下的最小主链
- CLI 层的 desync / resync 调试入口

本阶段明确不包含：

- Timeline driver 主线接入
- 真实网络抖动、超时重试、断线重连
- websocket / HTTP / 多客户端房间
- 多进程下的本地 network simulation 命令集扩展

---

## 5. 验收依据

当前 `M6` 的验收以以下依据为准：

- 自动化测试
  - `tests/integration/test_socket_transport.py`
  - `tests/acceptance/test_m6_acceptance.py`
- 手动 smoke
  - 独立启动 `server.socket_app`
  - 使用 `client.console_app --transport socket --attach-server`
  - 手测 `desync -> resync` 路径

---

## 6. 阶段结论

`M6` 完成后，项目已经不再只是“逻辑上支持物理 C/S”。

当前已具备：

- 独立 server 进程
- 独立 client 进程
- 本地 `127.0.0.1` 端口通信
- CLI 手动注入错位与恢复

这意味着“C/S 彻底分离到 localhost socket 级别”的目标已经达成。
