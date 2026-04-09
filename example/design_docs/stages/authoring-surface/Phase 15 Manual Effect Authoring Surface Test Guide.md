# Phase 15 Manual Effect Authoring Surface Test Guide

## 1. 目标

手动确认：

- 当前 runtime 已安装 effect catalog
- CLI 能显示 effect authoring surface
- 现有 `RALLY / HASTE / POISON` 仍通过新的通用构建入口工作

---

## 2. 启动方式

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app
```

---

## 3. 推荐手测路径

先看 catalog：

```text
effects
help effects
```

然后验证现有效果链：

```text
rally
status
quit
```

可选再测 timeline 相关速度效果：

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

- `effects` 会打印：
  - `Registered effects:`
  - `ATTACK_UP`
  - `HASTE`
  - `POISON`
- `help effects` 会显示该命令的详细帮助
- `rally` 后的 `status` 会看到 `ATTACK_UP(1)` 与攻击力提升
- timeline 下 `haste` 后的 `status` 会看到 `HASTE(1)`，并且 `SPD` 已提高
