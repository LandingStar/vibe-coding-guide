# Planning Gate — Decision Logs 最小字段设计

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-14-decision-logs-minimum-field-design |
| Scope | Decision Logs 后处理聚合（方案 A） |
| Status | **COMPLETED** |
| 来源 | `design_docs/decision-logs-direction-analysis.md` 方案 A |
| 前置 | Phase 17（审计系统）已完成 |
| 测试基线 | 779 passed, 2 skipped |

## 目标

在 Pipeline.process() 完成后，将已有 envelope + execution + audit_events 聚合为结构化 `DecisionLogEntry`，持久化到 `.codex/decision-logs/`，并通过 MCP 工具暴露查询能力。

**不做**：

- 不改变 PDP/PEP 内部逻辑
- 不改变 AuditEvent / TraceContext / ActionLog 的现有结构
- 不实现敏感数据掩码或日志轮转（方案 C 储备）
- 不实现远程推送后端

## 交付物

### 1. DecisionLogEntry dataclass

新增 `src/audit/decision_log.py`：

```python
@dataclass
class DecisionLogEntry:
    log_id: str                    # "dl-{uuid[:12]}"
    decision_id: str               # = envelope.decision_id
    trace_id: str                  # 全链路关联
    timestamp: str                 # ISO-8601
    input_summary: str             # 前 200 字符
    scope_path: str                # hierarchical pack scope（可为空）
    decision: str                  # "ALLOW" | "BLOCK"
    intent: str                    # 分类结果
    gate: str                      # gate 级别
    constraint_violated: list[str] # 若 BLOCK
    winning_rule: str | None       # precedence 结果
    adoption_layer: str | None     # 胜出层级
    resolution_strategy: str | None
    explicit_override: bool
    pack_names: list[str]          # 参与决策的 pack
    pack_versions: list[str]
    pep_action_count: int
    final_state: str | None
    audit_event_count: int
```

### 2. DecisionLogStore

同文件新增：

- `DecisionLogStore(log_dir: Path)`
- `store.append(entry: DecisionLogEntry)` → 写入 `<date>.jsonl`
- `store.query(trace_id=None, decision=None, intent=None, limit=50) → list[dict]`
- 日志目录：`.codex/decision-logs/`

### 3. Pipeline 集成

修改 `src/workflow/pipeline.py`：

- `process()` / `process_scoped()` 末尾：从 envelope + execution + audit_events 聚合 `DecisionLogEntry`
- 写入 `DecisionLogStore`（非 dry_run 模式下）
- `PipelineResult` 新增 `decision_log_entry: dict`

### 4. MCP 工具暴露

修改 `src/mcp/tools.py`：

- `governance_decide()` 返回新增 `decision_log_entry: dict`
- 新增 `query_decision_logs(trace_id=None, decision=None, intent=None, limit=50) → dict`

### 5. Targeted Tests

- `test_decision_log_entry_from_envelope_allow`: 验证从 ALLOW 结果聚合出正确字段
- `test_decision_log_entry_from_envelope_block`: 验证从 BLOCK 结果聚合出正确字段
- `test_decision_log_store_append_and_query`: 验证持久化写入与查询
- `test_pipeline_result_includes_decision_log`: 验证 PipelineResult 包含 decision_log_entry
- `test_mcp_governance_decide_includes_decision_log`: 验证 MCP 返回包含 decision_log_entry
- `test_mcp_query_decision_logs`: 验证新 MCP 查询工具

## 验证门

- [x] `DecisionLogEntry` dataclass 可正确聚合 envelope + execution 数据
- [x] `DecisionLogStore` 可写入 JSON Lines 并按 trace_id / decision / intent 查询
- [x] `Pipeline.process()` 在非 dry_run 时写入 decision log
- [x] `PipelineResult.decision_log_entry` 字段存在
- [x] MCP `governance_decide()` 返回包含 decision_log_entry
- [x] MCP `query_decision_logs()` 工具可工作
- [x] 全量回归测试通过
- [x] `review/research-compass.md` 空白项标记为已完成
