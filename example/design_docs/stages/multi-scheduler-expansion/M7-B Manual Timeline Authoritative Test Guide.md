# M7-B Manual Timeline Authoritative Test Guide

## 1. 文档定位

本文件用于手动验证 `M7-B` 的 Timeline authoritative 首切片。

它只覆盖：

- authoritative Timeline
- `basic_combat`
- 本地 CLI / socket CLI

它不覆盖：

- Timeline predictive
- Timeline replay / resync 特化
- 动态速度变化与拉条

---

## 2. 本地 CLI 手测

进入目录：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
```

启动：

```bash
python3.12 -m client.console_app --driver timeline
```

推荐手测顺序：

```text
status
attack slime
status
inject client time 1500
status
resync
status
quit
```

当前预期：

- 初始 `status` 显示 `Time 833.33 | Current actor: hero | ...`
- `attack slime` 后会先看到 `Hero attacks slime.`
- 敌方自动行动后，再次 `status` 应显示 `Time 1666.67 | Current actor: hero | ...`
- `inject client time 1500` 后，本地 `status` 应显示 `Time 1500.00 | ...`
- `resync` 后会恢复回权威状态，再次 `status` 回到 `Time 833.33 | ...` 或当前权威推进后的真实时间

---

## 3. Socket 手测

先启动独立 server：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m server.socket_app --host 127.0.0.1 --port 43117 --driver timeline
```

再在另一个终端连接 client：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --transport socket --attach-server --server-host 127.0.0.1 --server-port 43117 --driver timeline
```

推荐手测顺序：

```text
transport
ping
status
attack slime
status
quit
```

当前预期：

- `transport` 显示 `mode=socket`
- `ping` 显示 `ok=True`
- `status` 显示 `Time ...`
- `attack slime` 后整条 authoritative 主线可继续推进，不出现窗口绑定错误

---

## 4. 当前通过判定

满足以下条件即可判定 `M7-B` 手测通过：

1. Timeline authoritative CLI 能正常启动。
2. `status` 能显示 `Time` 而不是写死 `Round`。
3. `attack slime` 后 enemy auto turn 仍能正常推进。
4. `inject client time ... -> resync` 可以制造并恢复错位。
5. socket attach 模式下，Timeline authoritative 主线可运行。
