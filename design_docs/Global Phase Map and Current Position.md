# 全局阶段图与当前位置

## 文档定位

本文件用于解释 `doc-based-coding-platform` 当前处于哪个阶段，以及历史阶段文档应如何阅读。

## 推荐初始阶段划分

下面是当前仓库已经按现实收窄后的阶段划分：

- Phase 0：平台权威文档与官方实例定位定型
- Phase 1：当前仓库的 repo-local doc-loop adoption 对齐
- Phase 2：`doc-loop-vibe-coding/` 原型 authority rereview
- Phase 3：基于 rereview 结果推进 runtime/spec formalization 或 prototype cleanup
- Phase 4：平台对象规格化（PDP/PEP schema formalization）
- Phase 5：子 agent 对象规格化（Subagent Contract/Report/Handoff schema formalization）
- Phase 6：PDP/PEP Runtime 骨架实现
- Phase 7：PDP 完整决策链（delegation/escalation/precedence resolver）
- Phase 8：PEP + Subagent 接口与实现（依赖反转 + StubWorker）
- Phase 9：Handoff 落地实现
- Phase 10：升级路径执行
- Phase 11：Review 状态机引擎
- Phase 12：文档写回 + 工作流闭环
- Phase 13：Review 完整流程 + 真实通知
- Phase 14：Write-Back 语义文档更新 + E2E 治理测试
- Phase 15：Real Worker Adapter (LLM + HTTP)
- Phase 16：Pack Runtime Loader
- Phase 17：Audit & Tracing System
- Phase 18：Validator/Checks/Trigger Framework
- Phase 19：Official Instance E2E Validation
- Phase 20：Worker Collaboration Modes (Handoff + Subgraph)
- Phase 21：Checkpoint Persistence + Direction Template
- Phase 22：v0.1-dogfood Release（Pipeline + MCP + Instructions）
- Phase 23：PackContext Downstream Wiring + Dogfood
- Phase 24：MCP Prompts/Resources + always_on 注入
- Phase 25：Extension Bridging (Pack → Registry)
- Phase 26：on_demand 懒加载 API
- Phase 27：Dogfood 深度验证
- Phase 28：Dogfood Feedback Remediation
- Phase 29：Self-Hosting Workflow Rule Formalization
- Phase 30：Dogfood Feedback Remediation Part 2 (F8 First)
- Phase 31：F4 Validator Diagnostics Follow-up
- Phase 32：First Stable Release Closure
- Phase 33：Error Recovery for Entry Points
- Phase 34：Structured Error Format Unification
- Phase 35：v1.0 Stable Release Confirmation

## 当前阶段判断

当前项目位置应表述为：

- Phase 0 已完成
- Phase 1 已完成并收口
- Phase 2 已完成并通过用户审核（2026-04-09）
- Phase 3 Slice A (Instance Guidance Text Alignment) 已完成
- Phase 3 Slice B (Bootstrap Scaffold Template Alignment) 已完成
- Phase 4 已启动：平台对象规格化
- Phase 4 Slice A (PDP Decision Envelope Schema) 已完成
- Phase 4 Slice B (Intent Classification Result Schema) 已完成
- Phase 4 Slice C (Gate Decision Schema) 已完成
- Phase 4 Slice D (Delegation Decision Schema) 已完成
- Phase 4 Slice E (Escalation + Precedence Schema 收口) 已完成
- Phase 4 全部完成
- Phase 5 已启动：Subagent Schema 规格化
- Phase 5 Slice A+B (Contract/Report/Handoff Schema) 已完成
- Phase 5 全部完成
- Phase 6 已启动：PDP/PEP Runtime 骨架实现
- Phase 6 Slice A+B (PDP Core + PEP Executor) 已完成
- Phase 6 全部完成
- Phase 7 已启动：PDP 完整决策链
- Phase 7 Slice A+B 已完成
- Phase 7 全部完成
- Phase 8 已启动：PEP + Subagent 接口与实现
- Phase 8 Slice A+B+C 已完成
- Phase 8 全部完成
- Phase 9 已启动：Handoff 落地实现
- Phase 9 Slice A+B 已完成
- Phase 9 全部完成
- Phase 10 已启动：升级路径执行
- Phase 10 Slice A+B 已完成
- Phase 10 全部完成
- Phase 11 已启动：Review 状态机引擎
- Phase 11 Slice A（状态机核心引擎）已完成
- Phase 11 Slice B（PEP 集成）已完成
- Phase 11 全部完成
- Phase 12 已启动：文档写回 + 工作流闭环
- Phase 12 Slice A（WritebackEngine 核心）已完成
- Phase 12 Slice B（PEP 集成）已完成
- Phase 12 全部完成
- Phase 13 已启动：Review 完整流程 + 真实通知
- Phase 13 Slice A（Notifier 适配器系统）已完成
- Phase 13 Slice B（ReviewOrchestrator + PEP 反馈集成）已完成
- Phase 13 全部完成
- Phase 14 已启动：Write-Back 语义文档更新 + E2E 治理测试
- Phase 14 Slice A（Markdown Updater + Directive Engine）已完成
- Phase 14 Slice B（E2E 治理测试 + FeedbackAPI）已完成
- Phase 14 全部完成
- Phase 15 已启动：Real Worker Adapter (LLM + HTTP)
- Phase 15 Slice A（Worker Registry + Config）已完成
- Phase 15 Slice B（LLM Worker）已完成
- Phase 15 Slice C（HTTP Worker）已完成
- Phase 15 全部完成
- Phase 16 已启动：Pack Runtime Loader
- Phase 16 Slice A（ManifestLoader + PackManifest）已完成
- Phase 16 Slice B（ContextBuilder + PackContext）已完成
- Phase 16 Slice C（OverrideResolver + PDP 规则注入）已完成
- Phase 16 全部完成
- Phase 17 已启动：Audit & Tracing System
- Phase 17 Slice A（AuditLogger + TraceContext + Backends）已完成
- Phase 17 Slice B（PDP/PEP 审计集成）已完成
- Phase 17 全部完成
- Phase 18 已启动：Validator/Checks/Trigger Framework
- Phase 18 Slice A（Protocol + Registry + 内置实现）已完成
- Phase 18 Slice B（PEP + Pack 集成）已完成
- Phase 18 全部完成
- Phase 19 已启动：Official Instance E2E Validation
- Phase 19 Slice A（装载链 + PDP 集成 E2E）已完成
- Phase 19 Slice B（PEP + Validator + WriteBack + Bootstrap E2E）已完成
- Phase 19 全部完成
- Phase 20 已启动：Worker Collaboration Modes (Handoff + Subgraph)
- Phase 20 Slice A（Handoff Mode + PDP/PEP 分发）已完成
- Phase 20 Slice B（Subgraph Mode + merge_result）已完成
- Phase 20 全部完成
- Phase 21 已启动：Checkpoint Persistence + Direction Template
- Phase 21 Slice A（checkpoint 工具函数 + 测试）已完成
- Phase 21 Slice B（方向模板 + Workflow Standard 更新）已完成
- Phase 21 Slice C（首个 checkpoint 生成）已完成
- Phase 21 全部完成
- Phase 22 已启动：v0.1-dogfood Release（Pipeline + MCP + Instructions）
- Phase 22 Slice 1（Pipeline + CLI）已完成
- Phase 22 Slice 2（MCP Server + GovernanceTools）已完成
- Phase 22 MCP dogfood 验证通过，修复 checkpoint 解析 bug
- Phase 22 Slice 3（Instructions Generator）已完成
- Phase 22 Slice 4（project-local pack C1-C8 约束）已完成
- Phase 22 收口（Slice 5 推迟至 dogfood 反馈后）
- Phase 22 全部完成
- Phase 23 已启动：PackContext Downstream Wiring + Dogfood
- Phase 23 Slice A（intent_classifier platform_intents 限制检查）已完成
- Phase 23 Slice B（gate_resolver allowed_gates 校验）已完成
- Phase 23 Slice C（OverrideResolver merged_intents/gates 贯通）已完成
- Phase 23 全部完成
- Phase 24 全部完成
- Phase 25 全部完成
- Phase 26 全部完成
- Phase 27 已启动：Dogfood 深度验证
- Phase 27 Slice A（真实 issue-report dogfood）已完成
- Phase 27 Slice B（状态恢复 dogfood）已完成
- Phase 27 Slice C（writeback 推进 dogfood）已完成
- Phase 27 全部完成
- Phase 28 已启动：Dogfood Feedback Remediation
- Phase 28 Slice A（issue-report 分类修正）已完成
- Phase 28 Slice B（checkpoint phase 同步）已完成
- Phase 28 全部完成
- Phase 29 已启动：Self-Hosting Workflow Rule Formalization
- Phase 29 Slice A（文档型自用边界 + pre-release runtime 边界 formalize）已完成
- Phase 29 全部完成
- Phase 30 已启动：Dogfood Feedback Remediation Part 2 (F8 First)
- Phase 30 Slice A（CLI `check` 输出分层）已完成
- Phase 30 全部完成
- Phase 31 已启动：F4 Validator Diagnostics Follow-up
- Phase 31 Slice A（skipped validator 诊断分类）已完成
- Phase 31 Slice B（official-instance skipped reason 覆盖）已完成
- Phase 31 全部完成
- Phase 32 已启动：First Stable Release Closure
- Phase 32 Slice A（稳定版边界定义）已完成
- Phase 32 Slice B（收口清单）已完成
- Phase 32 全部完成
- 产出文档：`docs/first-stable-release-boundary.md`
- Phase 33 已启动：Error Recovery for Entry Points
- Phase 33 Slice A（Pipeline 初始化容错）已完成
- Phase 33 Slice B（MCP 初始化降级模式）已完成
- Phase 33 Slice C（CLI --debug 模式）已完成
- Phase 33 全部完成
- Phase 34 已启动：Structured Error Format Unification
- Phase 34 Slice A（ErrorInfo dataclass）已完成
- Phase 34 Slice B（Pipeline init_errors 集成）已完成
- Phase 34 Slice C（MCP / CLI 对齐）已完成
- Phase 34 全部完成
- Phase 35 已启动：v1.0 Stable Release Confirmation
- Phase 35 Slice A（验证门执行 + B7 用户确认）已完成
- Phase 35 Slice B（CHANGELOG + 版本标记）已完成
- Phase 35 全部完成

