# 子 Agent Tracing 与文档 Write-Back 对接方向分析

## 来源

- `review/research-compass.md` — 当前研究空白 #2："子 agent tracing 如何与文档 write-back 对接"
- `docs/subagent-management.md` — 子 agent 管理权威文档
- `docs/core-model.md` — 平台 actor 模型
- `design_docs/subagent-management-design.md` — 内部设计推导

## 现状

Phase 17 已交付完整的 Audit & Tracing 系统：`AuditEvent`（event-level 记录）、`TraceContext`（层级 trace 关联，root → child → grandchild）、多后端 `AuditLogger`。Phase 8 已交付 PEP + Subagent 接口（`WorkerBackend`、`ContractFactory`、`ReportValidator`），Phase 20 已交付三种协作模式（Worker / Handoff / Subgraph）。Decision Logs（Phase 17+）提供 19 字段的后处理聚合。

但 **tracing 链在 delegation → execution → write-back 通路上存在 5 个断裂点**（Gap A–E），导致无法从一个 trace_id 追踪到完整的子 agent 生命周期。

## 已识别的 Gap

### Gap A — Trace ID 在 Write-Back 阶段断裂

`src/pep/executor.py` → `_execute_writeback()` 捕获了 `trace_id = envelope.get("trace_id")`，但调用 `writeback_engine.execute_all(plans, dry_run)` 时 **不传递 trace_id**。WritebackEngine 无法为 write-back 操作生成 audit events。

**影响**：无法追踪某个 decision → 最终改了哪些文件。

### Gap B — Report → Write-Back Plans 映射缺失

子 agent 的 report 中包含 `changed_artifacts`，但 `WritebackEngine.plan()` 只从 envelope / execution result 推导，不检视 report。

**影响**：子 agent 报告的文件变更无法自动参与 write-back 规划。

### Gap C — ExecutionResult 不保存关键上下文

ExecutionResult 包含 `envelope_id`、`contract`、`report`、`review_state`，但不保存 `trace_id`、`delegation_mode`、`collaboration_context`。

**影响**：后续 reviewer / admin 无法从 result 追溯到原始决策链路。

### Gap D — Audit Events 不完整

缺少以下 event_type：`writeback_planned`、`writeback_blocked_by_check`、`contract_generated`、`subagent_report_received`、`artifact_changed`。

**影响**：审计链存在观测盲区，无法区分"写回被 check 拦截" vs "写回未触发"。

### Gap E — Handoff 与文档 Write-Back 的关系不明确

Handoff 生成为 JSON 持久化到 `.codex/handoffs/`，但不在权威文档中留下审计痕迹。

**影响**：对于长期追踪来说，handoff 的发生无法通过权威文档回溯。

## 候选方案

### 方案 A — Trace 链连通 + 关键 Event 补齐（推荐）

**范围**：修复 Gap A + C + D（trace 断裂 + result 缺失 + event 不完整）。

**改动**：

1. **ExecutionResult 扩展**（`src/pep/executor.py`）：
   - 新增 `trace_id: str`、`delegation_mode: str` 字段
   - 从 envelope 和 contract 中提取并保存

2. **WritebackEngine 签名扩展**（`src/pep/writeback_engine.py`）：
   - `execute_all(plans, dry_run, *, audit_logger=None, trace_id=None)`
   - 每个成功 write-back 操作发射 `artifact_changed` event
   - 开始时发射 `writeback_planned` event

3. **Executor 调用链修复**（`src/pep/executor.py`）：
   - `_execute_writeback()` 传递 `audit_logger` 和 `trace_id` 给 WritebackEngine
   - 新增 `contract_generated` 和 `subagent_report_received` event

4. **Audit event 补齐**：新增 5 个 event_type

**不做**：Gap B（report→plans 映射）和 Gap E（handoff 文档痕迹）留作后续切片。

**优势**：修复最核心的 trace 断裂，使端到端链路可追踪；改动集中在 3 个文件，风险可控。

**劣势**：report → write-back plans 仍然是手工映射。

### 方案 B — 全链路打通（A + B）

在方案 A 基础上，额外修复 Gap B：

5. **Report → Plans 映射**（`src/pep/executor.py`）：
   - `_execute_writeback()` 检查 `report.changed_artifacts`
   - 为每个 artifact 生成 `WritebackPlan`（update 类型，保守策略）
   - WritebackEngine 合并 envelope-derived plans + report-derived plans

**优势**：子 agent 产出的文件变更可自动流入 write-back 管道。

**劣势**：report.changed_artifacts 格式不统一（可能是相对路径、绝对路径、或 glob），需要归一化处理；且子 agent report 的可信度需要 review gate 控制。

### 方案 C — 全链路 + Handoff 审计（A + B + E）

在方案 B 基础上，额外修复 Gap E：

6. **Handoff 文档痕迹**（`src/pep/executor.py` 或 `src/workflow/safe_stop_writeback.py`）：
   - handoff 生成时发射 `handoff_generated` audit event
   - 在 checkpoint 中记录 handoff 发生的 trace_id
   - 可选：在 Phase Map 中追加 handoff 发生记录

**优势**：完整封闭所有 5 个 gap。

**劣势**：改动面最广，涉及 safe-stop bundle / checkpoint / Phase Map 等状态面，风险最高。

## 推荐

**推荐方案 A**。理由：

1. Gap A（trace 断裂）是最核心的阻塞——没有它，decision logs 的 trace_id 在 write-back 后就失去了追踪能力
2. Gap C（result 缺失）改动最小、风险最低，是顺手修复
3. Gap D（event 不完整）是 trace 连通的必要补充——不发射 event 就无法在 audit log 中观察到 write-back
4. Gap B 和 E 的触发信号不足，可在 dogfood 中观察是否有实际需求再决定

预计交付：

- 修改 3-4 个源文件
- 新增 5 个 audit event_type
- 6-8 个 targeted tests
- 全量回归通过
