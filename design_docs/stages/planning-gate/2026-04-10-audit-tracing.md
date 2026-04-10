# Planning Gate — Audit & Tracing System

- Status: **CLOSED**
- Phase: 17
- Date: 2026-04-10

## 问题陈述

`docs/core-model.md` §Tracing And Audit 要求平台"默认支持最小 tracing/audit 能力"，记录：输入、PDP 决策、gate 触发、委派、handoff/escalation、PEP 执行、写回 artifact。

当前仅有 `ActionLog`（PEP 方法级记录）和 Review 状态机的 audit trail，缺乏：
- 跨决策链的全链路 trace（从输入到写回）
- Correlation ID 串联各阶段
- 持久化审计日志（当前全部 in-memory）
- AuditLogger 中心化记录器

## 设计策略

1. **AuditLogger**：中心化审计记录器，支持 emit(event) 接口，可插拔后端（in-memory / JSON file）
2. **TraceContext**：每次 envelope 处理分配 trace_id，贯穿 PDP→PEP→writeback
3. **审计事件类型**：input_received、intent_classified、gate_resolved、delegation_decided、escalation_decided、precedence_resolved、execution_started、review_feedback、writeback_completed
4. **最小侵入**：各 resolver/executor 调用 logger.emit()，不改变返回值结构
5. **向后兼容**：AuditLogger 可选注入，未注入时不影响现有行为

## 切片计划

### Slice A — AuditLogger + TraceContext + Backends

**范围：**
- 创建 `src/audit/__init__.py`
- 创建 `src/audit/trace_context.py`：
  - `TraceContext` dataclass：trace_id、parent_trace_id（可选）、created_at
  - `new_trace() -> TraceContext`：生成新 trace
  - `child_trace(parent: TraceContext) -> TraceContext`：创建子 trace
- 创建 `src/audit/audit_logger.py`：
  - `AuditEvent` dataclass：event_id、trace_id、timestamp、event_type、phase（pdp/pep/writeback）、detail dict
  - `AuditBackend` Protocol：emit(event)、query(trace_id) -> list[AuditEvent]
  - `MemoryAuditBackend`：in-memory list
  - `FileAuditBackend`：JSON lines 文件（每行一条 event）
  - `AuditLogger`：聚合多个 backend，统一 emit + query 接口
- 测试：emit/query、多 backend、trace 关联

### Slice B — PDP + PEP 审计集成

**范围：**
- `decision_envelope.build_envelope()` 新增可选 `audit_logger` + `trace_ctx` 参数
  - 在 intent_classifier、gate_resolver、delegation_resolver、escalation_resolver、precedence_resolver 调用后各 emit 一条 event
  - envelope 中附加 `trace_id` 字段
- `executor.execute()` 新增可选 `audit_logger` 参数
  - execution_started、review_feedback（via apply_review_feedback）、writeback_completed 各 emit
- 无 logger 时行为与当前完全一致（向后兼容）
- 测试：全链路 trace 覆盖（input → PDP → PEP → writeback → audit query 验证 ≥7 条 event）

**不做：**
- 不实现远端审计推送（webhook/database）
- 不改变 ActionLog 的现有行为（保留现有 log 机制，审计层独立叠加）
- 不实现审计日志搜索/过滤/导出 API（仅 query by trace_id）

## 验证门

1. `pytest tests/` 全部通过（无回归）
2. AuditLogger 可 emit + query，MemoryBackend 和 FileBackend 均工作
3. TraceContext 可创建/关联 trace
4. build_envelope + execute 可选注入 logger 后产生完整审计链
5. query(trace_id) 返回 ≥7 条治理事件
6. 无 logger 时行为与当前完全一致