**→ v1.0.0 Stable Released**

### Post-v1.0 工作（无 Phase 编号，按方向候选推进）

- Payload + Handoff Footprint Controlled Dogfood 完成：baseline `StubWorker` payload path 与 latest handoff footprint 恢复面在 controlled dogfood 中可一起成立；live DashScope `LLMWorker` 返回 schema-valid `completed` report，但真实 payload candidate 仍会漂移到 schema 不接受的枚举值（如 `upsert`、`text/markdown`），因此被保守归一化层丢弃；结果已记录到 `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`
- LLMWorker Live Payload Contract Hardening 完成：prompt contract 显式枚举允许值并补齐禁止示例，`content_type` 只做极窄 alias normalization，且当 LLM 主动尝试 payload 但所有 candidate 都被 guard 拒绝时，`status` 从 `completed` 下调为 `partial`；定向 55 passed, 1 skipped，全量 946 passed, 2 skipped
- Live Payload Rerun Verification 完成：单次受控 live DashScope rerun 在临时目录中返回合法 `artifact_payloads`，最终 payload writeback 成功命中 `docs/controlled-dogfood-llm.md`；结果记录于 `review/live-payload-rerun-verification-2026-04-16.md`
- Real-Worker Payload Adoption Judgment 完成：当前权威口径已收口为“`LLMWorker` real-worker payload path 已有 1 条正向 live signal，可继续作为受控 dogfood 路径观察，但仍不属于默认稳定面”；若要扩大 wording，最小额外证据门是再拿到 1 条在无新 runtime 改动前提下的独立受控 live success；结果记录于 `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- LLMWorker Structured Payload Producer Alignment 完成：`LLMWorker` 现在要求受控 JSON response contract，并把输出归一化为 schema-valid `Subagent Report`；成功路径最多保留 1 个合法 `artifact_payloads` candidate，非结构化响应回退为 `partial`，API 错误回退为 `blocked`，delegation -> LLMWorker -> payload-derived writeback mock 链已打通；定向 51 passed, 1 skipped，全量 942 passed, 2 skipped
- Handoff Authority-Doc Footprint（P4）完成：latest canonical handoff 的 4 字段 pointer contract 已同步到 Checklist / Phase Map / checkpoint / safe-stop helper，authority docs 现在能直接指向当前 safe stop 对应的 canonical handoff；定向 72 passed，全量 936 passed, 2 skipped
- 双发行包标准制定完成：`design_docs/tooling/Dual-Package Distribution Standard.md`
- 方向候选 A（双发行包实现切片）完成
- 方向候选 B（validator/check 契约收口）完成
- 方向候选 C（兼容元数据与版本声明）完成
- 方向候选 D（MCP pack info 刷新一致性）完成
- 方向候选 E（strict doc-loop runtime enforcement）完成
- 方向候选 F（handoff model-initiated invocation）完成
- 方向候选 J（conversation progression contract stability）完成
- 方向候选 I（safe-stop writeback bundle）完成
- 方向候选 H（external skill interaction interface）完成
- 层级化 pack topology（tree-scoped packs）完成
- Release 构建 + 安装 + adoption 端到端验证通过（原 v1.0.0，后降级为 preview）
- 完成边界协议（completion boundary protocol）完成
- overrides 字段消费（gap #12）完成
- decision logs 最小字段设计（research gap #1）完成
- 子 agent tracing 与 write-back 对接（research gap #2）完成
- 多实例共存冲突解决策略（research gap #4）完成
- 插件分发方向分析（research gap #5）完成（纯分析，无实现）
- 版本降级 1.0.0 → 0.9.1 → 0.9.2 → 0.9.3（preview 定位）
- Backlog 与储备方案管理标准完成
- CI/CD 本地自动化脚本完成（`scripts/build.py` + `scripts/release.py`）
- Pack Index Metadata & CLI Pack Management 完成
- BL-1 Driver 职责定义文档完成
- v0.9.3 release 自动化复验完成：823 passed, 2 skipped；`release/doc-based-coding-v0.9.3.zip`（147.0 KB）
- 状态面一致性收口完成：Checklist / Phase Map / CURRENT / checkpoint 已统一到 v0.9.3 preview 口径，并回到无 active planning-gate 的 safe stop
- 类型/接口依赖关系图谱提取 Slice 1 完成：`tools/dependency_graph/` — Pylance MCP 聚合 186 节点 / 56 边 + dogfood 验证 — 850 passed, 2 skipped
- 变更影响分析与耦合钩子 Slice 2 完成：ImpactAnalyzer BFS 传播 + CouplingStore/CouplingChecker + 5 个耦合标注 + 22 测试 — 872 passed, 2 skipped
- Workspace Parallel Task Orchestration 候选 A 已进入实现态：`design_docs/stages/planning-gate/2026-04-24-parallel-safe-subgraph-fanout-fanin.md` 的 Slice 1 foundation 已落地，`src/interfaces.py` / `src/collaboration/subgraph_mode.py` / `src/pep/executor.py` 已具备 companion objects、parent-issued lineage / namespace、以及显式 lineage hints 的 dispatch preflight；相关定向回归 `tests/test_collaboration.py tests/test_pep_delegation.py tests/test_worker_registry_executor.py` 全部通过（67 passed）
- Workspace Parallel Task Orchestration 候选 A 已继续进入 Slice 2 foundation：`src/interfaces.py` / `src/pep/executor.py` 已新增 `MergeBarrierOutcome` 与 parent-side merge barrier conflict classification helper，当前覆盖 `no_conflict` / `review_required` / `blocked`；相关定向回归在扩展后继续通过（60 passed）
- Workspace Parallel Task Orchestration 候选 A 已继续进入 Slice 3 foundation：`src/interfaces.py` / `src/pep/executor.py` / `src/pep/writeback_engine.py` 已新增 `GroupedReviewOutcome`、grouped review audit events、`grouped_review_state` 镜像、grouped review write-back summary interface，以及 `all_clear` 下的 child payload write-back；相关定向回归 `tests/test_collaboration.py tests/test_pep_writeback_integration.py` 通过（60 passed）
- Workspace Parallel Task Orchestration 候选 A 已完成 post-Slice3 方向分析：`design_docs/parallel-safe-subgraph-post-slice3-direction-analysis.md` 已把下一阶段问题收窄为“真实 multi-child dispatch 应否继续留在 executor 内部”；当前默认推荐下一条 planning-gate 为 `Executor-local Real Multi-Child Subgraph Batch`
- Workspace Parallel Task Orchestration 候选 A 已切换到新的 active planning-gate：`design_docs/stages/planning-gate/2026-04-24-executor-local-real-multichild-subgraph-batch.md`；当前实施入口已收窄为 Slice 1：`parent-built child batch input + executor dispatch loop`
- Workspace Parallel Task Orchestration 候选 A 已完成 Executor-local multi-child Slice 1：`src/pep/executor.py` 现已支持 parent-provided `parallel_children` batch hints、真实多 child dispatch loop、多个 `child_execution_records` / `subgraph_contexts`，并已验证 `all_clear` real multi-child grouped child payload write-back；相关回归 `tests/test_collaboration.py tests/test_pep_writeback_integration.py` 共 63 项通过
- Workspace Parallel Task Orchestration 候选 A 暴露出新的方向边界：当前 strict preflight 对 disjoint `allowed_artifacts` 的要求，使 conflict-bearing `review_required` grouped review 在真实 batch 正常路径上变得难以到达；下一步应先做窄 direction analysis，而不是直接继续编码
- Workspace Parallel Task Orchestration 候选 A 已继续收窄为新的 direction analysis：`design_docs/parallel-safe-subgraph-conflict-bearing-grouped-review-direction-analysis.md`；当前默认推荐是继续保持 strict preflight，并把 real multi-child 第一版权威边界写成 `all_clear-only`
- Workspace Parallel Task Orchestration 候选 A 当前阶段已收口：`design_docs/stages/planning-gate/2026-04-24-executor-local-real-multichild-subgraph-batch.md` 已完成，strict preflight + `all_clear-only` 已被采纳为 real multi-child 第一版边界；若未来要支持 conflict-bearing grouped review，应另起 `shared-review zone` planning-gate
- Workspace Parallel Task Orchestration 候选 A 已继续收窄出新的后续方向：`design_docs/parallel-safe-subgraph-shared-review-zone-direction-analysis.md` 已把下一条潜在 planning-gate 收束为 `Shared-Review Zone Contract And Preflight`
- Workspace Parallel Task Orchestration 候选 A 已切换到新的 active planning-gate：`design_docs/stages/planning-gate/2026-04-24-shared-review-zone-contract-and-preflight.md`；当前实施入口已收窄为 Slice 1：`shared-review zone companion fields + preflight exception surface`
- Workspace Parallel Task Orchestration 候选 A 已进入 shared-review zone Slice 1：`src/interfaces.py` 已新增 `ParallelChildTask.shared_review_zone_id`，`src/pep/executor.py` 的 preflight 已新增 `overlap_decisions` 并支持 same-artifact zone-driven overlap 例外；相关定向回归 `tests/test_collaboration.py -k "shared_review_zone or overlapping_allowed_artifacts"` 通过（4 passed）
- Workspace Parallel Task Orchestration 候选 A 已进入 shared-review zone Slice 2：merge/grouped review 结果面现已保留 `review_driver` 与 `shared_review_zone_ids`，并可把 zone-driven `review_required` 与普通 conflict overlap 区分开；相关定向回归 `tests/test_collaboration.py -k "zone_driven_review_required or shared_review_zone_driver"` 通过（2 passed）
- Workspace Parallel Task Orchestration 候选 A 已进入 shared-review zone Slice 3：`src/pep/writeback_engine.py` 的 grouped review summary 已对齐 `review_driver` 与 `shared_review_zone_ids`；相关定向回归 `tests/test_pep_writeback_integration.py -k "summary_includes_grouped_review_metadata"` 通过（1 passed）
- Workspace Parallel Task Orchestration 候选 A 当前阶段已再次收口：`design_docs/stages/planning-gate/2026-04-24-shared-review-zone-contract-and-preflight.md` 已完成；下一步更值得单独分析的问题是 zone-approved payload writeback 语义，而不是继续扩当前 gate
- Workspace Parallel Task Orchestration 候选 A 已继续收窄为新的 direction analysis：`design_docs/shared-review-zone-approved-payload-writeback-direction-analysis.md` 已把下一条潜在 planning-gate 收束为 `Zone-Approved Payload Writeback Semantics`
- Workspace Parallel Task Orchestration 候选 A 已切换到新的 active planning-gate：`design_docs/stages/planning-gate/2026-04-24-zone-approved-payload-writeback-semantics.md`；当前实施入口已收窄为 Slice 1：`approval eligibility contract`
- Workspace Parallel Task Orchestration 候选 A 已进入 zone-approved payload writeback Slice 1/2：`src/pep/writeback_engine.py` 已允许 `shared-review-zone-approved` path 进入 grouped child payload planning，并新增 `grouped_child_writeback_summary.eligibility_basis` 区分审批驱动写回与 `all_clear` 自动写回；相关定向回归通过（4 passed）
- Workspace Parallel Task Orchestration 候选 A 当前阶段已再次收口：`design_docs/stages/planning-gate/2026-04-24-zone-approved-payload-writeback-semantics.md` 已完成；当前 shared-review zone 已形成最小 approval-driven writeback 闭环，下一步更值得单独分析的问题转回 group 内 handoff / escalation terminal semantics 或更高层 orchestration boundary
- Workspace Parallel Task Orchestration 候选 A 已继续收窄为新的 direction analysis：`design_docs/group-internal-handoff-escalation-terminal-semantics-direction-analysis.md` 已把下一条潜在 planning-gate 收束为 `Group Internal Handoff / Escalation Terminal Bundle`
- Workspace Parallel Task Orchestration 候选 A 已切换到新的 active planning-gate：`design_docs/stages/planning-gate/2026-04-24-group-internal-handoff-escalation-terminal-bundle.md`；当前实施入口已收窄为 Slice 1：`terminal bundle contract + comparison review`
- Workspace Parallel Task Orchestration 候选 A 已完成本轮对照分析：`design_docs/group-internal-handoff-escalation-terminal-semantics-comparison.md` 已把 group-level terminal bundle、child-local keep merging、continue forbidding 三种 terminal semantics 做了对照，当前判断为 A 方案合理性最高
- Workspace Parallel Task Orchestration 候选 A 已进入 Slice 1 contract draft：`design_docs/group-internal-handoff-escalation-slice1-contract-draft.md` 已把推荐的最小 companion/result surface 收束为 `GroupTerminalOutcome`，并明确 terminal bundle 形成后默认停止普通 grouped review / grouped writeback 路径
- Workspace Parallel Task Orchestration 候选 A 已进入 Slice 1 实现起点：`src/interfaces.py` 已新增 `GroupTerminalOutcome`，`src/pep/executor.py` 已在显式 `escalation_recommendation` 证据下产出 `group_terminal_outcome` 并暂停普通 merge / grouped review 路径；当前 active planning-gate 已自然前推到 Slice 2：`result / summary / audit surface`
- Workspace Parallel Task Orchestration 候选 A 已进入 Slice 2 初始结果面：`GroupTerminalOutcome` 现已通过 `suppressed_surfaces` 显式标记当前被暂停的 `merge_barrier` / `grouped_review` / `grouped_child_writeback` 路径；当前更窄的下一步是决定 summary 与 audit 是否要镜像这层 suppression surface
- Workspace Parallel Task Orchestration 候选 A 已继续推进 Slice 2：`src/pep/writeback_engine.py` 现已把 group terminal suppression 镜像到 grouped review / grouped child writeback summary；当前更窄的下一步收束为 audit detail 是否也要统一镜像这层 suppression surface
- Workspace Parallel Task Orchestration 候选 A 已完成 Slice 2 的显式 escalation 路径收口：`src/pep/executor.py` 现已把 group terminal suppression 镜像到 `group_terminal_prepared` audit detail，result / summary / audit surface 形成最小闭环；当前下一窄切口切换到 Slice 3：显式 child handoff 证据接入 terminal bundle
- Workspace Parallel Task Orchestration 候选 A 已完成 `Group Internal Handoff / Escalation Terminal Bundle` planning-gate：显式 child `Handoff` 现已接入 `GroupTerminalOutcome`，invalid handoff 会经 `handoff_validator` 降级为 blocked child result；当前已无 active planning-gate，下一步应切换到新的方向候选讨论
- 当前已按新方向选择起草 `design_docs/orchestration-bridge-daemon-layer-direction-analysis.md`；AI 当前倾向是先做 thin orchestration bridge / daemon contract，而不是继续把更高层调度语义压进 executor
- 当前已按用户选择继续进入 bridge / daemon 分叉，并激活 `design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md`；当前 active slice 已收窄为 bridge-owned `work item` / `group item` primitive contract
- 当前已创建 `design_docs/orchestration-bridge-daemon-slice1-work-item-group-item-contract-draft.md`；当前推荐先固定 bridge primitive 的 identity / lifecycle / ownership boundary，再讨论 result projection 与 stop-condition
- 当前已在 Slice 1 draft 中补出 bridge / executor / governance kernel 的 ownership matrix 与 `BridgeWorkItem` / `BridgeGroupItem` 的最小 lifecycle transition table
- 当前结构性边界已进一步明确：bridge 的 `lifecycle_state` 只表达调度阶段，grouped review / group terminal / blocked 仍通过 compact governance footprint 暴露，而不膨胀成第二套 lifecycle 语义
- 当前已创建 `design_docs/orchestration-bridge-daemon-slice2-governance-result-projection-draft.md`，开始收口 Slice 2 的 compact result projection
- 当前已在 Slice 2 draft 中补出 `BridgeGroupItem` 的 compact result projection field matrix，并把 4 个字段的允许值与归一化规则写清
- 当前已新增 `design_docs/orchestration-bridge-daemon-slice2-work-item-rollup-draft.md`，把 `BridgeWorkItem` 的最小 roll-up 字段、surface precedence 与 writeback precedence 收口到单独草案
- 当前已新增 `design_docs/orchestration-bridge-daemon-slice3-stop-condition-boundary-draft.md`，把 lifecycle 与 roll-up 的 boundary matrix 收口到单独草案
- 当前顺序决策的后半段也已完成；`design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md` 已收口为 COMPLETE
- 当前已按用户选择进入 `bridge runtime primitives`，并激活 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-runtime-primitives.md`
- 当前 active slice 已进一步收窄为 runtime surface isolation：Slice 1 现已把现有 `src/runtime/bridge.py` 与 orchestration bridge primitive 的模块/命名边界写清
- 当前已新增 `design_docs/orchestration-bridge-runtime-primitives-slice2-model-helper-contract-draft.md`，把 `models.py` 的字段合同与 `projection.py` / `rollup.py` 的 pure helper contract 收口到单独草案
- 当前已新增 `design_docs/orchestration-bridge-runtime-primitives-slice3-stop-evaluator-tests-draft.md`，把 `stop_conditions.py` 的 evaluator contract 与 targeted tests boundary 收口到单独草案
- 当前已无新的结构性空洞；`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-runtime-primitives.md` 已收口为 COMPLETE
- 当前已切换到新的实现 gate：`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-models-helpers-implementation.md`
- 当前 active slice 已收窄为先实现 `BridgeWorkItem` / `BridgeGroupItem` models，再进入 projection / roll-up / stop helper 与 targeted tests；这条实现 gate 现也已完成，helper 层联合回归 21 passed
- 当前已切换到新的 active gate：`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-executor-result-adapter.md`
- 当前下一窄切口已转为 executor-result adapter：先固定 serialized dict execution result 到 `BridgeGroupItem`/`BridgeWorkItem` 输入的 contract，再落 adapter helper；这一条 gate 现也已完成，联合回归 25 passed
- 当前 post-adapter 分叉已收敛为 coordinator glue，并已完成 single-step coordinator helper 与 targeted tests，联合回归 29 passed
- 当前已切换到新的 active gate：`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-integration.md`
- 当前下一窄切口已转为 external-resolution landing contract：先固定 `waiting_external_resolution` 到 handoff / reviewer takeover landing surface 的映射，再落 landing helper；这一条 gate 现也已完成，联合回归 33 passed
- 当前 landing consumer wiring 已完成：landing artifact 现在已能映射到 handoff / escalation / reviewer_takeover 对齐的 consumer payload，联合回归 36 passed
- 当前已切换到新的 active gate：`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md`
- 当前下一窄切口已转为 landing dispatch contract：先固定 payload 到实际 delivery surface 的统一 dispatch protocol，再落 dispatch helper
- VibeCoding-Workflow 外部项目详细分析完成：逐条模式映射 + Anti-Drift / Run Budget / Milestone Replan 采纳 → pack rules 更新
- MCP 变更影响与耦合检查工具 Slice 3 完成：impact_analysis + coupling_check MCP 工具 + 9 测试 — 881 passed, 2 skipped
- 子 agent 研究综合报告完成：5 份外部研究综合 + Gap A/C/D 已验证修复 + P1-P4 优先级排序
- Worker Registry 驱动 Executor 动态选择完成（P1/BL-2）：_resolve_worker 动态路由 + audit 事件 + 向后兼容 + 11 测试 — 892 passed, 2 skipped
- Handoff Recovery Hardening 完成：CURRENT intake 增加 source_hash 校验 + 唯一 active canonical 断言 + refresh-current 冲突明细 + Authoritative Sources 降噪 + 6 测试 — 898 passed, 2 skipped
- Handoff Validator 独立化完成（P2）：默认 handoff validator + executor handoff validation 分支 + invalid handoff review fallback + handoff_validated/handoff_validation_failed 审计事件 + 7 测试 — 905 passed, 2 skipped
- Subagent Report richer writeback payload 前置切片完成（P3-prep）：`Subagent Report` schema 新增可选 `artifact_payloads`，固定 `changed_artifacts` 与 payload 边界，schema-driven report validation 继续兼容，HTTP worker 透传远端 payload + 7 测试 — 912 passed, 2 skipped
- artifact_payloads -> WritebackPlan Mapping（P3）完成：`WritebackEngine.plan()` 消费 `report.artifact_payloads`，严格执行 `allowed_artifacts` 与 project-root 路径边界，summary writeback 增加 payload planned/skipped 摘要，`create` 语义收紧为不覆盖已有文件，定向 36 测试与全量 922 passed, 2 skipped
- StubWorker Payload Producer Alignment（A1）完成：`StubWorkerBackend` 现在会在 `allowed_artifacts` 非空时产出 1 个受控 `artifact_payloads` 候选，文件边界直接复用首个允许路径、目录边界映射到固定子路径 `stub-worker-output.md`；官方示例 report 与实例 schema 校验同步，first-party delegation -> payload-derived writeback 最小闭环打通，定向 51 passed, 1 skipped；全量 931 passed, 2 skipped
- 对话行为约束规则重写完成：正面模板 + 发送前检查清单
- Dogfood Pipeline MCP Exposure（Slice A）完成：`promote_dogfood_evidence` MCP 工具暴露完整 4 步 dogfood pipeline（evaluate → build → assemble → dispatch）为单次调用，`run_full_pipeline()` 协调函数 + MCP 注册 + 12 集成测试 — 976 passed, 2 skipped
- Dogfood Consumer Writeback（Slice B）完成：`write_consumer_payloads()` 将 4 个消费者（direction-candidates / checklist / checkpoint / planning-gate）的 payload 自动追加到目标文档，幂等性 + 安全降级 + dry_run 兼容 + MCP `auto_writeback` 参数 + 16 测试 — 992 passed, 2 skipped
- Pack Manager Reserved Interfaces 完成：`_check_runtime_compatibility()` PEP 440 校验 + `_get_runtime_version()` + install 前 hard reject + SHA-256 checksum 写入 `platform.json` + `PackInfo.checksum` 字段 — 1058 passed, 2 skipped
- B-REF-1 Slice 1 LoadLevel 三级渐进加载测试覆盖完成：`test_pack_progressive_load.py` 新建 24 测试覆盖 METADATA/MANIFEST/FULL build、scoped build with levels、upgrade() 语义 — 1082 passed, 2 skipped- B-REF-1 Slice 2 Pipeline MANIFEST 降级完成：`Pipeline._load_packs()` 从 FULL 降级为 MANIFEST，`pack_context` 属性按需 upgrade，`process_scoped()` / `info()` 均使用 MANIFEST 级别 + 5 个新测试 — 1087 passed, 2 skipped
- B-REF-1 Slice 3 MCP get_pack_info 分级返回完成：`Pipeline.info()` 支持 level 参数（METADATA/MANIFEST/FULL）+ description 字段 + scope_path；MCP get_pack_info 工具新增 scope_path 和 level 参数 + 8 个新测试 — 1095 passed, 2 skipped
- B-REF-2 Pack Description 质量标准完成：质量标准文档（`design_docs/tooling/Pack Description Quality Standard.md`）+ `validate_description()` 验证函数 + 现有 pack 添加符合标准的 description + 9 个新测试 — 1104 passed, 2 skipped
- B-REF-3 Pack 内部组织规范完成：组织标准文档（`design_docs/tooling/Pack Internal Organization Standard.md`）+ `validate_pack_organization()` 验证函数（引用深度/TOC/嵌套引用检查）+ 13 个新测试 — 1117 passed, 2 skipped
- B-REF-7 Custom tool surface 合并审计完成 + `analyze_changes` 统一入口已实施：11 个 MCP tools（旧名保留为别名）+ 6 个新测试 — 1133 passed
- Agent Output 可见性临时方案完成：`src/workflow/agent_output.py`（OutputSink Protocol + FileSink）+ GovernanceTools.write_output() 集成 + `.codex/agent-output/latest.md` 输出面 + 10 个新测试 — 1127 passed, 2 skipped
- **VS Code Extension P0+P1 完成**：15 个 TypeScript 文件（extension.ts / MCPClient / ConstraintDashboard TreeView / GovernanceInterceptor 接口 / PassthroughInterceptor / CopilotLLMProvider / AgentSession 多 agent 数据模型），TypeScript 零类型错误，esbuild 构建成功，Python 回归 1133 passed, 2 skipped
- **Extension 安装向导完成**：`setup/wizard.ts` + `pythonDetector.ts` + `runtimeInstaller.ts` — 首次激活自动检测 Python 环境 → runtime 未安装时弹模态对话框 → 一键从 release/ 目录 wheel 安装或手动选择 zip → pip batch install → 自动配置 pythonPath → MCP 启动 → `.vscode/mcp.json` 自动生成
- **VS Code Extension P2-P7 完成**：Pack Explorer TreeView + Decision Log + StatusBar (P2) | File Save Interception (P3) | Copilot Intent Classification (P4) | BLOCK Explanation + Pack Generation (P4+) | Review Panel WebView (P5) | Terminal Monitor via Shell Integration API (P6) | File Lifecycle create/delete/rename Interception (P6+) | Chat Participant `@governance` with /check /decide /constraints /packs (P7) — esbuild 零错误，.vsix 打包 (19.55 KB) 安装验证通过
- **硬编码 Git Push 拦截完成**：仅拦截 `git push`（修改远程的唯一操作）；pull/fetch/clone 允许通过。三层实现：`gitRemoteGuard.ts` 终端正则 + `gitRemoteGuardScm.ts` SCM UI git wrapper + MCP `governance_decide` pre-check。1133 pytest + esbuild 通过；VSIX 0.1.2（23.3 KB）
- **全局记忆/文档/规则支持完成**：A→C→D 全路线 — P0 user-global pack kind（manifest_loader + context_builder + pipeline + 14 tests）+ P1 config.json 配置层（user_config.py + pipeline integration + 22 tests + docs）+ P2 Extension Config Management UI（TreeView + WebView + MCP）。36 个新 Python 测试 — 1197 passed, 2 skipped
- **Multica 架构研究完成**：`review/multica.md` — Skills hash 锁定 + 远程来源模式、agent-as-teammate 多态模型、严格层级边界工程实践；`review/research-compass.md` 已更新
- **Multica 深度研究三阶段完成**：`review/multica/` — Phase 1 架构深潜（01-architecture-deep-dive.md: Go backend 分层 + Daemon 架构 + 前端 monorepo + Skills 系统 + Autopilot + 多租户安全 + 12 大技术债务）、Phase 2 方向与不足分析（02-direction-and-weaknesses.md: 5 大发展方向 + 5 大不足 + 版本演进趋势 + 社区特征）、Phase 3 借鉴洞察（`review/multica-borrowing/borrowing-insights.md`: hash 锁定→pack 版本管理、Platform Bridge→多入口统一、知识复合克制启示、index-based 渐进加载、互补潜力分析）；`review/research-compass.md` 引用已更新为新文件夹结构
- **Pack Integrity Hash (pack-lock.json) 完成**：`src/pack/pack_integrity.py` — `compute_pack_hash()` 全目录 SHA-256 + `PackLockFile` CRUD + `verify_pack()` / `verify_all()` 验证；Pipeline `_load_packs()` 非阻塞 integrity warning + `install_pack()` 自动 lock + `remove_pack()` 自动 unlock + MCP 工具 `pack_lock`/`pack_unlock`/`pack_verify`；20 个新测试 — 1223 passed, 2 skipped
- **条件化 always_on 加载完成**：`ContextBuilder.build(scope_path=)` — 当 scope_path 非空时，跳过 scope_paths 声明不匹配的 pack 的 always_on 内容加载；无 scope_paths 的 pack（universal）始终包含；MANIFEST 级别不受影响；6 个新测试 — 1229 passed, 2 skipped
- **RuntimeBridge 注入完成**：`src/runtime/bridge.py` — 统一初始化 facade 封装 Config+Worker+Pipeline 生命周期；WorkerHealth 状态跟踪（READY/DEGRADED/UNAVAILABLE）+ _TrackedWorker 装饰器；CLI 入口已迁移使用 RuntimeBridge；refresh()/reload_config() 热更新支持；13 个新测试 — 1242 passed, 2 skipped
- **依赖方向反转（consumes 字段）完成**：PackManifest 新增 `consumes: list[str]` + `check_consumes()` 函数校验能力满足情况；Pipeline.info() 暴露 consumes_status；warning-only 不阻塞；5 个新测试 — 1247 passed, 2 skipped
- **check_reply_progression MCP 工具完成**：`src/workflow/reply_progression.py` — 回复末尾符合性检查（禁止模式检测 + 分析判断存在性 + 推进式提问存在性）；MCP 工具注册完成；9 个新测试 — 1256 passed, 2 skipped
- **代码层依赖方向约束文档化完成**：`design_docs/tooling/Module Dependency Direction Standard.md` — 6 层架构定义 + 已知例外表 + 消除计划；`scripts/lint_imports.py` — AST 扫描跨包 import 方向验证（排除 TYPE_CHECKING 块）+ 已知例外白名单；发现并登记 2 个已知例外（pack→workflow, pack↔pdp）— 1256 passed, 2 skipped
- **依赖方向违规消除完成**：(1) `pack→workflow` 违规消除 — `_discover_packs` 及 8 个辅助函数/常量从 `workflow/pipeline.py` 下沉到新模块 `pack/pack_discovery.py`，pipeline.py 改为 re-export；(2) `pack→pdp` 类型违规消除 — `ToolPermissionConfig`/`ToolPolicy`/`PermissionResult`/`PermissionLevel`/`parse_tool_permissions` 从 `pdp/tool_permission_resolver.py` 提取到 `interfaces.py`，tool_permission_resolver 改为 re-export；已知例外从 3 个减至 1 个（`pack→pdp` intent_classifier 延迟导入）— 1256 passed, 2 skipped
- **依赖方向违规全部消除**：最后 1 个已知例外（pack→pdp intent_classifier 延迟导入）通过将 `PLATFORM_INTENTS`/`IMPACT_TABLE`/`KEYWORD_MAP` 提取到 `interfaces.py` 消除，`lint_imports.py` 零已知例外、零违规 — 1256 passed, 2 skipped
- **HTTPWorker failure fallback schema alignment 完成**：`_error_report()` 的 `status: "failed"` → `"blocked"` + `escalation_recommendation: "escalate_to_supervisor"` → `"review_by_supervisor"` + 新增 `unresolved_items` 字段，现在与 `LLMWorker` 和 `Subagent Report` schema 完全一致 — 1257 passed, 2 skipped
- **Workspace Parallel Task Orchestration 方向分析完成**：新增 `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`，将“同工作区多任务并行”为何当前不成立收口为 `single-contract / single-worker / single-review` runtime 语义缺口，并基于 LangGraph / AutoGen / Multica / CrewAI 研究压缩为三条候选路径：A）parallel-safe subgraph fan-out/fan-in，B）first-class task-graph/team runtime，C）orchestration bridge / daemon layer；当前推荐先进入候选 A 的 planning-gate

