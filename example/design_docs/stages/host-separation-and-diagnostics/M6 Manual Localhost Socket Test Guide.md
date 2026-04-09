# M6 Manual Localhost Socket Test Guide

## 1. 目标

本手测用于确认以下三件事：

- server 和 client 已能彻底分离为两个本地进程
- 双方通过 `127.0.0.1` 端口通信
- CLI 的 `inject / desync / resync` 可用于同步调试

---

## 2. 启动独立 Server

进入项目目录：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
```

启动 socket server：

```bash
python3.12 -m server.socket_app --host 127.0.0.1 --port 43117
```

也可以使用脚本入口：

```bash
tbge-server-socket --host 127.0.0.1 --port 43117
```

---

## 3. 启动独立 Client

在另一个终端中运行：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --predictive --transport socket --attach-server --server-host 127.0.0.1 --server-port 43117
```

---

## 4. 推荐手测路径

### 基础 authoritative / predictive 通信

输入：

```text
status
attack slime
sync
quit
```

预期：

- `attack slime` 成功生效
- `sync` 能输出最近一次同步状态

### 手动制造客户端错位并恢复

输入：

```text
desync hp slime 1
status
resync
status
quit
```

预期：

- `desync hp slime 1` 后，本地 `slime` HP 显示为 `1/25`
- `resync` 后，本地状态回到权威值
- 再次 `status` 时，`slime` HP 恢复为服务端当前值

### 手动修改权威状态

输入：

```text
inject server attack hero 99
resync
status
quit
```

预期：

- `resync` 后，客户端看到 `hero` 的攻击值被更新为 `99`

---

## 5. 关键日志

日志目录：

- `logs/runtime/demo.log`
- `logs/runtime/host_client.log`
- `logs/runtime/host_server.log`
- `logs/runtime/transport.log`

重点观察：

- socket attach 是否成功
- `inject / desync / resync` 是否按预期落到同步恢复路径
