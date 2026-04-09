# Phase 16 Manual Effect Runtime Hook Profile Test Guide

## 1. 目标

手动确认：

- CLI 能显示 runtime hook profiles
- `POISON` 仍在 owner 的 `TURN_END` 结算
- `ATTACK_UP / HASTE` 仍按有限 turn 正常衰减

---

## 2. 启动方式

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app
```

---

## 3. 推荐手测路径

先看 catalog 与 hook profiles：

```text
effects
help effects
```

再测 `POISON`：

```text
poison slime
status
quit
```

可选再测 timeline 下的 `HASTE`：

```bash
python3.12 -m client.console_app --driver timeline
```

```text
haste
status
quit
```

---

## 4. 预期结果

- `effects` 中会同时看到：
  - `Registered effects:`
  - `Runtime hook profiles:`
  - `TURN_END_DECAY`
  - `TURN_END_TICK_DAMAGE_AND_DECAY`
- `poison slime` 后，`status` 会显示 `POISON(1)` 或相应剩余层数
- timeline 下 `haste` 后，`status` 会显示 `HASTE(1)` 且速度提升仍正常
