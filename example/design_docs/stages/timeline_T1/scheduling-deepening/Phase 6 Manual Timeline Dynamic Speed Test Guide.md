# Phase 6 Manual Timeline Dynamic Speed Test Guide

## 1. 目标

本手测用于验证 `Phase 6` 的三条关键路径：

- authoritative timeline 下的 `haste`
- predictive timeline 下的 `haste`
- CLI 的 `inject ... speed ...` 与 `resync`

---

## 2. Authoritative Timeline

### 2.1 启动

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --driver timeline
```

### 2.2 推荐命令序列

```text
haste
status
quit
```

### 2.3 通过判定

- 输出 `Hero uses Haste.`
- 在 `haste` 的即时输出中，可看到：
  - `Time 1250.00`
  - `Current actor: slime`
  - `Hero(hero) ... SPD 18`
- 随后敌方自动回合会把控制权带回 `hero`
- `status` 时仍可看到 `Hero(hero) ... SPD 18`

---

## 3. Predictive Timeline

### 3.1 启动

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --predictive --driver timeline
```

### 3.2 推荐命令序列

```text
haste
sync
quit
```

### 3.3 通过判定

- 输出 `Hero uses Haste.`
- `sync` 显示 `kind=accepted`
- `sync` 中的 `token` 以 `TIMELINE:turn:` 开头

---

## 4. 速度注入与恢复

### 4.1 启动

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --driver timeline
```

### 4.2 推荐命令序列

```text
inject client speed hero 18
status
resync
status
quit
```

### 4.3 通过判定

- `inject` 输出 `Injected client snapshot: speed hero=18.`
- 第一次 `status` 可看到 `Hero(hero) ... SPD 18`
- `resync` 成功
- 第二次 `status` 可看到 `Hero(hero) ... SPD 12`
