# Phase 11 Manual Foreign-Actor Window Grant Test Guide

## 1. 文档定位

本文件提供 `Phase 11` 的正式手测入口。

本轮手测只覆盖：

- timeline authoritative 下的 `grant`
- timeline predictive 下的 `grant + follow-up + sync`
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
grant slime
quit
```

预期：

- 初始状态行中可看到：
  - `Time 833.33`
  - `Hero(hero) ... AV 0.00`
  - `Slime(slime) ... AV 416.67`
- `grant slime` 后应看到：
  - `Hero grants slime an extra action.`
  - `Timeline: Slime is granted an extra command window after the current turn.`
- 紧接着新的状态行应显示：
  - `Time 833.33 | Current actor: slime |`
- 然后应连续看到两次：
  - `Slime uses Basic Attack.`
- 在第二次 `Slime` 行动结束后，状态行应回到：
  - `Time 1666.67 | Current actor: hero |`

说明：

- 在当前 CLI demo 中，`slime` 属于自动侧，所以 granted turn 与原 future turn 会在同一轮用户输入后连续自动跑完
- 第一次 `Slime uses Basic Attack.` 是刚被插入的 granted window
- 第二次 `Slime uses Basic Attack.` 是它原本未来就会到来的轮次
- 若能连续观察到这两次自动行动，并最终回到 `hero` 回合，就说明原 future slot 被保留了，而不是被授予窗口吞掉

---

## 4. predictive 手测

输入：

```text
grant slime
sync
quit
```

预期：

- 能看到：
  - `Hero grants slime an extra action.`
  - `Timeline: Slime is granted an extra command window after the current turn.`
- 在当前 CLI demo 中，`slime` 属于自动侧，所以预测链会连续打印两次：
  - `Slime uses Basic Attack.`
- `sync` 输出应以：
  - `Sync: kind=`
  开头
- `sync` 后最终状态应回到：
  - `Time 1666.67 | Current actor: hero |`
- `sync` 后不应出现：
  - `command bound to non-current window`
  - granted window 丢失
  - actor / token 错乱

说明：

- 这一轮手测的重点不是只看 `accepted` 还是 `replayed`
- 而是确认 foreign grant 后的 follow-up command 在 predictive / authority 对账后仍保持一致调度结果

---

## 5. subprocess smoke

输入：

```text
grant slime
sync
quit
```

预期：

- subprocess transport 下同样可完成：
  - `grant slime`
  - authority 接受
  - `sync`
- 不应出现 transport 错误或命令绑定错误
- `sync` 后当前 actor 应为：
  - `slime`

---

## 6. 当前不在本轮手测中的内容

本文件明确不覆盖：

- `IMMEDIATE`
- cut-in / interrupt
- 多种 `window_kind`
- 完整 granted window 协调器
- 增量快照
- 第二个 demo slice
