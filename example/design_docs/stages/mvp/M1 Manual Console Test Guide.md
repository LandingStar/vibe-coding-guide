# 📄 M1 手动控制台测试指引

## 1. 文档定位

本文件用于指导 `M1 / MVP` 首个垂直切片的**手动控制台验收**。

当前手测目标不是覆盖全部异常分支，而是确认：

- 控制台 client 入口可正常启动
- 本地 `ServerHost + ClientHost` 闭环可运行
- 玩家能够通过控制台完成一场最小战斗
- 状态显示、命令输入、自动敌方回合与胜负收束都符合预期

---

## 2. 当前手测前提

默认前提：

- 已进入项目根目录 `turn-based game engine`
- 已使用 Python `3.12`
- 已安装项目依赖（当前仅需 `pytest` 这类开发依赖）

当前正式入口有两种：

1. 脚本入口

```bash
tbge-client-console
```

2. 模块入口

```bash
python3.12 -m client.console_app
```

若当前 shell 尚未暴露 `tbge-client-console`，优先使用第二种模块入口。

---

## 3. 预期最小流程

启动后应看到：

- `Battle started.`
- 当前回合状态行，例如：
  - `Round 1 | Current actor: hero | Hero(hero) HP 30/30 | Slime(slime) HP 25/25`

当前支持的控制台命令：

- `help`
- `status`
- `attack`
- `attack slime`
- `quit`
- `exit`

其中：

- `attack` 会自动选择默认敌方目标
- 敌方回合会自动执行 `Basic Attack`

---

## 4. 推荐手测步骤

### 4.1 启动与帮助

输入：

```text
help
```

预期：

- 输出帮助文本
- 不退出战斗

### 4.2 查看状态

输入：

```text
status
```

预期：

- 额外输出一行当前战场状态
- 不推进回合

### 4.3 完成一场最小战斗

按顺序输入：

```text
attack
attack
attack
```

预期：

- 玩家每次攻击后输出 `Hero attacks slime.`
- 敌方回合输出 `Slime uses Basic Attack.`
- 最终输出 `Winner: player`

### 4.4 非法目标

重新启动后输入：

```text
attack nope
```

预期：

- 输出 `Command rejected: unknown target entity`
- 程序不崩溃
- 当前战斗仍继续，仍可继续输入命令

### 4.5 主动退出

输入：

```text
quit
```

预期：

- 输出 `Battle aborted.`
- 程序正常退出

---

## 5. 日志位置

默认运行日志位于：

- `logs/runtime/`

当前日志分流包括：

- `core.log`
- `driver.log`
- `host_server.log`
- `host_client.log`
- `demo.log`

若手测中出现异常，优先查看：

- `demo.log`
- `host_server.log`
- `core.log`

---

## 6. 当前 M1 手测通过的判定

若以下条件都成立，则可认为 `M1` 手动控制台验收通过：

1. 控制台入口能正常启动。
2. 初始状态能正确显示当前 actor 与双方 HP。
3. `help / status / attack / quit` 都符合预期。
4. 敌方能自动完成回合。
5. 非法目标不会导致程序崩溃。
6. 一场战斗能够以 `Winner: player` 正常收束。

