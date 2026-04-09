# Phase 14 Manual Determinism Matrix Test Guide

## 1. 目标

本手测用于确认：

- 默认 determinism matrix 可以被直接运行
- 输出中能看到固定场景与组合摘要
- 工具返回 `PASS`

---

## 2. 运行方式

优先推荐在项目根目录执行：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
python3.12 -m tools.verification_platform.cli
```

如果项目已安装脚本入口，也可执行：

```bash
cd "/home/landingstar/workspace/turn-based game engine"
tbge-verify-matrix
```

---

## 3. 预期输出

输出中应至少包含：

- `Verification matrix report`
- `Cases: 14`
- `authoritative_basic_attack`
- `predictive_rally_commit`
- `predictive_disconnect_recover_rally`
- `Result: PASS`

---

## 4. 观察重点

这轮手测不检查逐行日志，而应关注：

- 两条 driver 是否都被覆盖
- `local / subprocess / socket` 是否都出现在矩阵中
- recovery 场景是否仍然返回 `accepted`
- 最终整体是否为 `PASS`

---

## 5. 说明

如果未来 Phase 扩展了 matrix 场景数量，本手测文档应同步更新。

但更新原则仍应保持：

- 以 canonical 场景为单位扩展
- 不因新组件增加而做无脑全组合
