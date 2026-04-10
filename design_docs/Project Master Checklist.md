# 项目总清单与状态板

## 文档定位

本文件是 `doc-based-coding-platform` 的总入口、状态板与协作恢复入口。

若当前对话、workspace 现实状态与其他文档冲突，优先级应为：

1. 用户在最新对话中的明确决定
2. 当前 workspace 的现实状态
3. 正式设计文档与协议文档
4. 当前 active handoff

## 当前快照

- Snapshot Date: `2026-04-10`
- Project Name: `doc-based-coding-platform`
- Current Phase: `Phase 21 Checkpoint Persistence + Direction Template`
- Active Slice: `Phase 21 Slice A+B+C` — completed
- Safe Stop Status: `Phase 21 All Slices Closed`

## 当前文档入口

- `docs/README.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-08-doc-loop-prototype-authority-rereview.md`
- `design_docs/doc-loop-prototype-authority-rereview.md`
- `design_docs/stages/README.md`
- `design_docs/tooling/README.md`
- `.codex/handoffs/CURRENT.md`

## 已确认决策

- 本项目默认采用“生成/更新 doc 规划 -> 按 doc 实施 -> 结果回写 doc”的工作流。
- 根目录 `docs/` 是当前仓库里关于平台与官方实例定位的最高权威来源。
- `design_docs/` 现在主要承载状态板、planning/phase 文档与内部设计推导。
- 当前已完成第一条仓库级执行切片：把 repo-local adoption 入口对齐到当前仓库现实。
- 当前已开启下一条 planning gate：`doc-loop-vibe-coding` prototype authority rereview。
- 重要设计节点默认必须先交用户审核，再进入下一大步。
- 当前已形成 prototype authority rereview 结论，正在等待用户审核。
- handoff 只负责安全停点交接，不替代正式设计文档。

## 当前待办与风险

