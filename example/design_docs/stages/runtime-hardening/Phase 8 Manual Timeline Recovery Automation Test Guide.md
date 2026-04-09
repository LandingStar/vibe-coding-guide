# Phase 8 Manual Timeline Recovery Automation Test Guide

## 1. 文档定位

本文件用于手动验证 `Phase 8` 的当前目标：

- `socket + predictive + timeline` 下的最小自动恢复闭环

---

## 2. 启动方式

### 2.1 本地自拉起 socket server

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --predictive --transport socket --driver timeline
```

### 2.2 连接既有 socket server

先启动 server：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m server.socket_app --host 127.0.0.1 --port 43117 --driver timeline
```

再启动 client：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --predictive --transport socket --attach-server --server-host 127.0.0.1 --server-port 43117 --driver timeline
```

---

## 3. 手测路径

### 3.1 命令提交触发自动恢复

在 client 中输入：

```text
disconnect
pull slime
transport
sync
quit
```

预期：

- `pull slime` 不应直接报 transport 错误。
- 之后 `transport` 应显示：
  - `connected=True`
  - `auto_recover=yes`
  - `last_recovery=command:ok:recover:cmd_...`
- `sync` 应显示：
  - `kind=accepted`
  - `token=TIMELINE:turn:...`

### 3.2 手动 recover 命令

在 client 中输入：

```text
disconnect
recover
transport
sync
quit
```

预期：

- 会先看到一条 `Recovery: ...` 输出
- `transport` 应显示：
  - `connected=True`
  - `last_recovery=manual:ok:recover:-`
- `sync` 应显示：
  - `kind=recover`

### 3.3 attach 既有 server 路径

在 attach-server 模式下重复 `3.2`。

预期：

- 恢复链仍然成立
- 不要求 client 拥有 server 进程

---

## 4. 当前不验证的内容

本手测不要求覆盖：

- 增量快照
- 自动 backoff
- `DELAY`
- `WindowGrantEvent`
- rollback 改写

因为这些不属于 `Phase 8` 的范围。
