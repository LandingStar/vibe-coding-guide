# Planning Gate — Worker Registry 驱动 Executor 动态选择

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-worker-registry-executor-integration |
| Scope | 将 Executor 从单一 Worker 注入改为 WorkerRegistry 驱动的动态选择 |
| Status | **DONE** |
| 来源 | `design_docs/subagent-research-synthesis.md` P1, BL-2 adapter-registry |
| 前置 | WorkerRegistry 已存在 (`src/workers/registry.py`), 3 种 Worker 后端已实现 |
| 测试基线 | 892 passed, 2 skipped |

## 问题陈述

当前 `Executor.__init__` 接受单一 `worker: WorkerBackend | None`，无法在运行时根据 delegation decision 的 `worker_type` 动态选择不同后端。`WorkerRegistry`（`src/workers/registry.py`）已实现 register/get/list_types，但 Executor 不使用它。

## 研究依据

- Semantic Kernel：multi-source plugin 发现 → 统一注册模型
- LangGraph：namespace scoping → 注册表隔离
- 当前 WorkerRegistry 已有 `register(type, worker)` / `get(type)` / `list_types()` / `__contains__`

## 目标

**做**：

1. **Executor 接受 WorkerRegistry**
   - `__init__` 新增 `worker_registry: WorkerRegistry | None` 参数
   - 向后兼容：若同时提供 `worker`（旧方式），将其注册为 `"default"` 类型
   - 若两者都未提供，行为不变（降级到 queue-for-review）

2. **动态 Worker 选择**
   - `_execute_worker_mode` 从 contract 或 delegation decision 中提取 `worker_type`
   - 通过 `registry.get(worker_type)` 获取对应 Worker
   - 若 `worker_type` 未注册，降级到 `"default"` 类型
   - 若 `"default"` 也不存在，走原有降级路径

3. **Executor factory 便捷方法**
   - `Executor.with_registry(registry, ...)` 或在现有 `__init__` 中直接支持
   - 提供默认 registry 构建：根据可用配置自动注册 LLM/HTTP/Stub

4. **Handoff / Subgraph 模式也使用 registry**
   - `_execute_handoff_mode` 和 `_execute_subgraph_mode` 通过 registry 获取 worker
   - 保持现有行为不变（只是 worker 来源改为 registry）

5. **Audit 事件补充**
   - worker 选择时发射 `worker_selected` event（记录 worker_type、来源）
   - worker_type 未找到降级时发射 `worker_fallback` event

**不做**：

1. 不做多层级 namespace（project → pack → instance）— 记录为 FR-NS-Hierarchy
2. 不做 MCP Worker 后端 — 记录为 FR-MCP-Worker
3. 不改 WorkerBackend Protocol — 保持 `execute(dict) -> dict`
4. 不做 capability-based 查询（按能力匹配 worker）— 留给后续
5. 不改 WorkerConfig 结构

## 模块改动

```
src/pep/executor.py          — __init__ 接受 registry, _execute_worker_mode 动态选择
src/workers/registry.py      — 确认现有接口充分（可能加 has_default() 等辅助）
tests/test_executor.py       — 新增 registry 注入 + 动态选择测试
tests/test_worker_registry.py — 新增/扩展 registry 测试
```

## 验证门

- [x] Executor 接受 WorkerRegistry 并能动态选择 worker_type
- [x] 向后兼容：旧 `worker=` 参数仍可用
- [x] worker_type 未注册时正确降级
- [x] handoff/subgraph 模式通过 registry 获取 worker
- [x] audit 事件 `worker_selected` / `worker_fallback` 正确发射
- [x] 新增测试 ≥ 8 个（实际 11 个）
- [x] 全量回归通过（892 passed, 2 skipped）