- Phase 4 Slice A (PDP Decision Envelope Schema) 已完成。
- Phase 4 Slice B (Intent Classification Result Schema) 已完成。
- Phase 4 Slice C (Gate Decision Schema) 已完成。
- Phase 4 Slice D (Delegation Decision Schema) 已完成。
- Phase 4 Slice E (Escalation + Precedence Schema 收口) 已完成。
- `docs/escalation-decision.md` 与 `docs/specs/escalation-decision-result.schema.json` 已创建。
- `docs/precedence-resolution.md` 与 `docs/specs/precedence-resolution-result.schema.json` 已创建。
- Envelope 中所有 5 个子决策类型均已用 `$ref` 引用独立 schema。
- Phase 4 平台对象规格化已全部完成。
- 下一步候选：Phase 5 方向选择（runtime 实现、扩展协议、或其他）。
- Phase 5 Slice A+B (Subagent Contract/Report/Handoff Schema) 已完成。
- `docs/specs/subagent-contract.schema.json`、`subagent-report.schema.json`、`handoff.schema.json` 已创建。
- `docs/subagent-schemas.md` 已添加全部 3 个 schema 引用。
- Phase 5 Subagent Schema 规格化已全部完成。
- Phase 6 Slice A+B (PDP/PEP Runtime Skeleton) 已完成。
- `src/pdp/` 包：intent_classifier、gate_resolver、decision_envelope。
- `src/pep/` 包：executor (dry-run)、action_log。
- 25 项 pytest 测试全部通过。
- Phase 6 Runtime 骨架已全部完成。
- Phase 7 Slice A+B (PDP Full Decision Chain) 已完成。
- `src/pdp/delegation_resolver.py`、`escalation_resolver.py`、`precedence_resolver.py` 已创建。
- 47 项 pytest 测试全部通过。
- Phase 7 PDP 完整决策链已全部完成。
- Phase 8 已启动：PEP + Subagent 接口与实现（依赖反转）。
- `src/interfaces.py`：WorkerBackend / ContractFactory / ReportValidator Protocol 定义。
- `src/subagent/contract_factory.py`：delegation_decision → Subagent Contract 生成。
- `src/subagent/report_validator.py`：report → schema 校验。
- `src/subagent/stub_worker.py`：StubWorkerBackend 最小可测实现。
- `src/pep/executor.py` 进化：支持委派管线（contract → worker → report → validate）。
- 71 项 pytest 测试全部通过。
- Phase 8 PEP + Subagent 接口已全部完成。
- Phase 9 已启动：Handoff 落地实现。
- `src/subagent/handoff_builder.py`：envelope + delegation + contract + report → Handoff 对象。
- `src/pep/executor.py` 进化：当 `allow_handoff=true` 时自动生成并持久化 Handoff。
- dry-run 模式不写磁盘，非 dry-run 会写入 `.codex/handoffs/` 目录。
- 85 项 pytest 测试全部通过。
- Phase 9 Handoff 落地已全部完成。
- Phase 10 已启动：升级路径执行。
- `src/interfaces.py` 新增 EscalationNotifier Protocol。
- `src/pep/notification_builder.py`：从 envelope + escalation_decision 生成通知对象。
- `src/pep/stub_notifier.py`：StubNotifier 内存记录实现。
- `src/pep/executor.py` 进化：千escalation_decision.escalate=true 时自动执行升级路径。
- human_reviewer → 调用通知器 + 状态标记 escalated。
- main_agent → 状态标记 re-evaluate。
- 93 项 pytest 测试全部通过。
- Phase 10 升级路径执行已全部完成。
- 子 agent 机制 5 项需求全部完成。
- Phase 11 已启动：Review 状态机引擎。
- `src/review/state_machine.py`：6 状态 / 7 事件 / 8 条迁移规则 + inform 快速路径。
- ReviewStateMachine 类：transition / allowed_events / audit trail。
- `src/pep/executor.py` 进化：每次 execute 创建 ReviewStateMachine 实例并驱动迁移。
- inform → proposed→applied；review/approve → proposed→waiting_review；delegation completed → submit→approve→apply。
- 执行结果包含 review_state 与 review_history 字段。
- 129 项 pytest 测试全部通过（1 skipped）。
- Phase 11 Review 状态机引擎已全部完成。
- Phase 12 已启动：文档写回 + 工作流闭环。
- `src/pep/writeback_engine.py`：WritebackPlan/WritebackResult/WritebackEngine 实现。
- WritebackEngine：plan + execute_plan + execute_all，支持 create/update/append 三种操作。
- 原子写入：写临时文件 + os.replace。
- `src/pep/executor.py` 进化：当 review_state=applied 且 writeback_engine 已配置时自动触发写回。
- dry-run 生成 plan 但不写磁盘；非 dry-run 落地文件并记录结果。
- 执行结果包含 writeback_plans 与 writeback_results 字段。
- 155 项 pytest 测试全部通过（1 skipped）。
- Phase 12 文档写回 + 工作流闭环已全部完成。
- Phase 13 已启动：Review 完整流程 + 真实通知。
- `src/pep/notifiers/` 包：ConsoleNotifier / FileNotifier / WebhookNotifier 三种通知适配器。
- 每个 notifier 实现 EscalationNotifier Protocol。
- WebhookNotifier 仅用 stdlib（urllib.request），无外部依赖。
- `src/pep/review_orchestrator.py`：ReviewOrchestrator 驱动 approve/reject/request_revision 反馈。
- approve → APPROVE → APPLY（auto_apply 可选）；reject → REJECT（终态 + 可选通知）；request_revision → REQUEST_REVISION → REVISED（修订循环）。
- submit_revision：revised → proposed → waiting_review（重新提交周期）。
- `src/pep/executor.py` 进化：结果附带 _rsm 引用 + 新增 apply_review_feedback() 方法。
- apply_review_feedback 使用 ReviewOrchestrator 驱动后续状态，applied 后自动触发 writeback。
- 183 项 pytest 测试全部通过（1 skipped）。
- Phase 13 Review 完整流程 + 真实通知已全部完成。
- Phase 14 已启动：Write-Back 语义文档更新 + E2E 治理测试。
- `src/pep/markdown_updater.py`：Markdown section 级别定位与更新。
  - find_section / replace_section / append_to_section / insert_after_line / replace_line。
  - 支持 heading 匹配、regex 行匹配。
