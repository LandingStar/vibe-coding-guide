# Planning Gate — 状态面一致性收口

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-14-state-surface-consistency-closeout |
| Scope | Checklist / Phase Map / CURRENT / checkpoint 当前状态叙事对齐 |
| Status | **COMPLETED** |
| 来源 | `design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`.codex/handoffs/CURRENT.md`、`.codex/checkpoints/latest.md`、本轮 v0.9.3 release 自动化复验 |
| 前置 | v0.9.3 release 自动化复验完成；当前无 active planning-gate |
| 测试基线 | 823 passed, 2 skipped |

## 问题陈述

当前 4 个关键状态面已经出现叙事漂移：

1. `design_docs/Project Master Checklist.md` 当前快照已在 `0.9.3 (preview)` 语境下更新
2. `design_docs/Global Phase Map and Current Position.md` 仍保留较多 `v1.0.0` / `v0.9.1` 阶段性结论文本
3. `.codex/handoffs/CURRENT.md` 当前 mirror 仍指向 `v0.9.2 release` 阶段收口
4. `.codex/checkpoints/latest.md` 仍声明 `Release: v1.0.0 — First stable release`

这会直接影响：

- 上下文恢复时的事实来源一致性
- safe-stop 入口的可信度
- `get_next_action()` / handoff intake / 人工审阅时对“当前仓库到底处在哪个 release 叙事中”的判断

## 目标

**做**：
1. 明确一个当前唯一有效的状态叙事：当前 phase、release 口径、safe-stop 状态、是否存在 active planning-gate
2. 将 Checklist、Phase Map、CURRENT、checkpoint 四个状态面同步到同一叙事
3. 保留历史阶段记录，但不让“当前结论”与 workspace 现实冲突
4. 用现有治理入口验证状态面对齐结果

**不做**：
1. 不修改 runtime / MCP / CLI 业务逻辑
2. 不重做 release 构建或 adoption 修复
3. 不重写所有历史 phase 文本，只修补“当前状态”相关表述
4. 不顺手扩展到 BL-1 / BL-2 / BL-3 的实现工作

## 交付物

### 1. 当前状态叙事对齐

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`

上述 4 个文件需要在以下字段上互相一致：

- 当前 phase / 当前 release 口径
- active planning-gate 是否为空
- 当前 safe-stop 判断
- 下一步应从哪里继续恢复

### 2. 验证记录

至少留下以下验证事实：

1. `get_next_action` 返回的 phase / planning-gate 判断与文档一致
2. 4 个状态面不再出现互相冲突的 release 叙事

## 验证门

- [x] Checklist / Phase Map / CURRENT / checkpoint 的当前状态字段一致
- [x] `mcp_doc-based-cod_get_next_action` 返回无 active planning-gate，且 phase 判断与文档一致
- [x] 若 handoff mirror 发生更新，mirror 与其 source handoff 关系仍清晰可追溯
- [x] 本切片不引入业务代码改动；若实际触及代码，再补 targeted/full regression

## 不触及

- 历史 phase 归档的全面重写
- release 产物内容变更
- 任何新的平台功能实现

## 收口判断

做到以下边界就应停：

1. 4 个关键状态面已经讲述同一个“当前事实”
2. `get_next_action` 不再与状态文档冲突
3. 能为下一轮继续 dogfood 或新 planning-gate 提供稳定恢复入口

下一条候选主线默认回到两选一：

1. 若状态面已稳定，则回到 `design_docs/direction-candidates-after-phase-35.md` 的 G（持续真实 dogfood）
2. 若用户希望先文档化后续结构边界，则转向 BL-1 / BL-2 / BL-3 的 backlog 文档切片