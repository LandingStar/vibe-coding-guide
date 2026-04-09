# Phase 9 Manual Timeline Delay Test Guide

## 1. 文档定位

本文件提供 `Phase 9` 的正式手测入口。

本轮手测只覆盖：

- timeline authoritative 下的 `delay`
- timeline predictive 下的 `delay + sync`
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
delay slime
quit
```

预期：

- 初始状态行中可看到：
  - `Time 833.33`
  - `Hero(hero) ... AV 0.00`
  - `Slime(slime) ... AV 416.67`
- `delay slime` 后应看到：
  - `Hero delays slime.`
  - `Timeline: Slime delayed by 50.00% (AV 416.67 -> 1041.67).`
- 紧接着下一轮状态行应显示：
  - `Time 1666.67 | Current actor: hero |`

说明：

- `delay` 在本阶段不会开新窗口，只会改变未来排序
- 由于 `50%` 足够把 `slime` 推到 `hero` 之后，所以 `hero` 会再次拿到下一次行动

---

## 4. predictive 手测

输入：

```text
delay slime
sync
quit
```

预期：

- 能看到：
  - `Hero delays slime.`
  - `Timeline: Slime delayed by 50.00% ...`
- `sync` 输出应以：
  - `Sync: kind=accepted`
  开头
- `token` 应带：
  - `TIMELINE:turn:`

---

## 5. subprocess smoke

输入：

```text
delay slime
sync
quit
```

预期：

- subprocess transport 下同样可完成：
  - `delay`
  - authority 接受
  - `sync`
- 不应出现 transport 错误或命令绑定错误

---

## 6. 当前不在本轮手测中的内容

本文件明确不覆盖：

- `WindowGrantEvent`
- cut-in / 插队 / 额外窗口
- 自动重连新策略
- 增量快照
- 第二个 demo slice
