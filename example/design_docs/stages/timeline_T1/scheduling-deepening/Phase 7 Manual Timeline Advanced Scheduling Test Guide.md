# Phase 7 Manual Timeline Advanced Scheduling Test Guide

## 1. 文档定位

本文件提供 `Phase 7` 的正式手测入口。

本轮手测只覆盖：

- timeline authoritative 下的 `pull`
- timeline predictive 下的 `pull + sync`
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
pull slime
quit
```

预期：

- 初始状态行中可看到：
  - `Time 833.33`
  - `Hero(hero) ... AV 0.00`
  - `Slime(slime) ... AV 416.67`
- `pull slime` 后应看到：
  - `Hero pulls slime closer.`
  - `Timeline: Slime advanced by 25.00% (AV 416.67 -> 104.17).`
- 紧接着下一轮状态行应显示：
  - `Time 937.50 | Current actor: slime |`

说明：

- CLI 会先打印新的 timeline 状态，再自动执行敌方回合
- 这正是本阶段要暴露的“未来顺位被主动拉近”的可观察面

---

## 4. predictive 手测

输入：

```text
pull slime
sync
quit
```

预期：

- 能看到：
  - `Hero pulls slime closer.`
  - `Timeline: Slime advanced by 25.00% ...`
- `sync` 输出应以：
  - `Sync: kind=accepted`
  开头
- `token` 应带：
  - `TIMELINE:turn:`

---

## 5. subprocess smoke

输入：

```text
pull slime
sync
quit
```

预期：

- subprocess transport 下同样可完成：
  - `pull`
  - authority 接受
  - `sync`
- 不应出现 transport 错误或命令绑定错误

---

## 6. 当前不在本轮手测中的内容

本文件明确不覆盖：

- `DELAY`
- `WindowGrantEvent`
- cut-in / 插队
- 自动重连
- 增量快照
- 第二个 demo slice
