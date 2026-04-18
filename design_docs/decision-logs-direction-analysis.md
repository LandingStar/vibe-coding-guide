# Direction Analysis — Decision Logs Minimum Field Design

## 背景

research-compass.md 仍将"decision logs 的最小字段设计"列为研究空白。当前审计系统（Phase 17）已提供事件级审计（`AuditEvent`）、全链路关联（`TraceContext`）和执行记录（`ActionLog`），但缺少**决策级**的结构化日志——即把"谁用什么规则对什么输入做了什么决定，结果是什么"聚合成一条可查询、可持久化的记录。

## 现有能力盘点

| 组件 | 位置 | 记录什么 | 缺什么 |
|------|------|---------|--------|
| `AuditEvent` | `src/audit/audit_logger.py` | 单个事件（intent_classified, gate_resolved 等） | 不聚合为决策级摘要 |
| `TraceContext` | `src/audit/trace_context.py` | 全链路 trace_id 关联 | 仅关联，不产出聚合记录 |
| `Decision Envelope` | `src/pdp/decision_envelope.py` | PDP 决策快照（intent + gate + precedence + delegation + escalation） | 在飞数据结构，不持久化 |
| `ActionLog` | `src/pep/action_log.py` | PEP 执行动作 | 只记动作，不含 PDP 决策上下文 |
| `PipelineResult` | `src/workflow/pipeline.py` | envelope + execution + audit_events + pack_info | 返回给调用方后即丢弃，无持久化 |

**核心缺口**：没有一条记录同时包含 INPUT（什么输入）、DECISION（允许/阻止）、RATIONALE（哪条规则胜出、依据什么策略）、OUTCOME（PEP 做了什么）、CONTEXT（哪个 pack、哪个版本、哪个 trace）并持久存储。

## OPA 借鉴点

依据 [review/open-policy-agent.md](../review/open-policy-agent.md)：

- Decision log 应包含：queried_policy, input, result, bundle_metadata, traceability fields
- 支持敏感数据掩码
- 支持后端可插拔（本地文件 / 远程推送）

## 候选方案

### 方案 A：后处理聚合（推荐）

**思路**：在 `Pipeline.process()` 完成后，将已有的 envelope + execution + audit_events 聚合为一条 `DecisionLogEntry`，写入独立的持久化后端。

**DecisionLogEntry 最小字段**：

```python
@dataclass
class DecisionLogEntry:
    # ── Identity ──
    log_id: str                    # "dl-{uuid[:12]}"
    decision_id: str               # = envelope.decision_id
    trace_id: str                  # 全链路关联
    timestamp: str                 # ISO-8601
    
    # ── Input ──
    input_summary: str             # 前 200 字符（与 envelope 一致）
    scope_path: str                # 显式 scope（hierarchical pack 模式，可为空）
    
    # ── Decision ──
    decision: str                  # "ALLOW" | "BLOCK"
    intent: str                    # 分类结果
    gate: str                      # gate 级别
    constraint_violated: list[str] # 若 BLOCK
    
    # ── Rationale ──
    winning_rule: str | None       # precedence 结果
    adoption_layer: str | None     # 胜出层级
    resolution_strategy: str | None # "adoption-layer-priority" | "explicit-override ..."
    explicit_override: bool        # 是否显式覆盖
    
    # ── Context ──
    pack_names: list[str]          # 参与决策的 pack 名称列表
    pack_versions: list[str]       # 对应版本列表
    
    # ── Outcome ──
    pep_action_count: int          # PEP 执行了多少动作
    final_state: str | None        # review state machine 最终状态
    
    # ── Audit Chain ──
    audit_event_count: int         # 关联的审计事件数
```

**持久化**：新增 `DecisionLogStore`，JSON Lines 格式，文件位置 `.codex/decision-logs/<date>.jsonl`。

