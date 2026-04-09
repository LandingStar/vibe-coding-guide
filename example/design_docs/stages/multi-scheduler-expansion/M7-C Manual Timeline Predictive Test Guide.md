# M7-C Manual Timeline Predictive Test Guide

## 1. 文档定位

本文件用于手动验证 `M7-C` 的 Timeline predictive / replay / resync 首切片。

它只覆盖：

- `basic_combat`
- Timeline predictive
- 现有 pending / replay / sync / network simulation 主线

---

## 2. 本地 predictive 手测

进入目录：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
```

启动：

```bash
python3.12 -m client.console_app --predictive --driver timeline
```

推荐手测顺序：

```text
attack slime
sync
quit
```

当前预期：

- 会先看到 `Hero attacks slime.`
- 敌方自动行动后，本地回到 `hero`
- `sync` 显示 `kind=accepted`
- `token=` 前缀为 `TIMELINE:turn:`

---

## 3. 本地 network simulation 手测

启动：

```bash
python3.12 -m client.console_app --predictive --network-sim --driver timeline
```

推荐手测顺序：

```text
attack slime
flush
sync
quit
```

当前预期：

- 会看到 `Predicted: Hero attacks slime.`
- 会看到 `Predicted Slime uses Basic Attack.`
- `flush` 结束后回到 `hero`
- `sync` 显示 `kind=accepted`
- `token=` 前缀为 `TIMELINE:turn:`

---

## 4. Socket predictive 手测

先启动独立 server：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m server.socket_app --host 127.0.0.1 --port 43117 --driver timeline
```

再在另一个终端连接 client：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --predictive --transport socket --attach-server --server-host 127.0.0.1 --server-port 43117 --driver timeline
```

推荐手测顺序：

```text
rally
resync
sync
quit
```

当前预期：

- `rally` 后本地会进入 pending / 预测状态
- `resync` 后仍能恢复到带有 `ATTACK_UP` 的正确状态
- `sync` 会显示 replay / resync 后的恢复结果

---

## 5. 当前通过判定

满足以下条件即可判定 `M7-C` 手测通过：

1. Timeline predictive CLI 可以正常启动。
2. `sync` / `resync` 输出中可见 `TIMELINE:turn:` token。
3. 本地 network simulation 下 `flush` 能回到玩家回合。
4. socket predictive 下，Timeline 的 replay / resync 不会出现窗口绑定错误。
