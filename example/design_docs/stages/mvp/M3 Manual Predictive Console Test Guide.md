# M3 手动 Predictive 控制台测试指南

## 1. 文档定位

本文件用于当前 `M3` 阶段的手动控制台验证。

目标不是覆盖完整网络同步系统，而是确认当前已落地的首切片在本地 predictive CLI 中可观察、可操作、可恢复。

---

## 2. 启动方式

进入项目目录：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
```

启动 predictive 控制台：

```bash
python3.12 -m client.console_app --predictive
```

或：

```bash
tbge-client-console --predictive
```

---

## 3. 重点手测路径

### 路径 A：最小预测闭环

依次输入：

```text
attack slime
sync
quit
```

预期：

- `Hero attacks slime.`
- 敌方自动行动后回到 `hero` 回合。
- `sync` 输出最近一次恢复报告，形如：
  - `Sync: kind=accepted snapshot=... revision=... pending=0 command=cmd_... actor=slime token=STRICT_TURN:turn:...`

### 路径 B：主动 resync

依次输入：

```text
resync
quit
```

预期：

- 输出一条 `Sync: kind=resync ...` 开头的同步报告。
- 报告中应包含当前 `actor` 与 `token`。
- 战场状态保持一致，不应报错。

### 路径 C：Rally 后下一回合继续行动

依次输入：

```text
rally
attack slime
quit
```

预期：

- `rally` 后敌方正常自动出手。
- 下一回合 `hero` 可以正常行动。
- 不应再出现：
  - `Command rejected: command bound to non-current window`

### 路径 D：查看帮助与当前状态

依次输入：

```text
help
status
quit
```

预期：

- `help` 中应包含：
  - `sync`
  - `resync`
- `status` 可正常显示当前回合、HP、ATK 与效果摘要。

---

## 4. 当前已知边界

当前 `M3` 首切片仍有明确限制：

- 只支持**单条 pending command**
- 还没有真实异步网络层
- 还没有多命令跨窗口重播
- 还没有 Timeline driver 下的预测重播

因此当前手测的目标是：

- 验证最小预测链
- 验证快照恢复与宿主可见同步报告
- 验证 `resync` 后 projection-only client 仍能恢复当前 actor / window / token
- 验证控制台桥接是否稳定

而不是：

- 验证完整线上同步系统

---

## 5. 通过判定

若以上路径均通过，则说明当前项目已经到达：

- `M3` 首切片的**手测停靠点**

此时下一步应由主开发对以下方向做选择：

1. 继续扩 `SyncRecoveryReport` 的宿主/UI 桥接。
2. 扩当前 `classical_turn` 的稳定 token 策略，为多 pending command 铺路。
3. 进入更真实的网络模拟。
