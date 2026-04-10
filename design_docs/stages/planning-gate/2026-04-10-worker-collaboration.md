# Planning Gate — Worker 协作模式扩展 (Handoff + Subgraph)

- Status: **CLOSED**
- Phase: 20
- Date: 2026-04-10
- Closed: 2026-04-10 — 414 tests passed (2 skipped)

## 问题陈述

当前 delegation_resolver 硬编码 `mode: "supervisor-worker"`，PEP executor 对所有委派都走同一条 `_execute_delegation` 路径。`docs/subagent-management.md` 和 `design_docs/subagent-management-design.md` 定义了 4 种非默认协作模式（handoff、team、swarm、subgraph），但均未实现。

Phase 20 实现 **handoff** 和 **subgraph** 两种模式的协议层 + PDP 路由 + PEP 执行骨架。

## 设计策略

### Handoff 模式
- **语义**：会话控制权从主 agent 显式移交给专业化 agent。接收方成为新的 supervisor，原方退出执行。
- **与 worker 模式区别**：worker 是"发出去再收回来"，handoff 是"发出去对方接管"。
- **关键对象**：
  - `HandoffRequest`：请求移交，包含 from_role、to_role、reason、scope、constraints
  - `HandoffExecution`：执行移交，生成 Handoff 对象 + 审计 + review
  - 复用已有 `handoff_builder.py` 和 `handoff.schema.json`
- **PDP 路由**：delegation_resolver 根据条件选择 mode=handoff（如高复杂度 + 专业化需求）
- **PEP 执行**：生成 Handoff 对象 + 持久化 + 触发 review（handoff 默认需 review）

### Subgraph 模式
- **语义**：创建隔离的子流程空间，子 agent 在独立 namespace 中执行，可暂停/恢复/重入。
- **关键对象**：
  - `SubgraphContext`：namespace + state_id + parent_trace + isolation_level
  - `SubgraphExecution`：创建隔离上下文 → 执行 → 收集结果 → 合并回主流程
- **PDP 路由**：delegation_resolver 根据条件选择 mode=subgraph（如长流程 + 状态隔离需求）
- **PEP 执行**：创建 SubgraphContext → 委派到 worker（在隔离上下文中）→ 结果合并

## 切片计划

### Slice A — Handoff 协作模式

**范围：**
- 创建 `src/collaboration/` 包
  - `__init__.py`
  - `modes.py`：CollaborationMode 枚举 + ModeSelector 协议
  - `handoff_mode.py`：HandoffExecutor 类
    - `prepare(delegation, contract)` → 生成 HandoffRequest
    - `execute(request, worker)` → 执行移交 + 生成 Handoff 对象
    - handoff 默认 requires_review=True
    - 审计集成（emit handoff_initiated / handoff_completed 事件）
- 重构 `src/pdp/delegation_resolver.py`：
  - 新增 mode 选择逻辑（默认 worker，条件触发 handoff/subgraph）
  - 条件：`allow_handoff=True` 在 delegation_decision 中 → mode=handoff
- 重构 `src/pep/executor.py`：
  - `_execute_delegation` 根据 mode 分发到不同执行器
  - mode=handoff → HandoffExecutor
  - mode=worker → 现有逻辑（不变）
- 测试 handoff 模式的 PDP 路由 + PEP 执行 + 审计

### Slice B — Subgraph 协作模式

**范围：**
- 创建 `src/collaboration/subgraph_mode.py`：
  - `SubgraphContext` dataclass — namespace, state_id, parent_trace_id, isolation_level, state_snapshot
  - `SubgraphExecutor` 类：
    - `create_context(delegation, contract)` → SubgraphContext
    - `execute(context, worker, contract)` → 在隔离上下文中执行
    - `merge_result(context, report)` → 合并结果回主流程
    - 审计集成（emit subgraph_created / subgraph_completed 事件）
- 重构 delegation_resolver：mode=subgraph 条件
- 重构 executor：mode=subgraph → SubgraphExecutor
- 测试 subgraph 模式的创建/执行/合并/审计

**不做：**
- 不实现真正的进程级隔离（当前在内存中模拟 namespace 隔离）
- 不实现 team/swarm 模式
- 不实现 subgraph 的持久化暂停/恢复（留给后续）
- 不实现并发多 worker

## 验证门

1. `pytest tests/` 全部通过（无回归）
2. delegation_resolver 可根据条件选择 worker/handoff/subgraph 三种模式
3. executor 根据 mode 分发到不同执行器
4. HandoffExecutor 生成 Handoff 对象 + 审计
5. SubgraphExecutor 创建隔离上下文 + 执行 + 合并结果 + 审计
6. 现有 worker 模式不受影响（向后兼容）