- WritebackEngine 进化：WritebackPlan 新增 match 字段 + 4 种 directive 操作。
  - section_replace / section_append / line_insert / line_replace。
  - 通过 markdown_updater 执行语义级别文档更新。
- `src/review/feedback_api.py`：FeedbackAPI 外部 reviewer 入口。
  - register / list_pending / submit / get_result。
  - in-memory 存储，可从外部提交 approve/reject/revision feedback。
- E2E 治理测试覆盖 5 条完整治理路径：
  - question→inform→applied（快速路径）
  - correction→review→approve→applied→writeback
  - scope-change→approve→escalation→reject→terminal
  - correction→review→revision→resubmit→approve→applied
  - delegation→contract→worker→report→auto-apply
- 228 项 pytest 测试全部通过（1 skipped）。
- Phase 14 Write-Back 语义文档更新 + E2E 治理测试已全部完成。
- Phase 15 已启动：Real Worker Adapter (LLM + HTTP)。
- `src/workers/` 包：WorkerConfig / WorkerRegistry / LLMWorker / HTTPWorker。
- WorkerConfig：dataclass，API key 通过环境变量读取（api_key_env → os.environ.get），不硬编码。
- WorkerRegistry：按 worker_type 注册和获取 worker 实例。
- LLMWorker：OpenAI-compatible API（兼容阿里云 DashScope），contract → prompt → LLM → report。
  - stdlib urllib.request（无外部依赖），指数退避重试，temperature 0.3。
  - 真实 LLM 调用测试通过（DashScope qwen-plus，1.44s 响应）。
- HTTPWorker：向外部 API endpoint POST contract，解析 response 为 report。
- 253 项 pytest 测试全部通过（1 skipped）。
- Phase 15 Real Worker Adapter 已全部完成。
- Phase 16 已启动：Pack Runtime Loader。
- `src/pack/` 包：ManifestLoader / ContextBuilder / OverrideResolver。
- `src/pack/manifest_loader.py`：PackManifest dataclass + load/load_dict 加载器。
  - 解析 pack-manifest.json，校验必填字段（name/version/kind）。
  - 支持完整字段集：provides, intents, gates, always_on, on_demand, rules 等。
- `src/pack/context_builder.py`：ContextBuilder + PackContext。
  - 多层 pack 注册（platform → instance → project-local）。
  - 合并 intents/gates/document_types（去重保序）。
  - 加载 always_on 文件内容，rules 深度合并。
- `src/pack/override_resolver.py`：RuleConfig dataclass + resolve/default_rule_config。
  - RuleConfig 统一承载 PDP 所有 resolver 的可配置规则。
  - resolve(PackContext) 将 pack 规则叠加到平台默认值上。
  - default_rule_config() 返回当前硬编码默认值。
- PDP 5 个 resolver 全部重构：classify/resolve 新增可选 rule_config 参数。
  - None 时使用硬编码默认值（向后兼容）。
  - 非 None 时从 RuleConfig 读取规则。
- decision_envelope.build_envelope() 新增可选 rule_config 参数。
- 官方实例 doc-loop-vibe-coding 的 pack-manifest.json 可成功加载并消费。
- 288 项 pytest 测试全部通过（1 skipped）。
- Phase 16 Pack Runtime Loader 已全部完成。
- Phase 17 已启动：Audit & Tracing System。
- `src/audit/` 包：AuditLogger / TraceContext / MemoryAuditBackend / FileAuditBackend。
- `src/audit/trace_context.py`：TraceContext (frozen dataclass) + new_trace / child_trace。
  - trace_id 串联 PDP → PEP → writeback 全链路。
