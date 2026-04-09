# M4 手动本地网络模拟测试指南

## 1. 文档定位

本文件用于当前 `M4` 阶段的手动控制台验证。

目标不是验证真实网络层，而是确认当前本地 loopback network 切片已经能把：

- 多 pending command
- send / deliver / flush
- 权威 snapshot 回传与 replay

这几条链路稳定跑通。

---

## 2. 启动方式

进入项目目录：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
```

启动 predictive + network simulation 控制台：

```bash
python3.12 -m client.console_app --predictive --network-sim
```

---

## 3. 重点手测路径

### 路径 A：最小多 pending + flush 闭环

依次输入：

```text
attack slime
pending
flush
sync
quit
```

预期：

- `attack slime` 后会先看到：
  - `Predicted: Hero attacks slime.`
- 随后客户端会把敌方自动回合也一起本地预测，因此还会看到：
  - `Predicted Slime uses Basic Attack.`
- `pending` 或 `net` 会显示当前 network 状态，通常能看到：
  - `pending=2`
- `flush` 后应看到：
  - `Network: flushed ...`
  - `Sync: kind=accepted ... actor=hero ...`
- 最终应回到 `hero` 回合，且 pending 清空。

### 路径 B：分步 send / deliver

依次输入：

```text
attack slime
send
deliver
send
deliver
sync
quit
```

预期：

- 第一次 `send` / `deliver` 后，client 仍可能保留剩余 pending。
- 第二次 `send` / `deliver` 后，pending 应清空。
- `sync` 应显示最近一次同步状态，形如：
  - `Sync: kind=accepted ...`

### 路径 C：跨多回合累积 pending

依次输入：

```text
attack slime
rally
queue
flush
sync
quit
```

预期：

- `attack slime` 与 `rally` 之间不需要先 `flush`。
- `queue` 应能看到不止一条 pending command。
- `flush` 后应成功清空 pending，并保持客户端/服务端状态一致。

---

## 4. 当前已知边界

当前 `M4` 切片仍有明确限制：

- 仍然只覆盖 `classical_turn`
- 仍然是本地 loopback network，不是真实 socket / websocket
- 还没有 Timeline driver 下的预测 / 回滚
- 还没有增量快照压缩

因此当前手测目标是：

- 验证多 pending
- 验证 send / deliver / flush
- 验证 snapshot 覆盖后 replay 的基本稳定性

而不是：

- 验证完整线上联机系统

---

## 5. 通过判定

若以上路径均通过，则说明当前项目已经到达：

- `M4` 的**手测停靠点**

此时下一步应由主开发决定：

1. 是否直接收口 `M4`
2. 还是继续补一轮更明确的宿主/UI 同步契约
3. 或继续推进更真实的网络模拟与多命令 token 策略
