# Phase 12 Manual Timeline Immediate Insert Test Guide

## 1. 文档定位

本文件提供 `Phase 12` 的正式手测入口。

本轮手测只覆盖：

- timeline authoritative 下的 `immediate`
- timeline predictive 下的 `immediate + sync`
- subprocess 远端 smoke

---

## 2. 启动方式

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m client.console_app --driver timeline
```

predictive：

```bash
python3.12 -m client.console_app --predictive --driver timeline
```

subprocess smoke：

```bash
python3.12 -m client.console_app --predictive --transport subprocess --driver timeline
```

---

## 3. authoritative 手测

输入：

```text
status
immediate slime
quit
```

预期：

- 初始状态行中可看到：
  - `Time 833.33`
  - `Hero(hero) ... AV 0.00`
  - `Slime(slime) ... AV 416.67`
- `immediate slime` 后应看到：
  - `Hero immediately grants slime an action.`
  - `Timeline: Slime is granted an immediate command window.`
- 紧接着应看到：
  - `Time 833.33 | Current actor: slime |`
- 由于 `slime` 属于自动侧，应继续看到：
  - `Slime uses Basic Attack.`
- 在该次自动行动结束后，状态应回到：
  - `Time 833.33 | Current actor: hero |`

说明：

- 当前时间不会推进
- 原 `Hero` 窗口会被挂起而不是销毁
- `Slime` 的 immediate inserted window 结束后，原窗口会恢复

---

## 4. predictive 手测

输入：

```text
immediate slime
sync
quit
```

预期：

- 能看到：
  - `Hero immediately grants slime an action.`
  - `Timeline: Slime is granted an immediate command window.`
- 在当前 CLI demo 中，`slime` 属于自动侧，因此会继续看到：
  - `Slime uses Basic Attack.`
- 状态应回到：
  - `Time 833.33 | Current actor: hero |`
- `sync` 输出应以：
  - `Sync: kind=accepted`
  开头
- `sync` 的 `actor=` 通常仍会显示 immediate grant 被 authority 接受时的 actor：
  - `actor=slime`
- 不应出现：
  - `command bound to non-current window`
  - token 错乱
  - 当前窗口恢复失败

说明：

- 当前阶段的 `sync` 仍报告“本次被 authority 接受的命令”对应的恢复摘要
- 所以即使界面此时已经因为自动侧行动而回到 `hero`，`sync` 中仍可能显示 `actor=slime`

---

## 5. subprocess smoke

输入：

```text
immediate slime
sync
quit
```

预期：

- subprocess transport 下同样可完成：
  - `immediate slime`
  - authority 接受
  - `sync`
- 不应出现 transport 错误、窗口恢复错误或 token 错乱

---

## 6. 当前不在本轮手测中的内容

本文件明确不覆盖：

- self `IMMEDIATE`
- 完整 cut-in / interrupt
- 多种 `window_kind`
- 完整窗口协调器
- 增量快照
- 第二个 demo slice
