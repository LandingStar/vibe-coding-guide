# Phase 10 Manual Window Grant Test Guide

## 1. 文档定位

本文件提供 `Phase 10` 的正式手测入口。

本轮手测只覆盖：

- timeline authoritative 下的 `extra`
- timeline predictive 下的 `extra + sync`
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
extra
quit
```

预期：

- 初始状态行中可看到：
  - `Time 833.33`
  - `Hero(hero) ... AV 0.00`
  - `Slime(slime) ... AV 416.67`
- `extra` 后应看到：
  - `Hero grants an extra action.`
  - `Timeline: Hero is granted an extra command window after the current turn.`
- 紧接着新的状态行应显示：
  - `Time 833.33 | Current actor: hero |`

说明：

- 当前时间不会推进
- 当前行动者会再次获得一个新的 command window
- 这仍是最小 after-current grant，不是完整 cut-in

---

## 4. predictive 手测

输入：

```text
extra
sync
quit
```

预期：

- 能看到：
  - `Hero grants an extra action.`
  - `Timeline: Hero is granted an extra command window after the current turn.`
- `sync` 输出应以：
  - `Sync: kind=accepted`
  开头
- `token` 应带：
  - `TIMELINE:turn:`

---

## 5. subprocess smoke

输入：

```text
extra
sync
quit
```

预期：

- subprocess transport 下同样可完成：
  - `extra`
  - authority 接受
  - `sync`
- 不应出现 transport 错误或命令绑定错误

---

## 6. 当前不在本轮手测中的内容

本文件明确不覆盖：

- 完整 cut-in / 插队
- 多种 `insert_mode`
- 多种 `window_kind`
- 自动恢复新策略
- 增量快照
- 第二个 demo slice
