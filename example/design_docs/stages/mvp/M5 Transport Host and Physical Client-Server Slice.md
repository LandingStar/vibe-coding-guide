# 📄 实现规划文档：M5 传输宿主与物理 C/S 首切片

**(Implementation Plan: M5 Transport Host & Physical Client-Server Slice)**

## 1. 文档定位

本文件用于定义并记录 `M4` 收口后的下一阶段主线。

`M4` 已经证明：

- predictive client 可以持有多条 pending command
- 客户端可在权威快照覆盖后稳定 replay
- 本地 loopback network 已足以压测 send / deliver / flush 与对账链路

因此 `M5` 不应继续停留在“单进程内模拟网络”的层面，而应开始验证本项目最早就确立的物理 C/S 方向。

---

## 2. 当前阶段目标

`M5` 的重点目标是：

1. 将当前 loopback 语义提升为**稳定的传输宿主接口**
2. 让 `ServerHost` 与 `ClientHost` 在**物理分离**的进程边界下仍能跑通最小链路
3. 保持当前 `classical_turn + basic_combat + predictive/replay` 行为在新宿主下不退化

换句话说，`M5` 不是追求完整线上联机，而是追求：

- 把“模拟网络”收束成真正可替换的 transport contract
- 把“本地双端会话”收束成最小物理 C/S 切片

---

## 3. 当前计划包含

- 传输契约
  - command outbound envelope
  - snapshot / event inbound envelope
  - 最小 message framing
  - 错误与拒绝语义

- 宿主装配
  - server 进程入口
  - client 进程入口或 transport adapter
  - 让当前 `LocalBattleSession` 不再是唯一驱动方式

- 回归与观测
  - 物理分离宿主下的最小 battle start
  - 一条 predictive command 的往返
  - 至少一条 replay / resync 路径
  - 传输日志与超时/断链的最小观测

- 保持当前边界
  - 不把 transport 细节写进 `Core`
  - 不改变 `Command / Event / Snapshot` 现有协议骨架

---

## 4. 当前明确不做

当前 `M5` 仍不直接包含：

- 真正公网部署级别的网络服务
- websocket/HTTP 与多种协议并行适配
- Timeline driver 的网络预测
- 增量快照压缩
- 图形客户端与表现平滑回滚
- 大规模房间/多玩家/观战系统

---

## 5. 当前已落地切片

当前 `M5` 已落地的最小物理 C/S 切片包括：

- `server/stdio_app.py`
  - 基于 JSON-lines 的最小 server subprocess 宿主
- `transport/subprocess_proxy.py`
  - client 侧 subprocess transport proxy
- `demo/session.py`
  - subprocess session 工厂
- `demo/cli.py`
  - `--transport subprocess`
- `tests/integration/test_subprocess_transport.py`
  - 跨宿主 authoritative / predictive / resync 主链
- `tests/acceptance/test_m5_acceptance.py`
  - 当前阶段自动化验收边界

手测入口见：

- `M5 Manual Physical Client-Server Test Guide.md`

---

## 6. 与 MVP 的关系

本阶段完成后，`MVP` 的关键剩余工作已经全部被覆盖到以下结果：

1. **物理 C/S 首切片已成立**
   - 当前不再只依赖本地 loopback network
   - 已存在 subprocess transport host
   - 已跑通跨进程 battle start / command / sync 主链

2. **宿主与协议最小闭环已成立**
   - command / snapshot / sync report 已具备最小宿主桥接语义
   - accepted / replay / resync 已可跨宿主观测

3. **最小玩法闭环已不再依赖本地直连**
   - `basic_combat`
   - `RALLY / POISON`
   - predictive + replay
   - subprocess transport

4. **自动化验收已覆盖 MVP 收口主线**
   - 物理 C/S 集成测试
   - predictive accepted / replay / resync
   - CLI 跨宿主主链

换句话说，`MVP` 到此已无额外阻塞项；后续重点已从“收口 MVP”切换为：

- **后 MVP 的 transport 加固、第二 driver 与更深的协议/快照能力**

---

## 7. 建议验收线

`M5` 最低验收建议为：

1. server 与 client 不依赖同一进程内直接对象调用
2. 当前 `basic_combat` 能通过 transport host 跑通启动、出手、同步
3. predictive command 至少有一条跨宿主 accepted/replay 路径
4. `resync` 或等价强制覆盖路径在物理 C/S 下仍成立
5. 现有 CLI 或最小宿主壳能观察到 transport 层状态

---

## 8. 当前验收结果

截至当前版本，`M5` 的最低验收建议已经满足，因此阶段状态应视为：

- **`M5` 已完成自动化与手动 smoke 验证**
- **整体 `MVP` 已达到可验收状态**

---

## 9. 当前建议工作顺序

建议按以下顺序推进：

1. 以 `M6` 为起点，继续加固真实 transport adapter
2. 将第二种 driver（Timeline）引入 authoritative 主线
3. 再补增量快照、协议版本与 determinism 测试

不建议的顺序：

- 在真实 transport adapter 还没成型前就大规模扩 Timeline 预测
- 在第二种 driver 还没进入主线前就先做大量表现/UI 工作