## 阅读顺序

1. 先读本文件。
2. 再读 `design_docs/Project Master Checklist.md`。
3. 再读当前 active planning 或 phase 文档。
4. 再读 `docs/starter-surface.md`、`docs/README.md` 与当前任务直接相关的 `docs/` 权威文档。
5. 若需要当前仓库的切片与协议细节，再读 `design_docs/stages/README.md` 与 `design_docs/tooling/`。

## 当前结论

Phase 3-35 均已完成。原 v1.0.0 已降级为 preview 定位，当前版本为 **v0.9.4**。Post-v1.0 的方向候选 A-J 标准化切片全部完成（双发行包、validator/check 收口、兼容元数据、MCP 刷新、doc-loop enforcement、handoff 主动调用、conversation progression、safe-stop writeback、external skill interaction），并继续完成了真实模型 producer 主线上的 `LLMWorker Structured Payload Producer Alignment` 与后续 `Payload + Handoff Footprint Controlled Dogfood`。

Release 封装已通过完整验证链：构建（双包 wheel/sdist）→ 测试 → 打包。当前可分发安装包为 `release/doc-based-coding-v0.9.4.zip`（191.8 KB），最新全量回归基线为 1284 passed, 2 skipped。

2026-04-21 新增：Cline 外部项目研究完成（`review/cline.md`，7 借鉴点 + 9/10 差距分析），MCP 真实场景 dogfood 完成（5 症状，IC-001 意图分类器覆盖率提升，S3 `_EMPTY_PLANNING_GATE_MARKERS` 中文标记修复）。

