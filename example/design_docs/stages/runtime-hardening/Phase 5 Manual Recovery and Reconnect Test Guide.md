# Phase 5 Manual Recovery and Reconnect Test Guide

## 1. 目标

本手测用于验证 `Phase 5` 的两条关键路径：

- socket transport 的断开、重连与恢复
- subprocess transport 的 server-only 注入与 resync

---

## 2. Socket 重连恢复

### 2.1 启动独立 server

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m server.socket_app --host 127.0.0.1 --port 43117
```

### 2.2 启动 attach client

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --transport socket --attach-server --server-host 127.0.0.1 --server-port 43117
```

### 2.3 推荐命令序列

```text
transport
disconnect
transport
ping
reconnect
sync
quit
```

### 2.4 通过判定

- `disconnect` 后 `transport` 显示 `connected=False`
- `ping` 返回失败但 CLI 不崩
- `reconnect` 后 `transport` 显示 `connected=True`
- `sync` 显示 `kind=reconnect`

---

## 3. Subprocess 注入恢复

### 3.1 启动 CLI

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --transport subprocess
```

### 3.2 推荐命令序列

```text
inject server hp slime 1
resync
status
quit
```

### 3.3 通过判定

- `inject server hp slime 1` 不崩溃
- `resync` 成功
- `status` 中可看到 `Slime(slime) HP 1/25`

