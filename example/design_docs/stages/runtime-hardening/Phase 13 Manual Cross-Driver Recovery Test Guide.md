# Phase 13 Manual Cross-Driver Recovery Test Guide

## 1. 目标

本手测用于确认：

- `classical_turn` 与 `timeline` 两条 driver 都支持 predictive socket 自动恢复
- `recover`、`transport`、`sync` 的 CLI 输出仍可观察

---

## 2. classical_turn 自动恢复

启动：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --predictive --transport socket --driver classical_turn
```

输入：

```text
disconnect
rally
transport
sync
quit
```

预期：

- `rally` 不会因为断链直接失败
- `transport` 会显示：
  - `connected=True`
  - `last_recovery=command:ok:recover:cmd_...`
- `sync` 会显示：
  - `kind=accepted`
  - `token=STRICT_TURN:turn:...`

---

## 3. classical_turn 手动 recover

启动同上。

输入：

```text
disconnect
recover
transport
sync
quit
```

预期：

- 会输出 `Recovery: trigger=manual ... succeeded=True`
- `transport` 显示 `last_recovery=manual:ok:recover:-`
- `sync` 显示 `kind=recover`

---

## 4. timeline 回归确认

启动：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --predictive --transport socket --driver timeline
```

输入：

```text
disconnect
rally
transport
sync
quit
```

预期：

- timeline 仍可自动恢复
- `transport` 显示 `last_recovery=command:ok:recover:cmd_...`
- `sync` 显示 `token=TIMELINE:turn:...`

---

## 5. 收口说明

若上述三条都通过，则说明本阶段“跨 driver 的最小 recovery 泛化”目标已满足。