2026-04-22 新增：完成 Codex 主链适配（`generate-instructions` 支持 `generic|codex|copilot` 与 `AGENTS.md` 推断）以及 VS Code extension LLM provider abstraction（命令层切到抽象 provider 契约，GitHub Copilot 保持默认实现）；targeted `pytest` 35 passed，`vscode-extension` esbuild 构建通过。

2026-04-23 新增：完成 docs-only 切片 `design_docs/stages/planning-gate/2026-04-23-host-interaction-surface-isolation.md`，新增权威文档 `docs/host-interaction-model.md`，把平台明确分成 Core Contract / Portable Runtime / Interaction Adapter / Host UX 四层，并把 Codex 独立入口 contract 收口为该方向下的首个子案例；当前仓库回到无 active planning-gate 状态。

2026-04-23 新增：完成 docs-only 切片 `design_docs/stages/planning-gate/2026-04-23-temporary-scratch-stable-docs-split.md`，新增 `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`，明确 `.codex/tmp/` 为推荐 scratch 面，并把 scratch → review / design_docs / docs 的 promotion 规则写入长期标准与 review/workflow 规范；当前仓库回到无 active planning-gate 状态。

2026-04-23 新增：完成 docs-only 切片 `design_docs/stages/planning-gate/2026-04-23-public-surface-convergence.md`，新增 authority 路由文档 `docs/starter-surface.md`，并将根 README、`docs/README.md`、`AGENTS.md`、安装文档与官方实例文档统一指向 starter surface；当前仓库继续保持无 active planning-gate 状态。

