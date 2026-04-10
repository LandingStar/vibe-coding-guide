# Planning Gate — Checkpoint 持久化 + 方向文档化模板

- Status: **CLOSED**
- Phase: 21
- Date: 2026-04-10

## 问题陈述

Phase 20 完成后暴露了两个上下文压缩问题：
1. AI 在上下文压缩后丢失行为约束（已通过 B 层 always-on 约束修复）
2. 工作状态（当前 phase/slice/todo/候选方向）在压缩后不可恢复（需要 C 层 checkpoint）

本 Phase 实施 `design_docs/context-persistence-design.md` 中的 C.1 (Checkpoint 工具函数) 和 C.3 (候选方向文档化模板)。

## 设计策略

### Slice A: Checkpoint 工具函数

实现 `src/workflow/checkpoint.py`：
- `write_checkpoint(...)` — 将当前工作状态写入 `.codex/checkpoints/latest.md`
- `read_checkpoint(path)` — 解析 checkpoint 文件返回结构化 dict
- `validate_checkpoint(path)` — 检查 checkpoint 是否存在且包含必填字段

Checkpoint 格式定义：
```markdown
# Checkpoint — <ISO timestamp>
## Current Phase
Phase N: <name>, Slice <X>, status: <in-progress|completed|waiting-user>
## Active Planning Gate
<path>
## Current Todo
- [x] done
- [-] in-progress
- [ ] not-started
## Pending User Decision
<optional>
## Direction Candidates
- A: <one-line> — source: <doc ref>
## Key Context Files
- <file1>
- <file2>
```

### Slice B: 方向文档化模板 + Workflow Standard 更新

1. 创建 `design_docs/stages/_templates/direction-candidates.md` 模板
2. 在 Document-Driven Workflow Standard 中增加 checkpoint 触发时机约定

### Slice C: 生成首个 checkpoint

用 Slice A 的工具函数生成 Phase 21 完成时的首个 checkpoint。

## 明确不做

- 不做 Runtime 自动触发（C 层）——当前阶段过度工程
- 不修改 executor.py 或 PEP 层
- 不做 checkpoint 历史版本管理

## 验证门

- `write_checkpoint` + `read_checkpoint` + `validate_checkpoint` 有 pytest 覆盖
- 首个 checkpoint 文件被成功生成并可被 `read_checkpoint` 解析
- 全量回归 414+ 测试通过
- Document-Driven Workflow Standard 已更新

## 同步更新

- `design_docs/context-persistence-design.md` — 步骤 4/5/6 标记完成
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