- `src/audit/audit_logger.py`：AuditEvent + AuditBackend Protocol + AuditLogger。
  - MemoryAuditBackend：内存存储（测试/轻量场景）。
  - FileAuditBackend：JSON Lines 文件存储。
  - AuditLogger：多后端分发 + emit/query 接口。
- PDP decision_envelope.build_envelope() 集成审计：
  - 新增可选 audit_logger + trace_ctx 参数。
  - 6 种审计事件：input_received, intent_classified, gate_resolved, delegation_decided, escalation_decided, precedence_resolved。
  - envelope 中新增 trace_id 字段。
- PEP executor 集成审计：
  - 新增可选 audit_logger 构造参数。
  - 3 种审计事件：execution_started, review_feedback, writeback_completed。
- 全链路审计测试确认 ≥7 条治理事件覆盖 pdp + pep 两个阶段。
- 313 项 pytest 测试全部通过（1 skipped）。
- Phase 17 Audit & Tracing System 已全部完成。
- Phase 18 已启动：Validator/Checks/Trigger Framework。
- `src/validators/` 包：Validator / Check / Trigger Protocol + Registry + 内置实现。
- `src/validators/base.py`：3 个 Protocol（Validator / Check / Trigger）+ 3 个 Result dataclass。
- `src/validators/registry.py`：ValidatorRegistry（按名称注册/获取/列出 validators/checks/triggers）。
- `src/validators/schema_validator.py`：SchemaValidator（JSON Schema 校验，内置 jsonschema）。
- `src/validators/script_validator.py`：ScriptValidator（Python 函数调用作为校验器）。
- `src/validators/trigger_dispatcher.py`：TriggerDispatcher（事件路由 + 多 handler 分发）。
- `src/pep/executor.py` 进化：新增可选 validator_registry 构造参数。
  - delegation report 后自动调用 pack validators（结果存入 pack_validations）。
  - writeback 前自动调用 pack checks（失败时阻止写回 + 记录 writeback_blocked_by）。
- 348 项 pytest 测试全部通过（1 skipped）。
- Phase 18 Validator/Checks/Trigger Framework 已全部完成。
- Phase 19 已启动：Official Instance E2E Validation。
- `tests/test_official_instance_e2e.py`：40 项 E2E 测试。
  - ManifestLoader 加载官方实例 manifest，字段完整。
  - ContextBuilder 合并 always_on 内容、intents、gates、document_types。
  - OverrideResolver 从实例 pack 消解出有效 RuleConfig。
  - PDP 使用实例规则后决策结果符合预期（question→inform、correction→review、scope-change→approve）。
  - PDP + audit 全链路，审计事件 ≥4 种类型。
  - PEP inform 快速路径产出 write-back 文件。
  - SchemaValidator + ScriptValidator 校验 delegation report。
  - Blocking check 阻止 writeback；passing check 允许 writeback。
  - TriggerDispatcher 基于实例 manifest triggers 分发事件。
  - 完整治理链 E2E：inform/delegation/review-approve/validators 四条路径。
  - Bootstrap 产出通过 validate_doc_loop.py 校验。
- 387 项 pytest 测试全部通过（2 skipped）。
- Phase 19 Official Instance E2E Validation 已全部完成。
- Phase 20 已启动：Worker Collaboration Modes (Handoff + Subgraph)。
- `src/collaboration/` 包：CollaborationMode 枚举 + ModeExecutor Protocol。
- `src/collaboration/modes.py`：CollaborationMode(worker/handoff/subgraph) + ModeExecutor Protocol。
- `src/collaboration/handoff_mode.py`：HandoffRequest dataclass + prepare/execute/_build_handoff。
  - 显式控制权转移：fire-and-transfer（区别于 worker 的 fire-and-collect）。
  - 生成 Handoff 对象（符合 handoff.schema.json）。
  - 审计事件：handoff_initiated / handoff_completed / handoff_failed。
