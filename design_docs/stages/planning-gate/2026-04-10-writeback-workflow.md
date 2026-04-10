# Planning Gate — 文档写回 + 工作流闭环

- Status: **CLOSED**
- Phase: 12
- Date: 2026-04-10

## 问题陈述

`governance-flow.md` 定义的最小治理流第 7 步为"写回 artifact"，`core-model.md` 明确 PEP 职责包括"文档起草与改写"、"模板应用"、"write-back"。但当前 PEP executor 虽能产出完整决策（intent → gate → delegation → escalation → review state），结果始终停在内存中，无法落地到实际文档/artifact 改写。

**当前缺口：**
- PEP `execute()` 返回 dict 但不改写任何文件（handoff 除外）
- review state machine 到达 `applied` 后无后续写回动作
- 无模板引擎或 artifact 写回能力
- 无 write-back 历史记录

## 切片计划

### Slice A — Write-back Engine 核心

**范围：**
- 创建 `src/pep/writeback_engine.py`
  - `WritebackPlan` 数据类：target_path, content_type (markdown/json/yaml), operation (create/update/append), template (可选), variables (可选)
  - `WritebackEngine` 类
    - `plan(envelope, execution_result) -> list[WritebackPlan]`：从执行结果推导写回计划
    - `execute_plan(plan, *, dry_run=True) -> WritebackResult`：执行单个写回计划
    - `execute_all(plans, *, dry_run=True) -> list[WritebackResult]`
  - `WritebackResult` 数据类：path, operation, success, diff_summary, error
  - dry-run 模式：生成 plan 但不写磁盘
  - 非 dry-run 模式：原子写入（先写临时文件再 rename）
  - 每次写回记录审计条目
- 测试：dry-run plan 生成、非 dry-run 文件写入、原子写入回滚、不同 content_type

**不做：**
- 不实现 Jinja2 或复杂模板引擎（用简单 string format）
- 不涉及 PEP executor 集成

### Slice B — PEP 集成与端到端

**范围：**
- 更新 `src/pep/executor.py`
  - 新增可选参数 `writeback_engine: WritebackEngine | None`
  - 当 review state 到达 `applied` 且 `writeback_engine` 已配置时，自动执行写回
  - dry-run 模式下生成 plan 但不落地
  - 非 dry-run 模式下执行写回并记录结果
  - 执行结果中包含 `writeback_plans` 和 `writeback_results` 字段
- 端到端测试：
  - inform gate → applied → write-back executed
  - review gate → waiting_review → 无 write-back（未到 applied）
  - delegation completed → applied → write-back executed
  - dry-run 不写文件
  - 非 dry-run 写入并验证文件内容
- write-back

**不做：**
- 不实现 artifact 版本管理（留给后续 Phase）
- 不实现远程 artifact 写回
- 不处理并发写入冲突

## 验证门

- [x] `pytest tests/` 全部通过（155 passed, 1 skipped）
- [x] WritebackEngine dry-run plan 生成正确
- [x] 非 dry-run 文件写入可验证
- [x] PEP 端到端：applied 状态触发写回
- [x] PEP 端到端：非 applied 状态不触发写回

## 依赖

- `src/pep/executor.py`（Phase 11 产出）
- `src/review/state_machine.py`（Phase 11 产出）
- `docs/governance-flow.md`、`docs/core-model.md`（权威来源）

## 风险

- Slice B 集成可能需要调整现有测试的 assert（因为执行结果会包含新的 writeback 字段）
- 原子写入在 Windows 上的 rename 行为需要验证