**对外暴露**：
- `Pipeline.process()` 返回的 `PipelineResult` 新增 `decision_log_entry: dict`
- MCP `governance_decide()` 返回值新增 `decision_log_entry: dict`
- 新增 MCP 工具 `query_decision_logs(trace_id=None, decision=None, intent=None, limit=50) → list[dict]`

**改动范围**：
- 新增：`src/audit/decision_log.py`（`DecisionLogEntry` + `DecisionLogStore`）
- 修改：`src/workflow/pipeline.py`（process() 末尾聚合并写入）
- 修改：`src/mcp/tools.py`（governance_decide 返回新增字段 + 新工具 query_decision_logs）
- 新增：targeted tests

**优势**：
- 最小侵入——完全基于已有数据结构的后处理
- 不改变 PDP/PEP 内部逻辑
- 聚合逻辑简单（从 envelope + execution + audit_events 提取字段）
- 立即提升 dogfood 可观测性

**劣势**：
- 聚合发生在 Pipeline 而非审计后端，耦合点单一（但也意味着维护简单）
- 查询能力有限（本地文件 grep 级别）

### 方案 B：DecisionLog 作为 AuditBackend 的一等输出

**思路**：在 AuditLogger 的多后端分发架构中新增一个 `DecisionLogBackend`，该后端在收到 `execution_started` 事件时自动回溯同 trace_id 的所有前序事件，聚合为 `DecisionLogEntry` 并写入。

**改动范围**：
- 新增：`src/audit/decision_log_backend.py`
- 修改：`src/audit/audit_logger.py`（注册新后端）
- 修改：`src/workflow/pipeline.py`（Pipeline.__init__ 注册后端）
- MCP 暴露同方案 A

**优势**：
- 利用已有的多后端架构，职责分离更干净
- 聚合逻辑与 Pipeline 解耦

**劣势**：
- `DecisionLogBackend` 需要缓存事件再回溯，实现复杂度更高
- 回溯依赖事件到达顺序，边界情况需要额外处理
- 过度设计——当前只有一个 Pipeline，多后端的解耦收益不明显

### 方案 C：完整 Decision Log 系统（远期）

在方案 A 或 B 基础上新增：
- 敏感数据掩码（input_summary 中的 API key / 个人信息脱敏）
- 日志轮转与保留策略
- 远程推送后端（webhook / 文件网关）
- 统计聚合查询（按 intent/gate/pack 分组统计）

**判断**：当前无真实需求，标记为储备。若实际部署到共享环境或需要合规审计时再考虑。

## 方案对比

| 维度 | A（后处理聚合） | B（审计后端输出） | C（完整系统） |
|------|---------------|-----------------|-------------|
| 改动量 | 小（新增 1 文件 + 修改 2 文件） | 中（新增 1 文件 + 修改 3 文件） | 大 |
| 侵入性 | 最低 | 中 | 高 |
| 架构一致性 | 中（在 Pipeline 层聚合） | 高（利用审计多后端） | 最高 |
| 可观测性提升 | 高 | 高 | 最高 |
| 当前必要性 | 是 | 过度设计 | 过度设计 |

## AI 倾向判断

**推荐方案 A（后处理聚合）**。理由：

1. 它是唯一满足"最小改动、最大可观测性收益"的方案
2. 聚合逻辑简单透明——从 envelope / execution / audit_events 提取 10+ 个字段写入文件
3. `DecisionLogEntry` 的字段设计参考了 OPA decision log 但保持平台特色（intent/gate/precedence 而非 OPA 的 policy/binding）
4. 新增的 `query_decision_logs` MCP 工具直接提升 dogfood 可观测性（可以在 MCP 客户端查看"上一个决策是什么"）
5. 方案 B 的多后端解耦在当前只有一个 Pipeline 的架构下无实际收益
6. 方案 C 的掩码/轮转/远程推送在本地 dogfood 阶段不需要

方案 C 的各项能力可以在方案 A 的基础上渐进增强，不需要一步到位。