- `src/collaboration/subgraph_mode.py`：SubgraphContext dataclass + create_context/execute/merge_result。
  - 隔离执行上下文（namespace）+ 状态快照（state_snapshot）。
  - delta 捕获：artifacts_changed / assumptions / unresolved_items。
  - merge_result：受控合并 delta 到父状态。
  - 审计事件：subgraph_created / subgraph_completed / subgraph_failed。
- `src/pdp/delegation_resolver.py` 进化：_select_mode() 基于 RuleConfig.extra 选择协作模式。
  - 默认 supervisor-worker；pack 可通过 extra.collaboration_mode 覆盖为 handoff/subgraph。
  - mode 影响 worker_only / requires_review / allow_handoff 字段。
- `src/pack/override_resolver.py` 进化：RuleConfig 新增 extra 字段（dict[str, object]）。
- `src/pep/executor.py` 进化：_execute_delegation 重构为模式分发。
  - _execute_worker_mode：保持原有 supervisor-worker 逻辑不变。
  - _execute_handoff_mode：调用 handoff_mode.prepare/execute + RSM → waiting_review。
  - _execute_subgraph_mode：调用 subgraph_mode.create_context/execute + RSM → waiting_review。
- 414 项 pytest 测试全部通过（2 skipped）。
- Phase 20 Worker Collaboration Modes 已全部完成。
- 下一步：方向选择。
- Phase 21 已启动：Checkpoint Persistence + Direction Template。
- `src/workflow/checkpoint.py`：write_checkpoint / read_checkpoint / validate_checkpoint 工具函数。
- `tests/test_checkpoint.py`：17 项 pytest 测试全部通过。
- `design_docs/stages/_templates/Direction Candidates Template.md`：候选方向文档化模板。
- `design_docs/tooling/Document-Driven Workflow Standard.md`：新增 Checkpoint 触发时机 + 方向模板段落。
- `.codex/checkpoints/latest.md`：首个 checkpoint 已生成并通过 round-trip 验证。
- 431 项 pytest 测试全部通过（2 skipped）。
- Phase 21 Checkpoint Persistence + Direction Template 已全部完成。
- 下一步：方向选择（参见 `design_docs/direction-candidates-after-phase-20.md`）。
- 风险：无当前阻塞项。

## 最近一次写回

