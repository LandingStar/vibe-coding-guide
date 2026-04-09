# M5 手动物理 C/S 测试指南

## 1. 文档定位

本文件用于当前 `M5` 阶段的手动控制台验证。

目标不是验证真实公网网络，而是确认项目已经不再依赖“同进程内直接对象调用”，而是能通过最小 subprocess transport 跑通物理分离的 client/server 主链。

---

## 2. 启动方式

进入项目目录：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
```

启动 predictive + subprocess transport 控制台：

```bash
python3.12 -m client.console_app --predictive --transport subprocess
```

---

## 3. 重点手测路径

### 路径 A：最小物理 C/S 出手闭环

依次输入：

```text
attack slime
sync
quit
```

预期：

- `Hero attacks slime.`
- 敌方自动行动后回到下一状态。
- `sync` 输出一条 `kind=accepted` 的同步状态。

### 路径 B：效果 + 监听器 + 物理 C/S

依次输入：

```text
rally
poison slime
sync
quit
```

预期：

- `Hero uses Rally.`
- `Hero poisons slime.`
- 敌方行动后出现：
  - `Slime suffers 3 poison damage.`
- `sync` 仍能输出可读的权威同步状态。

### 路径 C：强制权威覆盖

依次输入：

```text
resync
quit
```

预期：

- 输出一条 `Sync: kind=resync ...` 或等价可读的同步状态。
- 客户端不会报错退出。

---

## 4. 当前边界

当前 `M5` 仍然有明确限制：

- transport 基于 subprocess/stdin-stdout
- 还不是 socket / websocket
- subprocess transport 下暂不启用 `--network-sim`
- 当前仍只覆盖 `classical_turn + basic_combat`

---

## 5. 通过判定

若以上路径通过，则说明当前项目已经具备：

- 物理分离的最小 client/server 宿主闭环
- 基于 transport 的 command / snapshot / sync 主链
- predictive + resync 在物理 C/S 下的最小可用形态
