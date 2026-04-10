# Planning Gate — Handoff 落地实现

- Status: **CLOSED**
- Phase: 9
- Date: 2026-04-10

## 问题陈述

当委派完成后若 `allow_handoff=true`，PEP 需要生成一个符合 `handoff.schema.json` 的 Handoff 对象并持久化到文件系统。当前只有 schema 定义，没有生成和持久化逻辑。

## 切片计划

### Slice A — Handoff Builder 纯函数

**范围：**
- 创建 `src/subagent/handoff_builder.py`
  - `build(envelope, delegation, contract, report) -> dict`
  - 从执行上下文中提取 10 个 required 字段
  - 输出符合 `handoff.schema.json`
- 测试：生成结果通过 schema 校验

**不做：**
- 不涉及文件系统
- 不涉及 PEP

### Slice B — PEP 集成 + 持久化

**范围：**
- 更新 `src/pep/executor.py`：当 `delegation.allow_handoff=true` 且委派完成时，调用 handoff_builder 并持久化
- 持久化路径：`.codex/handoffs/` 目录下按 `handoff_id` 命名
- dry-run 模式下只记录 log 不实际写文件
- 测试：端到端 + 持久化行为
- write-back

**不做：**
- 不实现 Handoff 的「接收方确认」流程
- 不实现 Handoff 链

## 验证门

- [x] `pytest tests/` 全部通过 — 85 passed
- [x] Handoff Builder 输出通过 `handoff.schema.json` 校验
- [x] PEP 端到端测试包含 handoff 生成
- [x] dry-run 不写文件
- [x] `validate_doc_loop.py --target .` 通过

## 依赖

- `docs/specs/handoff.schema.json`
- `src/pep/executor.py`（Phase 8 产出）
- `src/subagent/contract_factory.py`、`report_validator.py`

## 风险

- Handoff 持久化涉及文件 I/O，需要确保 dry-run 模式不产生副作用。