2026-04-23 新增：完成 docs-only 切片 `design_docs/stages/planning-gate/2026-04-23-codex-independent-entry-contract.md`，新增 authority 文档 `docs/codex-entry-contract.md`，把 Codex 的最短入口闭环、与 VS Code/Copilot extension 的职责边界，以及“Codex 不等于 extension 第二 provider”的判断收口为正式入口 contract；当前仓库继续保持无 active planning-gate 状态。

2026-04-23 新增：基于 llmdoc 借鉴完成一组连续的 docs-only 收口，并在无 active planning-gate 状态下形成新的 safe-stop handoff `2026-04-23_2238_llmdoc-derived-doc-surface-and-host-boundaries_stage-close`；当前默认回到方向候选面，后续主线收敛为 `scratch 轻量恢复协议`、`helper entry / companion surface`、`extension 第二 provider 扩展比较分析`。

2026-04-24 新增：完成 docs-only 切片 `design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md`，将 scratch recovery 的适用范围、四状态集合与最小恢复字段写入 `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md` 与 `design_docs/tooling/Document-Driven Workflow Standard.md`，并生成新的 safe-stop handoff `2026-04-24_1013_scratch-lightweight-recovery-protocol_stage-close`；当前仓库再次回到无 active planning-gate 状态，默认下一步回到 `helper entry / companion surface`、`scratch recovery 受控实现切片` 与 `extension 第二 provider 扩展比较分析` 的方向选择。

