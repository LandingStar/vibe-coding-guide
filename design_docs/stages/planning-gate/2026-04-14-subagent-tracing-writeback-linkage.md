# Planning Gate — 子 Agent Tracing 与 Write-Back 链路连通

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-14-subagent-tracing-writeback-linkage |
| Scope | Trace 链连通 + 关键 Event 补齐（方案 A） |
| Status | **COMPLETED** |
| 来源 | `design_docs/subagent-tracing-writeback-direction-analysis.md` 方案 A |
| 前置 | Phase 17（审计系统）、Decision Logs 已完成 |
| 测试基线 | 785 passed, 2 skipped |

## 目标

修复 trace 链在 delegation → execution → write-back 通路上的 3 个断裂点（Gap A/C/D），使 `trace_id` 能从 intent → delegation → execution → write-back → artifact 全程追踪。

**不做**：

- Gap B（report → write-back plans 自动映射）留作后续切片
- Gap E（handoff 文档审计痕迹）留作后续切片
- 不改变 PDP 层逻辑
- 不改变现有 AuditEvent / TraceContext 结构

## 交付物

### 1. ExecutionResult trace 字段扩展

修改 `src/pep/executor.py`：

- `_result()` 方法新增 `trace_id` 和 `delegation_mode` 字段
- `execute()` 中将 `trace_id` 传递给 `_result()`
- delegation 模式执行器中将 `mode` 传递给 result

### 2. WritebackEngine 签名扩展

修改 `src/pep/writeback_engine.py`：

- `execute_all()` 新增可选参数 `audit_logger` 和 `trace_id`
- `execute_plan()` 新增可选参数 `audit_logger` 和 `trace_id`
- 每个成功的 write-back 操作发射 `artifact_changed` audit event
- 开始执行前发射 `writeback_planned` audit event

### 3. Executor 调用链修复

修改 `src/pep/executor.py`：

- `_execute_writeback()` 传递 `audit_logger` 和 `trace_id` 给 `WritebackEngine.execute_all()`
- delegation 路径新增 `contract_generated` audit event
- worker/handoff/subgraph 路径新增 `subagent_report_received` audit event
- check 阻止写回时新增 `writeback_blocked_by_check` audit event

### 4. 新增 Audit Event Types

| event_type | phase | 触发点 |
|-----------|-------|--------|
| `contract_generated` | pep | 合同创建后 |
| `subagent_report_received` | pep | worker 返回 report 后 |
| `writeback_planned` | writeback | execute_all 开始前 |
| `writeback_blocked_by_check` | writeback | pack check 阻止写回时 |
| `artifact_changed` | writeback | 单个文件写入完成后 |

### 5. Targeted Tests

- `test_execution_result_contains_trace_id`: 验证 execute() 返回包含 trace_id
- `test_execution_result_contains_delegation_mode`: 验证 delegation 结果包含 mode
- `test_writeback_emits_artifact_changed_events`: 验证 write-back 发射 artifact_changed
- `test_writeback_emits_planned_event`: 验证 write-back 发射 writeback_planned
- `test_delegation_emits_contract_and_report_events`: 验证 delegation 发射 contract_generated + subagent_report_received
- `test_writeback_blocked_emits_check_event`: 验证 check 阻止时发射 writeback_blocked_by_check
- `test_trace_chain_end_to_end`: 验证完整 trace 链路可追踪

## 验证门

- [x] ExecutionResult 包含 trace_id 和 delegation_mode
- [x] WritebackEngine 发射 writeback_planned 和 artifact_changed events
- [x] Executor delegation 路径发射 contract_generated 和 subagent_report_received
- [x] Pack check 阻止写回时发射 writeback_blocked_by_check
- [x] 全量回归测试通过
- [x] research-compass "子 agent tracing" 空白标记为已完成