- `2026-04-08`: 初始化 doc-loop 骨架。
- `2026-04-08`: 对齐当前仓库的 repo-local adoption 入口，使 `docs/` 成为 project-local pack 的正式权威输入之一。
- `2026-04-08`: 起草 `doc-loop-vibe-coding` prototype authority rereview 的 planning-gate。
- `2026-04-08`: 形成 `doc-loop-vibe-coding` prototype authority rereview 结论并进入用户审核节点。
- `2026-04-09`: 用户审核通过 rereview 全部 4 项判断，Phase 2 关闭，确认 Phase 3 方向为 prototype cleanup。
- `2026-04-09`: Phase 3 Slice A 完成——将 SKILL.md、references/workflow.md、references/subagent-delegation.md 对齐到平台治理语义，修复 handoff 示例引用。
- `2026-04-09`: Phase 3 Slice B 完成——将 bootstrap 模板（AGENTS.md、Checklist、Phase Map、tooling 标准）对齐到平台治理语义。
- `2026-04-09`: Phase 4 Slice A 完成——创建 PDP Decision Envelope 说明文档与 JSON Schema，建立平台核心对象规格化框架。
- `2026-04-09`: Phase 4 Slice B 完成——创建 Intent Classification 说明文档与独立 JSON Schema，固化平台最小 intent 枚举、高影响标记、实例扩展机制。
- `2026-04-09`: Phase 4 Slice C 完成——创建 Gate Decision 说明文档与 JSON Schema，固化 gate-review state machine 映射规则，重构 Envelope 中 gate 子结构。
- `2026-04-09`: Phase 4 Slice D 完成——创建 Delegation Decision 说明文档与 JSON Schema，固化 5 个关键问题、拒绝/保护条件、Contract 关联。
- `2026-04-09`: Phase 4 Slice E 完成——创建 Escalation Decision 与 Precedence Resolution 说明文档及独立 JSON Schema，Envelope 全部子决策类型均已 `$ref` 收口，Phase 4 完结。
- `2026-04-10`: Phase 5 Slice A+B 完成——创建 Subagent Contract、Report、Handoff 的独立 JSON Schema (draft-2020-12)，更新 subagent-schemas.md 添加 schema 引用，解决 mode/status 枚举固化问题，Phase 5 完结。
- `2026-04-10`: Phase 6 Slice A+B 完成——实现 PDP 核心（intent_classifier + gate_resolver + decision_envelope）和 PEP 执行层（executor dry-run + action_log），25 项 pytest 全部通过，Phase 6 完结。
- `2026-04-10`: Phase 7 Slice A+B 完成——实现 delegation_resolver、escalation_resolver、precedence_resolver，集成到 envelope，47 项 pytest 全部通过，提取子 agent 机制需求 5 项，Phase 7 完结。
- `2026-04-10`: Phase 15 Slice A+B+C 完成——创建 workers 包（WorkerConfig + WorkerRegistry + LLMWorker + HTTPWorker），实现真实 worker 执行后端，LLM Worker 兼容 DashScope OpenAI-compatible API，真实调用验证通过，253 项 pytest 全部通过，Phase 15 完结。
- `2026-04-10`: Phase 16 Slice A+B+C 完成——创建 pack 包（ManifestLoader + ContextBuilder + OverrideResolver），重构 PDP 5 个 resolver 支持可选 rule_config 参数，实现 3 层配置覆盖（platform → instance → project-local），官方实例 manifest 可成功加载，288 项 pytest 全部通过，Phase 16 完结。
- `2026-04-10`: Phase 17 Slice A+B 完成——创建 audit 包（AuditLogger + TraceContext + Memory/File Backend），PDP 和 PEP 集成审计（全链路 9 种事件类型），向后兼容无破坏性，313 项 pytest 全部通过，Phase 17 完结。
- `2026-04-10`: Phase 18 Slice A+B 完成——创建 validators 包（Validator/Check/Trigger Protocol + Registry + SchemaValidator + ScriptValidator + TriggerDispatcher），PEP executor 集成 pack validators（report 后）和 checks（writeback 前），348 项 pytest 全部通过，Phase 18 完结。
- `2026-04-10`: Phase 19 Slice A+B 完成——官方实例 E2E 验证：ManifestLoader 加载实例 manifest、ContextBuilder 合并上下文、OverrideResolver 消解规则、PDP 使用实例规则决策、PEP 执行+writeback+validator/check 闭环、全链路审计、Bootstrap 产出校验。新增 40 项 E2E 测试，387 项 pytest 全部通过，Phase 19 完结。
- `2026-04-10`: Phase 20 Slice A+B 完成——Worker 协作模式（Handoff + Subgraph）：创建 collaboration 包（CollaborationMode 枚举 + HandoffRequest/SubgraphContext + prepare/execute/merge 全流程），PDP delegation_resolver 支持 mode 选择（pack 可覆盖），PEP executor 重构为模式分发（worker/handoff/subgraph 三路径），RuleConfig 新增 extra 字段，414 项 pytest 全部通过，Phase 20 完结。
- `2026-04-10`: Phase 21 Slice A+B+C 完成——Checkpoint Persistence + Direction Template：创建 src/workflow/checkpoint.py（write/read/validate 工具函数）+ 17 项 pytest 测试，创建候选方向文档化模板，更新 Document-Driven Workflow Standard 添加 checkpoint 触发时机，生成首个 checkpoint 并通过 round-trip 验证，431 项 pytest 全部通过，Phase 21 完结。