2026-04-24 补充：完成 docs-only 方向分析 `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`，明确当前平台尚未支持同工作区任务并行的根因不是缺少简单并发执行，而是 delegation 仍按单合同、单 worker、单结果、单 review 建模；`direction-candidates-after-phase-35.md` 已同步新增三条候选，其中当前 AI 倾向先进入候选 A：围绕 `subgraph` 建立 parallel-safe fan-out / fan-in contract，再决定是否演进到完整 `team/swarm` runtime。

2026-04-24 继续补充：用户已沿候选 A 推进，新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-24-parallel-safe-subgraph-fanout-fanin.md` 已创建；当前 active slice 已切到 `Parallel-Safe Subgraph Fan-Out / Fan-In`，本轮先锁定 `TaskGroup`、child lineage、`per-invocation` namespace、disjoint write set、barrier merge 与 grouped review outcome 的最小 contract，并明确把 full `team/swarm` runtime 与 orchestration daemon 保持在后续候选面。

2026-04-26 新增：用户提出新的 `project progress multi-graph` 主线，用于保留项目推进历史、表达多图并发推进、支持 typed edge 与节点团压缩/展开。原 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md` 因 scope interrupt 暂停于 Slice 1 入口；随后已完成新的 foundation gate `design_docs/stages/planning-gate/2026-04-26-project-progress-multi-graph-foundation.md`，新增 `tools/progress_graph/model.py` / `query.py` 与 `tests/test_progress_graph.py`（6 passed），当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `doc-loop projection and snapshot persistence`。

2026-04-26 继续新增：当前已沿推荐方向进入新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md`；本轮 scope 收窄为把 `.codex/checkpoints/latest.md`、`design_docs/stages/planning-gate/` 与 `design_docs/Project Master Checklist.md` 投影到 `ProgressMultiGraphHistory`，并把 snapshot 持久化到 `.codex/progress-graph/latest.json`；当前明确不进入 UI export、scheduler integration 或通用 markdown parser。

2026-04-26 继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md` 已完成；`tools/progress_graph/doc_projection.py` 已把 checkpoint / planning-gate / checklist 投影成真实 snapshot history，并已在真实仓库写出 `.codex/progress-graph/latest.json`；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `user-facing graph export surface`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-user-facing-graph-export-surface.md` 已完成；新增 `tools/progress_graph/export.py` 与 `tests/test_progress_graph_export.py`，把 current history 收口成稳定的 raw + display 双视图 export schema，并为 cross-graph edge 增补 display-aware endpoint；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `static renderer / preview consumer over export surface`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-graphviz-preview-consumer.md` 已完成；新增 `tools/progress_graph/graphviz.py` 与 `tests/test_progress_graph_graphviz.py`，把现有 export surface 转成 Graphviz DOT preview，并已在真实仓库写出 `.codex/progress-graph/latest.dot`；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `doc source enrichment and linkage refinement`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-html-preview-consumer.md` 已完成；新增 `tools/progress_graph/html_preview.py` 与 `tests/test_progress_graph_html_preview.py`，把现有 export surface 进一步转成可直接打开的 `.codex/progress-graph/latest.html`，并用内联 SVG 提供第一版轻量化图形展示；到这里，progress graph 的轻量展示功能已达到初步完成，当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `doc source enrichment and linkage refinement`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-phase-map-current-position-projection.md` 已完成；`tools/progress_graph/doc_projection.py` 已新增 `phase-map-current-position` graph，把 `design_docs/Global Phase Map and Current Position.md` 的 recent date-prefixed timeline entries 以及显式 planning-gate 引用投影到 `.codex/progress-graph/latest.json`，并同步刷新 `.codex/progress-graph/latest.dot` / `.html`；`tests/test_progress_graph_doc_projection.py` 已通过 2 个 targeted tests，`progress_graph` 全套验证 17 passed；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `direction-analysis candidate projection`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-direction-analysis-candidate-projection.md` 已完成；`tools/progress_graph/doc_projection.py` 已新增 `direction-analysis-current` graph，把当前 `project-progress` follow-up direction-analysis 文档的 `### A/B/C` 候选项投影到 `.codex/progress-graph/latest.json`，并把“当前 AI 倾向判断”映射成 recommended candidate；当前 source path 不再写死，而是从 `design_docs/Project Master Checklist.md` 中解析最新的 `project-progress-*-followup-direction-analysis.md` 记录；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `global direction-candidates aggregation`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-global-direction-candidates-aggregation.md` 已完成；`tools/progress_graph/doc_projection.py` 已新增 `direction-candidates-global` graph，把 `design_docs/direction-candidates-after-phase-35.md` 中标题含 `project progress` 的 section 投影到 `.codex/progress-graph/latest.json`，并把每个 section 的 `- 候选 1/2/3` 聚合成 candidate nodes；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `richer candidate-doc linkage refinement`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-richer-candidate-doc-linkage-refinement.md` 已完成；`tools/progress_graph/doc_projection.py` 已为 checklist / phase map / global direction-candidates 图层接入稳定 `source-document` 入口节点，并把 current/global candidate nodes 的 `basis_refs` 翻译成 explicit cross-graph linkages；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `research-compass / external-reference projection`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-external-reference-projection.md` 已完成；`tools/progress_graph/doc_projection.py` 已新增 `research-compass-current` graph，把 `review/research-compass.md` 的 stable `source-document` 与 `全量研究地图` 研究入口投影到 `.codex/progress-graph/latest.json`，并把 candidate `basis_refs` 翻译成 explicit external-reference linkages；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `VS Code / host-specific preview integration`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-host-preview-integration.md` 已完成；`vscode-extension` 已新增 `docBasedCoding.openProgressGraphPreview` 命令与最小 WebView panel，可直接在 VS Code 内打开 `.codex/progress-graph/latest.html`；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `richer research-compass topic projection`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-research-compass-topic-projection.md` 已完成；`tools/progress_graph/doc_projection.py` 已为 `research-compass-current` graph 接入 `按问题检索` topic layer，并通过 topic -> entry `reference` edge 把主题入口连到稳定研究条目；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `preview workflow integration`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-preview-workflow-integration.md` 已完成；`vscode-extension/src/views/progressGraphPreview.ts` 已升级为 singleton 独立 WebView workflow，重复打开会 reveal 现有 panel，panel 内已具备 `Refresh Preview` / `Reveal Artifact`，并通过 `npm run build`；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `preview artifact refresh pipeline integration`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-preview-artifact-refresh-pipeline-integration.md` 已完成；`vscode-extension` 已通过 workspace Python 复用 `tools.progress_graph` 现有 build/write helpers，使 standalone preview 的 `Refresh Preview` 成为 regenerate `.codex/progress-graph/latest.json` / `.dot` / `.html` 后再 reload 的 end-to-end workflow，并已通过 `npm run build` 与真实 artifact regenerate 验证；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `non-project-progress candidate aggregation`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-non-project-progress-candidate-aggregation.md` 已完成；`tools/progress_graph/doc_projection.py` 已把 `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 且采用 `### 新候选 A/B/C` 的 section 纳入现有 `direction-candidates-global` graph，并把 candidate-local `当前判断：**推荐**` 映射到 recommended surface；`tests/test_progress_graph_doc_projection.py` 已通过且真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已刷新；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `legacy non-project-progress format aggregation`。

2026-04-26 再继续新增：`design_docs/stages/planning-gate/2026-04-26-project-progress-legacy-non-project-numbered-candidate-aggregation.md` 已完成；`tools/progress_graph/doc_projection.py` 已把 `design_docs/direction-candidates-after-phase-35.md` 中标题不含 `project progress`、且沿用 `- 候选 1/2/3` 与 section-level `当前倾向` 的 legacy numbered sections 纳入现有 `direction-candidates-global` graph；`tests/test_progress_graph_doc_projection.py` 已通过且真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已刷新；验证中发现的 section recency 语义问题已被登记到 `design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`，当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `plain A/B/C legacy candidate aggregation`。

2026-04-27 再继续新增：`design_docs/stages/planning-gate/2026-04-27-project-progress-legacy-plain-lettered-candidate-aggregation.md` 已完成；`tools/progress_graph/doc_projection.py` 已把 `design_docs/direction-candidates-after-phase-35.md` 中标题不含 `project progress`、且采用 plain `### A./B./C.` 的 legacy sections 纳入现有 `direction-candidates-global` graph，并保持 plain / `新候选` 标题前缀分离；`tests/test_progress_graph_doc_projection.py` 已通过且真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已刷新；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `extended plain lettered variant aggregation`。

2026-04-27 再继续新增：`design_docs/stages/planning-gate/2026-04-27-project-progress-legacy-extended-plain-lettered-candidate-aggregation.md` 已完成；`tools/progress_graph/doc_projection.py` 已把 `design_docs/direction-candidates-after-phase-35.md` 中标题不含 `project progress`、且采用无前缀 extended plain lettered variants 的 legacy sections 纳入现有 `direction-candidates-global` graph；`tests/test_progress_graph_doc_projection.py` 已通过且真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已刷新；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `global direction-candidates recency semantics`。

2026-04-27 再继续新增：当前已沿推荐方向进入新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`；本轮 scope 收窄为修正 `direction-candidates-global` 的 latest/current section 选择规则，使其不再直接依赖“最后出现的 numbered section”；当前明确不进入 companion prose projection、selected-next-step linkage 或 UI 变更。

2026-04-27 再继续新增：`design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md` 已完成；`tools/progress_graph/doc_projection.py` 现已按 section title 日期优先、文档更早位置 tie-break 的规则选择 `direction-candidates-global` 的 latest numbered section，并把 `recency_date` 写入 metadata；`tests/test_progress_graph_doc_projection.py` 已新增顶部插入 numbered section 的 targeted probe 并通过（3 passed），真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已刷新；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `companion prose projection`。

2026-04-27 release-preview 后继续新增：用户已基于 `design_docs/v0.9.5-preview-release-followup-direction-analysis.md` 选定新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-27-release-close-handoff-current-refresh-hardening.md`；本轮 scope 收窄为处理 `0.9.5` release-close 与 latest handoff pointer / `.codex/handoffs/CURRENT.md` / authority-doc footprint 之间的漂移，先固定 drift surface、writeback target 与是否需要真正 refresh hardening 的边界；当前明确不进入更宽的 handoff history/tracing 重构，也不回到 `companion prose projection`。

后续附加完成项：decision logs 最小字段设计、子 agent tracing 与 write-back 对接、多实例共存冲突解决策略、overrides 字段消费、hierarchical pack topology、completion boundary protocol、CI/CD 本地自动化脚本、Pack Index Metadata & CLI Pack Management、BL-1 Driver 职责定义文档、P4 handoff authority-doc footprint、`LLMWorker Structured Payload Producer Alignment`、`Payload + Handoff Footprint Controlled Dogfood`，以及 `LLMWorker Live Payload Contract Hardening`。详见上方"Post-v1.0 工作"条目。

低优先级 backlog（BL-2/3 adapter-registry/转接层）已结构化记录在 `design_docs/direction-candidates-after-phase-35.md`。

当前仓库已经完成 `Dogfood Issue Promotion / Feedback Packet Pipeline` 全链路：contract 定义（promotion threshold T1-T4 / suppression S1-S3 / issue candidate 12 字段 / feedback packet 9+3 字段 / 消费者边界 6×矩阵）→ dry-run 验证 → interface draft（5 数据结构 + 4 函数签名）→ 实现（`src/dogfood/` 4 模块：models / evaluator / builder / dispatcher）→ 16 单元测试 + 2 E2E 测试全部通过 → 全量基线 964 passed, 2 skipped。在此基础上，Slice A 将 pipeline 暴露为 MCP 工具 `promote_dogfood_evidence`，新增 `run_full_pipeline()` 协调函数 + 12 集成测试，全量基线升至 976 passed, 2 skipped。

## 当前 Handoff Footprint

- handoff_id: `2026-04-27_1931_global-direction-candidates-section-recency-semantics_stage-close`
- source_path: `.codex/handoffs/history/2026-04-27_1931_global-direction-candidates-section-recency-semantics_stage-close.md`
- scope_key: `global-direction-candidates-section-recency-semantics`
- created_at: `2026-04-27T19:31:29+08:00`

施工中提取的子 agent 机制需求（全部完成）：

1. ~~**Contract 生成接口**~~：已由 `src/subagent/contract_factory.py` 实现（Phase 8）。
2. ~~**Worker 调用运行时**~~：已由 `src/interfaces.py` WorkerBackend Protocol + `src/subagent/stub_worker.py` StubWorkerBackend 实现（Phase 8）。真正的 Worker adapter 留给后续 Phase。
3. ~~**Report 收集与校验**~~：已由 `src/subagent/report_validator.py` 实现（Phase 8）。
4. ~~**Handoff 落地**~~：已由 `src/subagent/handoff_builder.py` + PEP executor 实现（Phase 9）。
5. ~~**升级路径执行**~~：已由 `src/pep/notification_builder.py` + `src/pep/stub_notifier.py` + PEP executor 实现（Phase 10）。

子 agent 机制 5 项需求全部完成。Phase 33 已完成：Pipeline 初始化容错、MCP 降级模式、CLI --debug 模式。首个稳定 release 的边界与收口条件已写入 `docs/first-stable-release-boundary.md`。
