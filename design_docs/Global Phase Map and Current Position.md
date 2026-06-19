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

2026-04-28 再继续新增：`design_docs/stages/planning-gate/2026-04-27-release-close-handoff-current-refresh-hardening.md` 已完成；当前已确认 release-close 漂移来自“缺少新的 canonical release-close handoff”，并已沿既有 `generate handoff -> refresh current` workflow 生成 `2026-04-28_0548_release-close-handoff-current-refresh-hardening_stage-close`，使 `CURRENT.md`、Checklist、Phase Map 与 checkpoint 的 handoff footprint 重新统一；真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 也已按新状态面刷新，当前仓库再次回到无 active planning-gate 状态，等待从 `design_docs/v0.9.5-preview-release-followup-direction-analysis.md` 中重新选择下一条 post-release 窄主线。

2026-04-28 再继续新增：用户已在 release-close safe stop 后重新选择 `companion prose projection recovery`；当前已创建新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md`，并新增 Slice 1 草案 `design_docs/project-progress-companion-prose-projection-slice1-draft.md`；本轮 scope 先固定 `用户选定下一步`、`当前更窄的入口`、`当前实际下一条 planning-gate` 三类 companion prose 的 projection contract，当前明确不进入 post-release dogfood/install path tightening，也不继续 extension runtime/package follow-up validation。

2026-04-28 再继续新增：`design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md` 已完成；`tools/progress_graph/doc_projection.py` 现已把 pure companion prose sections 纳入 `direction-candidates-global`，并为 `selected-next-step` / `narrowed-entry` / `actual-next-gate` 建立 section-local 独立 node；当 prose 中出现显式 planning-gate path 时，`actual-next-gate` 还能建立到 `planning-gates-index` 的最小 linkage。`tests/test_progress_graph_doc_projection.py` 已通过 3 个 targeted tests，真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已刷新；当前仓库再次回到无 active planning-gate 状态，等待从 `design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md` 中选择下一条 post-release 窄主线。

2026-04-28 再继续新增：用户已按未执行议案视角重新审查候选，并明确恢复此前 `PAUSED` 的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md`；Checklist、Phase Map、checkpoint 与 gate 状态面现已切回 landing dispatch 主线，当前 active slice 收窄为沿 `design_docs/orchestration-bridge-landing-dispatch-integration-slice1-draft.md` 固定 `handoff` / `escalation` / `reviewer_takeover` 到真实 delivery surface 的统一 dispatch contract，当前明确不回到 post-release 候选待选状态，也不扩到 daemon queue / persistence / replay 或更厚的 landing history runtime。

2026-04-28 再继续新增：恢复后的 landing dispatch gate 已完成 Slice 1 contract 定稿，并在 `src/runtime/orchestration/landing_dispatch.py` 中落下最小 dispatch helper / protocol；当前 `handoff`、`escalation`、`review_intake` 三类 payload 已可通过同一 helper 注入 owner surface 并返回统一 success/failure result。`tests/test_runtime_orchestration_landing_dispatch.py` 与 `tests/test_runtime_orchestration_landing_consumers.py` 联合通过（8 passed）；当前 active slice 继续收窄为真实 handoff consumer / review-intake adapter wiring 与 gate-level 联合验证，仍不扩到 daemon queue / persistence / replay 或更厚的 landing history runtime。

2026-04-28 再继续新增：landing dispatch gate 已把 handoff consumer 与 review-intake adapter 接到真实 owner surface：handoff 现在通过 `FileHandoffConsumer` 复用 executor handoff JSON 持久化语义，review_intake 现在通过 `FeedbackAPIReviewIntakeConsumer` 复用现有 `FeedbackAPI.register()` pending review surface；新的 owner-surface wiring 已补进 `tests/test_runtime_orchestration_landing_dispatch.py`，当前与 `tests/test_runtime_orchestration_landing_consumers.py` 联合通过（10 passed）。当前 active slice 继续收窄为更宽的 runtime bridge / orchestration 联合验证与 stop condition 判断，仍不扩到 daemon queue / persistence / replay 或更厚的 landing history runtime。

2026-04-28 再继续新增：landing dispatch gate 的更宽 orchestration 联合验证已通过：`tests/test_runtime_orchestration.py`、`tests/test_runtime_orchestration_adapter.py`、`tests/test_runtime_orchestration_coordinator.py`、`tests/test_runtime_orchestration_landing.py`、`tests/test_runtime_orchestration_landing_consumers.py`、`tests/test_runtime_orchestration_landing_dispatch.py` 共 30 项通过。当前实现与验证面已达到 gate stop condition；下一步更合理的动作不再是继续扩实现，而是执行 gate-close writeback 并准备下一条候选主线。

2026-04-28 再继续新增：`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md` 已完成并关闭；当前已生成 `2026-04-28_1140_orchestration-bridge-landing-dispatch-integration_stage-close`，并将 `CURRENT.md`、Checklist、Phase Map 与 checkpoint 的 handoff footprint 统一到同一 canonical source。landing dispatch 的 follow-up direction analysis 已固定为 `design_docs/orchestration-bridge-landing-dispatch-integration-followup-direction-analysis.md`，当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `thin orchestration bridge / daemon contract-first`，而不是继续在已关闭 gate 内扩到 daemon queue / persistence / replay 或更厚的 landing history runtime。

2026-04-28 再继续新增：用户已从 `design_docs/orchestration-bridge-landing-dispatch-integration-followup-direction-analysis.md` 明确选定 Candidate A `thin orchestration bridge / daemon contract-first`；当前已创建新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md`，并新增 Slice 1 草案 `design_docs/orchestration-bridge-daemon-contract-first-slice1-draft.md`。本轮 scope 先固定 bridge-owned work-item / group-item lifecycle、terminal landing 向上回传，以及 bridge 与 governance kernel / landing dispatch surface 的 ownership matrix；当前明确不进入 full daemon runtime、queue / persistence / replay 实现，也不切回 broader companion prose 或 dogfood backlog。

2026-04-28 再继续新增：`design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md` 已按 docs-only boundary 完成并关闭；当前 Slice 1-3 已把 ownership boundary、group-item projection、work-item roll-up、stop-boundary trigger family 与 next runtime entry 收窄到同一 contract 面。当前已新增 `design_docs/orchestration-bridge-daemon-contract-first-followup-direction-analysis.md`，仓库再次回到无 active planning-gate 状态；默认下一步转向 `contract/runtime alignment over existing bridge surface`，而不是直接跳到 broader daemon queue / persistence runtime。

2026-04-28 再继续新增：用户已从 `design_docs/orchestration-bridge-daemon-contract-first-followup-direction-analysis.md` 选定 Candidate A `contract/runtime alignment over existing bridge surface`；当前已创建新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md`，并新增 Slice 1 草案 `design_docs/orchestration-bridge-contract-runtime-alignment-slice1-draft.md`。本轮 scope 先盘点 `src/runtime/orchestration/models.py`、`rollup.py`、`stop_conditions.py`、`landing.py` 与 Slice 1-3 contract 的对应关系，当前明确不进入 broader daemon queue / persistence / replay runtime。

2026-04-29 新增：当前 `design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md` 已完成 Slice 1 inventory、Slice 2 delivery-signal isolated conformance edit，以及 `tests/test_runtime_orchestration.py` 的 targeted validation（10 passed），因此在内容面已满足 close 条件；但按 `design_docs/tooling/Document-Driven Workflow Standard.md` 的 safe-stop writeback bundle，当前还不能直接切为 `COMPLETED`，因为 current-gate follow-up direction analysis、direction candidates、Phase Map / checkpoint 与 handoff / `CURRENT.md` 仍未同步到 close 后口径。此次 close 规则差点未被精准执行的主要原因也已明确：本 gate 本地 `Stop condition` 只编码 implementation readiness，没有显式复写 safe-stop bundle，而 repo memory `project-state.md` 仍保留“无 active planning gate”的过期状态，不能作为 close judgment 的权威依据。

2026-04-29 再继续新增：`design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md` 的 gate-close writeback bundle 已完成；当前已生成并激活 `2026-04-29_1925_orchestration-bridge-contract-runtime-alignment_stage-close`，并将 `CURRENT.md`、Checklist、Phase Map 与 checkpoint 的 handoff footprint 统一到同一 canonical source。`design_docs/orchestration-bridge-contract-runtime-alignment-followup-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md` 已固定 close 后的下一步入口；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `delivery signal integration hook over existing bridge surface`，而不是继续在已关闭 gate 内扩到 external-resolution landing conformance 或 broader daemon queue / persistence runtime。

2026-04-29 再继续新增：用户已从 `design_docs/orchestration-bridge-contract-runtime-alignment-followup-direction-analysis.md` 选定 Candidate A `delivery signal integration hook over existing bridge surface`；当前已创建新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md`，并新增 Slice 1 草案 `design_docs/orchestration-bridge-delivery-signal-integration-hook-slice1-draft.md`。本轮 scope 先固定 delivery dispatch result 与 `BridgeGroupItem` 回写目标同时可见的最小 runtime entry，默认沿 coordinator / landing boundary 邻侧的 post-dispatch overlay hook 收窄，而不是直接扩大到 external-resolution landing conformance 或 broader daemon queue / persistence runtime。

2026-04-30 新增：`design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md` 已完成 Slice 2/3 contract、最小 live helper `overlay_delivery_dispatch_result(...)` 与 focused validation `tests/test_runtime_orchestration_landing_dispatch.py`（9 passed）；`design_docs/orchestration-bridge-mvp-boundary-draft.md` 现已明确 bridge MVP 的四个 completion signals 全部成立，因此当前 bridge MVP 的技术验收边界已经满足。

2026-04-30 再继续新增：`orchestration-bridge-delivery-signal-integration-hook` 的 formal close writeback bundle 已完成；当前已生成并激活 `2026-04-30_1818_orchestration-bridge-delivery-signal-integration-hook_stage-close`，并将 `CURRENT.md`、Checklist、Phase Map 与 checkpoint 的 handoff footprint 统一到同一 canonical source。`design_docs/direction-candidates-after-phase-35.md` 与 `design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md` 已固定 bridge MVP 之后的默认恢复入口；当前仓库再次回到无 active planning-gate 状态，默认下一步转向 `richer interactive preview over current export surface`，而不是继续在已关闭 gate 内扩大 bridge runtime 或回到 graph source coverage 扩展。

2026-04-30 再继续新增：当前已沿推荐方向进入新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md`；用户交互的第一刀当前被收窄为“现有 HTML artifact / host preview 之上的 graph-local filter、node detail 与 focused reveal”，并明确不在本轮同时重开 `doc_projection` / export schema、preview freshness signaling、handoff-safe-stop projection 或 cluster expand/collapse。

2026-05-03 新增：`design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md` 的 formal close writeback bundle 已完成；当前已生成并激活 `2026-05-03_1210_project-progress-richer-interactive-preview-over-current-export-surface_stage-close`，并将 `CURRENT.md`、Checklist、Phase Map 与 checkpoint 的 handoff footprint 统一到同一 canonical source。`design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md` 已固定 close 后的下一步入口；当前默认更稳的恢复线是 `preview freshness signaling and workflow polishing`，而“大型项目 compound node / expandable roll-up”需求保持在已记录但未激活的后续候选层。当前仓库再次回到无 active planning-gate 状态。

2026-05-03 再继续新增：用户已从 `design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md` 选定 Candidate A `preview freshness signaling and workflow polishing`；当前已创建新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md`，并新增 Slice 1 草案 `design_docs/project-progress-preview-freshness-signaling-and-workflow-polishing-slice1-draft.md`。本轮 scope 先固定 stale hint、dirty badge、refresh-state 与 artifact freshness 可见性，继续沿现有 host preview / artifact refresh workflow 收窄；当前明确不进入 watcher-driven auto refresh、compound node / hierarchical roll-up、handoff / safe-stop projection 或新的 renderer 重写。

2026-05-05 新增：当前 active gate `design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md` 已启动 Slice 2 实装；`vscode-extension/src/views/progressGraphPreview.ts` 现已统一经过最小 host wrapper / chrome 承载 current preview，而不是在 artifact 存在时直接直出 raw `latest.html`。当前 host shell 已接入 artifact mtime、last-loaded time 与 refresh lifecycle，可表达 `fresh` / `stale` / `refreshing` / `failed` / `missing` 五类 freshness state，并保持 raw artifact 仍通过 iframe `srcdoc` 复用原内容；当前最窄 executable check `npm run build` 已通过，后续仍需继续做 stale / failure / missing 行为 spot check，同时保持 no-change boundary 不扩到 watcher、compound node 或 source coverage。

2026-05-05 再继续新增：当前已进一步明确 Candidate A 的承载边界：在 UX 彻底稳定接管前，继续保持“原始 HTML artifact + 宿主 UX shell 并行”模式。当前 `raw latest.html` 仍作为 graph 主内容被原样承载，host wrapper 只并行补 freshness / refresh-state 与操作入口，不把 freshness cue 下压成对原始 HTML 的内部接管。

2026-05-06 新增：`design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md` 已补齐剩余的 `missing` / `stale` / `failed` 行为 spot check，并据此收口为 COMPLETE；当前 freshness/workflow polish 的最小 contract、host-side implementation 与窄验证均已成立。

2026-05-06 再继续新增：当前已创建并激活新的 ACTIVE planning-gate `design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md`，并新增 Slice 1 草案 `design_docs/project-progress-graph-interactive-control-surface-slice1-draft.md`。本轮 scope 先收窄为 read-only control overlay + orchestration compact snapshot contract：优先让 graph 直接看见 `BridgeWorkItem` / `BridgeGroupItem` 的 compact state 与 graph node binding，而不直接进入 direct mutation controls、daemon persistence 或新的 renderer 重写。

2026-05-06 再继续新增：当前 active gate 的 contract-only groundwork 已进一步收口：`design_docs/project-progress-graph-interactive-control-surface-snapshot-schema-draft.md`、`design_docs/project-progress-graph-interactive-control-surface-slice2-projection-helper-contract-draft.md`、`design_docs/project-progress-graph-interactive-control-surface-slice2-graph-binding-contract-draft.md` 与 `design_docs/project-progress-graph-interactive-control-surface-slice3-overlay-consumer-surface-draft.md` 已把 graph-facing snapshot schema、snapshot producer owner、raw target + scoped key 的 binding contract，以及 read-only overlay consumer surface 依次写清。当前判断中，继续推进时最合适的新信息已经不再是补文档，而是进入最小代码骨架实现。

2026-05-06 再继续新增：当前最小代码骨架实现已进一步落地：`tools/progress_graph/control_snapshot.py` / `tools/progress_graph/control_binding.py` 已提供 control snapshot writer 与 binding normalization 的稳定入口，`vscode-extension/src/views/progressGraphArtifacts.ts` 已把 `control-snapshot.json` 接入真实 regenerate pipeline，`vscode-extension/src/views/progressGraphPreview.ts` 已能消费该 artifact；随后 `write_control_snapshot(...)` 的默认 source 又已接到当前 `.codex/checkpoints/latest.md` 与 active planning-gate，使 workspace 中的 `control-snapshot.json` 不再停留在合法空壳，而是 active gate + open checkpoint todo 的最小非空 bridge 观察面。此后又把宿主 HTML/control overlay 组装抽成纯 helper `vscode-extension/src/views/progressGraphPreviewHtml.ts`，并通过 `vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 的 focused Node spot check 固定了非空 snapshot overlay 与 failed fallback 两条宿主输出路径；`npm run build` 也已再次通过。当前下一窄切口收束为：继续补最小 source coverage，而不是继续停留在静态或空数据占位。

2026-05-06 再继续新增：当前最小 source coverage 已完成第一条真实 persisted owner surface 接线：`tools/progress_graph/control_snapshot.py` 现在会在 fallback 路径里直接投影 `.codex/handoffs/CURRENT.md` 的 current handoff mirror，而不是继续只依赖 checkpoint/planning-gate。新的 handoff row 以 `completed` work item + `handoff/delivered` group item 进入 `control-snapshot.json`，并通过 unbound runtime panel 暴露给宿主 control overlay；`tests/test_progress_graph_control_snapshot.py` 现通过（8 passed），实际 workspace 的 `.codex/progress-graph/control-snapshot.json` 也已刷新到包含 current handoff persisted source 的状态。当前若继续推进 source coverage，应只再检查 escalation file notifier 是否真的形成可消费 artifact，review_intake 仍保持 in-memory，不应就地扩成 direct mutation controls。

2026-05-06 再继续新增：上述 escalation 调研现已完成，并形成明确边界：当前仓库里并不存在真实 escalation persisted surface。`src/pep/notifiers/file_notifier.py` 只是可选 utility，当前 `src/` 中没有默认实例化、没有默认 output path，workspace 里也没有任何 escalation JSON artifact；`review_intake` 继续只落到 `FeedbackAPI` 的 in-memory store。因此，当前 active gate 的 source coverage 已经收口为“handoff 是唯一新增且诚实的 persisted owner surface”，而 escalation 如需继续，必须先进入独立的 paused gate `design_docs/stages/planning-gate/2026-05-06-escalation-notification-persisted-surface-contract.md`，而不是在现有 control-snapshot slice 里顺手发明新的 file sink contract。

2026-05-07 新增：当前 graph 主线已按用户采纳发生一次受控换线：`design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md` 现暂停在 stable baseline / read-only groundwork 的位置；随后 `design_docs/stages/planning-gate/2026-05-07-parallel-v2-graph-renderer-and-library-selection.md` 已完成 docs-first 收口，并把更窄的执行入口固定为 `design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md`。这意味着当前 active slice 已从“继续补 control snapshot source coverage”切到“先验证更接近 Obsidian graph view 的并行 V2 展示层”。

2026-05-07 再继续新增：`design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md` 已从“代码已接入、待真实宿主验收”推进到“真实宿主验收完成、继续 read-only 图面微调”。`vscode-extension/src/views/progressGraphPreview.ts` 已补强选图逻辑：优先选择 edgeful graph，并在同优先级下优先更晚的 `recorded_at`，避免零边图或旧 snapshot 抢占；`vscode-extension/src/webviews/progressGraphV2PoC.ts` 已修复 Sigma reducer replace 语义导致的 `x/y` 丢失问题，并继续把 runtime-bound / milestone / blocked nodes 作为 idle label anchors，补上 click-to-focus camera follow，并把初始布点改为 semantic-band seed + 更松的 ForceAtlas2 cloud tuning；`tools/progress_graph/doc_projection.py` 也已修复 `project-checklist-current` 的 source reference edge 位置错误，避免最新 checklist 快照出现零边或重复 reference edge。随后又在 `vscode-extension/src/views/progressGraphPreviewHtml.ts` + `vscode-extension/src/webviews/progressGraphV2PoC.ts` 内补入最小 Obsidian-ish Graph Config shell：外观滑杆现在会驱动 label density / label size / node scale / edge scale，力度滑杆会映射到 ForceAtlas2 gravity / scalingRatio / edgeWeightInfluence 与整体 spread，颜色组已根据 Obsidian 官方 Graph/Search 文档与公开行为线索收紧为“复用 Search 核心语法 + 列表顺序首个命中优先”的模型，并新增顺序调整控件；同时明确当前 payload 仍不承载真实文件全文与任意 property surface，因此 `content:` / property 仍只做现有节点数据面的近似映射。当前 focused validation 继续成立：`npm run build` 通过、自定义 in-memory helper validation 与 query semantics validation 通过、关键入口 diagnostics clean，且真实 VS Code webview 内的用户验证已确认边可见、`x/y` 报错消失。当前 gate 仍保持 ACTIVE，但理由已从“待做宿主 spot check”切换为“继续只在 read-only graph-view PoC 内微调图感与配置手感，不提前进入 control panel 或 formal close”。

2026-05-09 新增：当前 graph 主线已进一步从旧 Sigma residual path 收口到新的 ACTIVE gate `design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md`。`vscode-extension/src/webviews/progressGraphV2G6.ts` 当前已完成一轮真实宿主驱动的交互稳定化：hover / selected 高亮不再依赖浏览器侧手写 redraw，而是改由 G6 element state 直接接管；本节点、相邻点、相接边与其余节点已形成稳定的分层高亮语义，selected 相对 hover 的确认感也已单独拉开，节点标签已切到深色文案。此前 hover / click / node-scale 相关 shrink 回归也已定位并移除。当前 focused validation 继续成立：`npm run build` 通过、touched files diagnostics clean、真实 VS Code 宿主 spot check 已确认当前图面交互闭环成立。当前 active slice 后续不应回到 Sigma/Sigma-like 双链路修补，而应只在 G6 路线下继续推进下一项增量能力，例如颜色组迁移或更细的视觉调校。

2026-05-27 新增：用户已明确把关系图谱实现源切换到外部工作区 `E:\workspace\tool develop\graph engine\knowledge-graph-engine`，并要求完全放弃当前 G6 相关成果。`design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md` 现已降级为 `SUPERSEDED / ARCHIVED REFERENCE`，只保留已指定功能与效果经验；新的 ACTIVE gate 为 `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`。当前第一刀只做 VS Code progress graph preview 对外部 `GraphModel` / `SimulationClient` / `Canvas2DRenderer` 的接入、G6 构建链移除，以及外部组件接口缺口文档化。

2026-06-10 新增：side planning-gate `design_docs/stages/planning-gate/2026-06-09-python-reference-dependency-baseline-generator-adapter.md` 已完成并切为 `COMPLETED`。当前 `tools/dependency_graph/reference_adapter.py` 提供 create / refresh / generate / validate / repair / rollback 生命周期命令；Python 路径采用 AST 符号骨架 + Pylance usage fixture 优先关系增强，JavaScript 路径提供 module / class / function / import / require / simple extends 的 conservative support；`docs/dependency-baseline-maintenance-guide.md` 与 `.codex/prompts/doc-loop/06-dependency-baseline-maintenance.md` 已覆盖创建、维护、修正、回退、扩张和 write-back 指导。验证结果：相关 focused suite `146 passed`，runtime wheel verification 已确认包含 `tools/dependency_graph/reference_adapter.py`，instance pack / bootstrap validators 与 pack verify 均通过。该支线不改变当前 Knowledge Graph Engine 主 active gate。

2026-06-17 新增：agent orchestration / scheduler 主线已完成 `design_docs/stages/planning-gate/2026-06-17-host-authorized-scheduler-runner-adapter.md` 并切为 `COMPLETED`。当前 `src/runtime/orchestration/scheduler_host_runner.py` 提供 `HostSchedulerRunRequest`、`HostSchedulerRunResult` 与 `run_host_authorized_scheduler_once()`；`tools/progress_graph/scheduler_projection.py` 提供 `run_host_authorized_scheduler_once_and_refresh_projection()`，可在不突变 agent-owned Local Work Trajectory 的前提下刷新 scheduler-derived trajectory projection。focused validation 结果为 `280 passed, 1 skipped`。新的 ACTIVE gate 已切换为 `design_docs/stages/planning-gate/2026-06-17-controlled-host-runtime-dogfood-harness.md`，下一步收窄为 evidence JSON contract、fake runtime dogfood harness、mock-Qoder host-authorized harness 与维护提示词。

2026-06-17 再继续新增：`design_docs/stages/planning-gate/2026-06-17-controlled-host-runtime-dogfood-harness.md` 已正式切为 `COMPLETED`。本轮新增 `HostSchedulerRunEvidence` / `write_host_scheduler_run_evidence()` 与 `run_host_runtime_dogfood_harness()`，使 fake runtime 与 mock-Qoder host-authorized scheduler pass 均可产出同形 evidence JSON、刷新 scheduler-derived trajectory projection，并保持 MCP fake-only、scheduler state authority、scheduler projection read-only 与 agent-owned Local Work Trajectory 的边界。close-review evidence 位于 `review/controlled-host-runtime-dogfood-harness-2026-06-17.md`；后续方向分析位于 `design_docs/controlled-host-runtime-dogfood-harness-followup-direction-analysis.md`，当前推荐下一候选为 `Controlled Real Qoder Wrapper Spike`。focused validation 结果为 `284 passed, 1 skipped`。

2026-06-17 再继续新增：当前已沿上述推荐创建并激活 `design_docs/stages/planning-gate/2026-06-17-controlled-real-qoder-wrapper-spike.md`。本 gate 只允许在 host-owned surface 中实现 real Qoder SDK wrapper behind `QoderQueryClient`，并把凭据/授权失败、SDK 缺失、权限回调/拒绝、fail-closed 与 rollback 行为设为 acceptance criteria；MCP `schedulerRunOnceAndProject` 继续保持 fake-only，当前不进入 daemon、UI evidence consumer、真实 sandbox 或多 agent 调度扩张。

2026-06-17 再继续新增：`design_docs/stages/planning-gate/2026-06-17-controlled-real-qoder-wrapper-spike.md` 已推进到 `READY-FOR-CLOSE-REVIEW`。当前已落地 host-owned optional Python wrapper `QoderSDKQueryClient` / `QoderSDKQueryClientConfig`，动态导入 `qoder_agent_sdk`，并通过 `validate_host_ready()` 在 `run_host_runtime_dogfood_harness()` 运行前检查 SDK/auth readiness；缺 SDK、缺 auth、非法 stream、权限回调默认拒绝、surface-without-approval、token redaction 与 host dogfood auth-failure fail-closed 均已有 focused tests。MCP `schedulerRunOnceAndProject` 仍为 fake-only。close-review evidence 位于 `review/controlled-real-qoder-wrapper-spike-2026-06-17.md`；focused validation 结果为 `272 passed, 1 skipped`。

2026-06-17 再继续新增：`design_docs/stages/planning-gate/2026-06-17-controlled-real-qoder-wrapper-spike.md` 已正式切为 `COMPLETED`。本轮 close 后 follow-up analysis 位于 `design_docs/controlled-real-qoder-wrapper-spike-followup-direction-analysis.md`，当前推荐并已激活下一条 gate `design_docs/stages/planning-gate/2026-06-17-host-owned-qoder-smoke-runner-helper.md`。第一刀已落 `tools/progress_graph/qoder_smoke.py`：helper 可初始化最小 Qoder smoke scheduler snapshot、构造 host invocation / qoder permission grant、复用 `QoderSDKQueryClient` 或 injected `QoderQueryClient`，并委托 `run_host_runtime_dogfood_harness()` 产出同形 evidence 与 scheduler-derived trajectory projection；MCP real-provider exposure、daemon、UI evidence consumer、real sandbox 仍不进入当前 slice。当前 helper gate 已推进到 `READY-FOR-CLOSE-REVIEW`，review evidence 位于 `review/host-owned-qoder-smoke-runner-helper-2026-06-17.md`；focused validation 结果为 `295 passed, 1 skipped`。

2026-06-17 再继续新增：`design_docs/stages/planning-gate/2026-06-17-host-owned-qoder-smoke-runner-helper.md` 已正式切为 `COMPLETED`。本轮新增 follow-up analysis `design_docs/host-owned-qoder-smoke-runner-helper-followup-direction-analysis.md`，并激活新的 ACTIVE gate `design_docs/stages/planning-gate/2026-06-17-credentialed-live-qoder-smoke.md`。下一步只做本机 host readiness 检查与一条 bounded live Qoder smoke（若 SDK/auth 可用），若 SDK/auth 不可用则记录 credential-safe 的 readiness-negative evidence；仍不进入 MCP real-provider exposure、daemon、UI evidence consumer、real sandbox 或多 agent 调度策略。

2026-06-17 再继续新增：`design_docs/stages/planning-gate/2026-06-17-credentialed-live-qoder-smoke.md` 已推进到 `READY-FOR-CLOSE-REVIEW`。本机 credential-safe readiness 检查显示 `qoder_agent_sdk` 不可 import，`QODER_PERSONAL_ACCESS_TOKEN` 不存在，`QoderSDKQueryClient.validate_host_ready()` 以 `authentication_failed / MissingEnvironmentVariable` fail-closed；未打印或持久化 token 值，也未生成 Qoder smoke snapshot、evidence JSON 或 scheduler projection。当前证据位于 `review/credentialed-live-qoder-smoke-2026-06-17.md`；这是 readiness-negative close，而不是 live success。

2026-06-18 新增：`design_docs/stages/planning-gate/2026-06-17-credentialed-live-qoder-smoke.md` 已正式切为 `COMPLETED`，并完成 `design_docs/stages/planning-gate/2026-06-18-host-evidence-consumer.md`。当前新增的 host evidence consumer 是只读产品化投影层：`HostSchedulerRunEvidenceSummary` / `read_host_scheduler_run_evidence_summary()` / `read_host_scheduler_run_evidence_summaries()` / `tools.progress_graph.read_host_evidence_bundle()` 可读取已有 `host_scheduler_run_evidence` JSON，并输出不含嵌入式 `host_result` 的 compact summary；它不执行 provider、不初始化/刷新 scheduler、不突变 Local Work Trajectory，也不会为 readiness-negative review doc 合成 evidence JSON。review evidence 位于 `review/host-evidence-consumer-2026-06-18.md`，follow-up analysis 位于 `design_docs/host-evidence-consumer-followup-direction-analysis.md`；focused validation 结果为 `221 passed, 1 skipped`。当前推荐下一步为只读 MCP Resource Exposure For Host Evidence，而不是直接进入 UI dirty branch、live credential provisioning 或 scheduler daemon。

2026-06-18 再继续新增：`design_docs/stages/planning-gate/2026-06-18-host-evidence-mcp-resource-exposure.md` 已完成。当前 MCP resource surface 新增只读资源 `dbc://host-evidence/bundle`，由 `GovernanceTools.list_resources()` 暴露、`GovernanceTools.read_resource()` 读取，并复用 `tools.progress_graph.read_host_evidence_bundle()` 输出 compact host evidence JSON。该资源不是 execution tool，不会触发 fake/real provider，不会初始化 scheduler state，不会刷新 scheduler projection，也不会突变 Local Work Trajectory；缺 evidence 目录时返回空 bundle。review evidence 位于 `review/host-evidence-mcp-resource-exposure-2026-06-18.md`；focused validation 结果为 `26 passed`。

2026-06-18 继续新增：`design_docs/stages/planning-gate/2026-06-18-cli-resource-inspection-for-host-evidence.md` 已完成。当前 CLI 入口新增 `doc-based-coding resources list` 与 `doc-based-coding resources read <uri>`，复用 `GovernanceTools` 的资源 list/read surface，使 `dbc://host-evidence/bundle` 能在无 MCP host 的情况下被 operator 或脚本检查。该入口仍是只读检查面，不添加 MCP tool、不执行 scheduler/Qoder、不改变 resource contract；missing resource 会返回非零 exit 与明确错误。review evidence 位于 `review/cli-resource-inspection-for-host-evidence-2026-06-18.md`，follow-up analysis 位于 `design_docs/cli-resource-inspection-for-host-evidence-followup-direction-analysis.md`；focused validation 结果为 `4 passed, 7 deselected`，CLI list/read/missing 手测通过。

2026-06-18 继续新增：`design_docs/stages/planning-gate/2026-06-18-resource-error-isolation-for-host-evidence.md` 已完成。当前 `HostEvidenceBundle` 增加 `errors[]` / `error_count`，resource/CLI 面对 malformed evidence JSON 时会把坏文件隔离成 compact error summary，而不是让整个 bundle 读取失败；有效 evidence 仍保留在 `summaries[]`，严格 runtime reader 仍保持严格抛错。review evidence 位于 `review/resource-error-isolation-for-host-evidence-2026-06-18.md`；focused validation 结果为 `204 passed, 1 skipped`，外部临时 workspace CLI 坏 evidence 手测通过。

2026-06-18 继续新增：`design_docs/stages/planning-gate/2026-06-18-host-evidence-presentation-contract.md` 已完成。当前 `HostEvidenceBundle` 之上新增纯数据 presentation contract：`HostEvidencePresentation` / cards / error rows 可把 evidence summaries 与 isolated read errors 归一为 UI/operator-facing view，并覆盖 empty / completed / permission-review / failed / partial / degraded 状态推导；现有 MCP resource 与 CLI bundle payload 保持不变，且本轮未进入 VS Code UI binding、新 MCP execution tool、新 resource URI、scheduler daemon、Qoder 凭据或 SDK 安装。review evidence 位于 `review/host-evidence-presentation-contract-2026-06-18.md`；focused validation 结果为 `231 passed, 1 skipped`。

2026-06-18 继续新增：`design_docs/stages/planning-gate/2026-06-18-host-evidence-presentation-resource-exposure.md` 已完成。当前新增只读资源 `dbc://host-evidence/presentation`，由 `GovernanceTools.list_resources()` 暴露、`GovernanceTools.read_resource()` 读取，并复用 `read_host_evidence_bundle()` 与 `build_host_evidence_presentation()` 输出 host/UI/operator-facing presentation JSON；现有 `doc-based-coding resources read` 可直接检查该 URI，且 bundle resource payload 保持不变。本轮未进入 VS Code UI binding、provider execution、scheduler daemon、Qoder 凭据或 SDK 安装。review evidence 位于 `review/host-evidence-presentation-resource-exposure-2026-06-18.md`；focused validation 结果为 `209 passed, 1 skipped`。

2026-06-18 继续新增：`design_docs/stages/planning-gate/2026-06-18-credentialed-live-qoder-rerun-over-presentation-resources.md` 已完成。当前本机 host readiness 仍为 readiness-negative：`qoder_agent_sdk` 不可 import，`QODER_PERSONAL_ACCESS_TOKEN` 不存在，`QoderSDKQueryClient.validate_host_ready()` 以 `authentication_failed / MissingEnvironmentVariable` fail-closed；本轮新增的验证点是通过现有 CLI resource path 读取 `dbc://host-evidence/bundle` 与 `dbc://host-evidence/presentation`，确认 bundle 诚实返回 `evidence_count=0 / error_count=0`，presentation 诚实返回 `status=empty`，且未创建 Qoder smoke snapshot、host evidence JSON 或 scheduler-derived trajectory projection。review evidence 位于 `review/credentialed-live-qoder-rerun-over-presentation-resources-2026-06-18.md`；focused validation 结果为 `209 passed, 1 skipped`。下一步推荐先做 `design_docs/credentialed-live-qoder-rerun-over-presentation-resources-followup-direction-analysis.md` 中的 Qoder host provisioning check guide，而不是在 UI dirty branch 或 scheduler daemon 上扩 scope。

2026-06-18 继续新增：`design_docs/stages/planning-gate/2026-06-18-qoder-host-provisioning-check-guide.md` 已完成。当前新增 `QoderSDKHostReadinessReport`、`QoderSDKQueryClient.host_readiness_report()` 与 CLI `doc-based-coding qoder readiness`，用于在不执行 provider、不写 evidence、不刷新 scheduler projection、不泄露 token 的前提下检查 Qoder host readiness；`docs/qoder-host-provisioning-check-guide.md` 已固定 SDK 安装期望、`env` / `qodercli` auth 模式、JSON 输出合同和 write-back 安全规则。当前本机仍未准备好 live Qoder：默认 `env` 模式报告 `sdk_importable=false / token_present=false / authentication_failed`，`qodercli` 模式报告 `sdk_unavailable`。review evidence 位于 `review/qoder-host-provisioning-check-guide-2026-06-18.md`；focused validation 结果为 `155 passed`。下一步若 host 环境被外部 provision，可回到 credentialed live Qoder smoke；若不 provision，则更适合转向 Host Evidence Preview UI Binding 或 presentation timestamp polish。

2026-06-18 继续新增：`design_docs/stages/planning-gate/2026-06-18-exchange-artifact-durable-store-foundation.md` 已完成。当前从 Qoder host readiness 之后的方向分析中重新锚定编排层底座：`ExchangeArtifact` 现在除 `InMemoryArtifactVersionStore` 外已有 `JsonArtifactVersionStore`，并新增 `exchange_artifact_to_json_dict()` / `exchange_artifact_from_json_dict()` 覆盖 text / structured / ref / artifact_delta / contract / evidence / relation / storage_manifest / log 九类 payload part。本轮保持 scheduler snapshot 仍为调度权威，exchange artifact store 只作为本地持久化协调产品版本库，不进入 UI、远程 registry、数据库或真实 Qoder。review evidence 位于 `review/exchange-artifact-durable-store-foundation-2026-06-18.md`；focused validation 结果为 `238 passed`。

2026-06-19 新增：`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-store-inspection-and-admission-prep.md` 已完成。当前在 durable `ExchangeArtifact` store 之上新增只读 inspection/admission-prep 面：`ExchangeArtifactInspectionBundle` / `ExchangeArtifactVersionSummary` / `ExchangeArtifactAdmissionCandidate` 可读取 `.codex/orchestration/exchange-artifacts.json`，汇总精确 artifact versions、latest flags、scope / producer / lifecycle、payload part types，并识别 `scheduler_task_submission` / `scheduler_task_batch_submission` 候选；MCP/CLI resource `dbc://exchange-artifacts/bundle` 已可读取该 bundle。该面只为后续 admission 做准备，不提交任务、不改变 scheduler snapshot 权威、不刷新 scheduler projection、不突变 Local Work Trajectory。review evidence 位于 `review/exchange-artifact-store-inspection-and-admission-prep-2026-06-19.md`；focused validation 结果为 `243 passed`（pytest 成功后 Windows 进程尾声打印 access-violation 栈；最小 import 与 CLI resource smoke 正常，已记录为残余 Windows/Python test-process 信号）。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-exact-version-scheduler-admission.md` 已完成。当前 `ExchangeArtifact` store inspection 之后的第一条 admission helper 已落地：`admit_exchange_artifact_version_to_scheduler()` 从 `JsonArtifactVersionStore` 读取指定 `(artifact_id, version)`，要求其恰好包含一个 `scheduler_task_submission` 或 `scheduler_task_batch_submission` payload，然后通过既有 scheduler submission persistence path 写入 scheduler snapshot 与 event log。该 helper 只做 scheduler task-contract admission，不运行 provider、不刷新 scheduler projection、不标记 artifact consumed、不突变 Local Work Trajectory，也不新增 stored-artifact MCP 写工具；review evidence 位于 `review/exchange-artifact-exact-version-scheduler-admission-2026-06-19.md`；focused validation 结果为 `249 passed`（pytest 成功后仍出现既有 Windows/Python access-violation printout，断言与 exit code 成功）。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-operator-admission-cli.md` 已完成。当前在 exact-version admission helper 之上新增 CLI-first operator surface：`doc-based-coding scheduler admit-exchange-artifact`，可从默认 `.codex/orchestration/exchange-artifacts.json` 或显式 `--artifact-store-path` 读取指定 artifact/version，并写入显式指定的 scheduler snapshot / event log。该命令输出 `ok=true`、submitted task IDs、submission event IDs 与 authority clues；仍不运行 provider、不刷新 scheduler projection、不标记 artifact consumed、不新增 stored-artifact MCP 写工具、不突变 Local Work Trajectory。review evidence 位于 `review/exchange-artifact-operator-admission-cli-2026-06-19.md`；focused validation 结果为 `tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py` 261 passed。

2026-06-19 继续新增：已完成 `design_docs/exchange-artifact-operator-admission-followup-direction-analysis.md`。该方向分析比较了四条后续路线：Operator Admission Workflow Polish、Stored-Artifact MCP Admission Tool、Scheduler Daemon / Durable Queue、Host Evidence UI Binding。当前推荐下一条窄 gate 为 `ExchangeArtifact Operator Admission Workflow Polish`：先把 inspect -> admit -> readback/projection guidance 的 operator workflow 做成更容易验证的闭环；stored-artifact MCP 写工具、scheduler daemon、UI binding 与 artifact lifecycle consumed ledger 均延后为独立 gate。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-operator-admission-workflow-polish.md` 已完成。当前 CLI operator workflow 已形成无 MCP host 的四步闭环：`resources read dbc://exchange-artifacts/bundle` 检查候选，`scheduler admit-exchange-artifact` 写入 scheduler snapshot/event-log，`scheduler inspect-state` 只读验证 scheduler state/event clues，`scheduler project` 显式刷新 scheduler-derived trajectory projection。该闭环仍不运行 provider、不新增 stored-artifact MCP 写工具、不标记 exchange artifact consumed、不进入 daemon/UI、不突变 Local Work Trajectory；review evidence 位于 `review/exchange-artifact-operator-admission-workflow-polish-2026-06-19.md`；focused validation 结果为 `267 passed`。

2026-06-19 继续新增：已完成 `design_docs/exchange-artifact-admission-after-workflow-polish-direction-analysis.md`。该方向分析在 operator workflow polish 之后重新比较 Admission Ledger、Stored-Artifact MCP Admission Tool、Scheduler Daemon / Durable Queue、Host Evidence / Scheduler Admission UI Binding 与 Provider Execution / Qoder Runtime Recheck；当前推荐下一条窄 gate 为 `Exchange Artifact Admission Ledger`，先固化 admission/consumption/duplicate audit 语义，再考虑 agent-callable MCP 写工具或 daemon。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-admission-ledger.md` 已完成。当前 exact-version ExchangeArtifact scheduler admission 已新增 durable local admission ledger，默认路径为 `.codex/orchestration/exchange-artifact-admissions.json`；CLI `scheduler admit-exchange-artifact` 会在成功 admission 后写入 `admitted` 记录，在重复 exact artifact/version admission 且未传 `--allow-duplicate-admission` 时于 scheduler mutation 前拒绝并写入 `rejected_duplicate`，并保持 `--allow-duplicate-admission` 与 scheduler `--replace-existing` 语义分离；新增 `scheduler inspect-admissions` 只读检查 ledger 状态。review evidence 位于 `review/exchange-artifact-admission-ledger-2026-06-19.md`；focused validation 结果为 `274 passed`。后续方向分析 `design_docs/exchange-artifact-admission-ledger-followup-direction-analysis.md` 推荐下一条窄 gate 为 `Stored-Artifact MCP Admission Tool`，但 provider execution、daemon、UI binding 与 exchange-store consumed marking 仍不进入当前完成面。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-stored-artifact-mcp-admission-tool.md` 已完成。当前 stored-artifact scheduler admission 已新增 MCP tool `admitExchangeArtifact`，由 `GovernanceTools.admit_exchange_artifact()` 接入并复用 `admit_exchange_artifact_version_with_ledger()`，使 MCP 与 CLI 共用 durable admission ledger、duplicate exact artifact/version rejection、explicit duplicate override 和 scheduler submission persistence path。该 MCP tool 需要 exact `artifactId` / `version` 与显式 scheduler snapshot/event-log paths，返回 snake_case authority clues、ledger record id、submitted task ids、dependency ids 与 submission event ids；它不运行 provider、不自动刷新 scheduler projection、不标记 exchange artifact consumed、不突变 Local Work Trajectory。review evidence 位于 `review/stored-artifact-mcp-admission-tool-2026-06-19.md`；tracked focused validation 结果为 `198 passed`，本地 ignored MCP harness 扩展验证 `279 passed`。后续方向分析 `design_docs/stored-artifact-mcp-admission-tool-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Exchange Artifact Lifecycle Consumed Projection`，先把 admission ledger 状态只读投影回 exchange artifact inspection，而不是直接进入 daemon、UI binding 或 provider execution。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-admission-state-projection.md` 已完成。当前 `dbc://exchange-artifacts/bundle` 已把 durable admission ledger 中的 exact `(artifact_id, version)` 记录投影为每个 stored artifact version 的 `admission_state`，包含 status/counts/latest-record clues 以及 admitted/rejected/failed record ids；缺 ledger 时为 `not_admitted`，malformed ledger 被隔离为 bundle error 且不隐藏有效 summaries。该面只读，不突变 exchange store lifecycle、不标记 consumed、不运行 provider、不刷新 scheduler projection、不突变 Local Work Trajectory。review evidence 位于 `review/exchange-artifact-admission-state-projection-2026-06-19.md`；tracked focused validation 结果为 `201 passed`。后续方向分析 `design_docs/exchange-artifact-admission-state-projection-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Scheduler Daemon / Durable Queue Readiness`，因为 admission inspect/admit/audit/projected-readback 链已经闭合，下一步更适合转向 bounded scheduler advancement contract。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-daemon-durable-queue-readiness.md` 已完成。当前 scheduler 已新增 daemon-ready one-tick contract：`SchedulerDaemonTickRequest` / `SchedulerDaemonTickResult` / `SchedulerDaemonQueueSummary` / `run_scheduler_daemon_tick()`，并通过 CLI `doc-based-coding scheduler tick` 暴露 fake-runtime-only bounded advancement；tick 复用现有 `run_persisted_scheduler_once()`、scheduler snapshot/event-log persistence 与 `SchedulerRunPolicy`，返回 queue summary、run_count、stop_reason、scheduler_event_count 与 authority_split。该切片不启动长驻 daemon、不自动刷新 scheduler projection、不运行真实 provider、不突变 ExchangeArtifact/admission ledger、不突变 Local Work Trajectory。review evidence 位于 `review/scheduler-daemon-durable-queue-readiness-2026-06-19.md`；tracked focused validation 结果为 `207 passed`。后续方向分析 `design_docs/scheduler-daemon-durable-queue-readiness-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Scheduler Durable Daemon Loop Policy`，把 one-tick 合同提升为可恢复的 repeated bounded loop stop policy。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-durable-daemon-loop-policy.md` 已完成。当前 scheduler 已新增 bounded repeated daemon loop policy：`SchedulerDaemonLoopStopPolicy` / `SchedulerDaemonLoopRequest` / `SchedulerDaemonLoopIteration` / `SchedulerDaemonLoopResult` / `run_scheduler_daemon_loop()`，并通过 CLI `doc-based-coding scheduler daemon-loop` 暴露 fake-runtime-only repeated advancement；loop 复用 `run_scheduler_daemon_tick()`，支持 max-tick、no-ready、blocked-task、runtime-failure-limit 等 stop policy，返回 tick_count、total_run_count、iterations、final_queue_summary、scheduler_event_count 与 authority_split。该切片不启动后台 daemon service、不自动刷新 scheduler projection、不运行真实 provider、不突变 ExchangeArtifact/admission ledger、不突变 Local Work Trajectory。review evidence 位于 `review/scheduler-durable-daemon-loop-policy-2026-06-19.md`；tracked focused validation 结果为 `214 passed`。后续方向分析 `design_docs/scheduler-durable-daemon-loop-policy-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Scheduler Loop Host Evidence Binding`，先给 loop result 建立 durable evidence 产品，再进入 UI 或 host-injected runtime。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-loop-host-evidence-binding.md` 已完成。当前 scheduler loop 已新增 durable evidence 产品：`SchedulerLoopEvidence` / `SchedulerLoopEvidenceSummary` / `SchedulerLoopEvidenceWriteResult` / `build_scheduler_loop_evidence()` / `write_scheduler_loop_evidence()` / `read_scheduler_loop_evidence_summary()` / `default_scheduler_loop_evidence_path()`；CLI `doc-based-coding scheduler daemon-loop` 新增显式 `--evidence-id` / `--evidence-path` 写入 `.codex/scheduler/evidence/<safe-id>.json`，既有 `dbc://host-evidence/bundle` / `dbc://host-evidence/presentation` 可只读识别 `host_scheduler_run_evidence` 与 `scheduler_loop_evidence` 混合目录。该切片不新增 MCP execution tool、不运行真实 provider、不自动刷新 scheduler projection、不突变 ExchangeArtifact/admission ledger、不从 scheduler code 突变 Local Work Trajectory。review evidence 位于 `review/scheduler-loop-host-evidence-binding-2026-06-19.md`；tracked focused validation 结果为 `278 passed, 1 skipped`。后续方向分析 `design_docs/scheduler-loop-host-evidence-binding-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Host-Injected Runtime Daemon Loop`，先在 host-owned Python injection seam 验证非 CLI/MCP 的 runtime authority。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-host-injected-scheduler-daemon-loop.md` 已完成。当前 scheduler loop 已新增 host-owned Python injection seam：`HostSchedulerDaemonLoopRequest` / `HostSchedulerDaemonLoopResult` / `run_host_authorized_scheduler_daemon_loop()`；该 helper 复用 `RuntimeRegistryWiringConfig`、`build_runtime_registry_from_config()` 与 `run_scheduler_daemon_loop()`，可由 host 注入 fake 或 mock-Qoder runtime registry，并在显式 `evidence_id` 下写入 `scheduler_loop_evidence`。非 fake provider 仍要求 host-authorized surface、permission grant 与 injected client；CLI/MCP daemon-loop 仍 fake-only。该切片不运行 live provider、不启动后台 daemon service、不自动刷新 scheduler projection、不突变 ExchangeArtifact/admission ledger、不从 scheduler code 突变 Local Work Trajectory。review evidence 位于 `review/host-injected-scheduler-daemon-loop-2026-06-19.md`；tracked focused validation 结果为 `283 passed, 1 skipped`。后续方向分析 `design_docs/host-injected-scheduler-daemon-loop-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Host Loop Projection Workflow Polish`，把 host loop execution、evidence 与 projection readback 组合成显式 host workflow。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-host-loop-projection-workflow-polish.md` 已完成。当前 host workflow 已新增 `HostSchedulerDaemonLoopProjectionRefreshResult` / `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()`，在 `tools.progress_graph` 层组合 host-injected scheduler daemon loop、optional `scheduler_loop_evidence` 写入、scheduler-derived trajectory projection refresh 与 compact readback；结果返回 `scheduler_projection_path`、`projection_summary`，并显式报告 `scheduler_projection_refreshed=true` / `local_work_trajectory_mutated=false`。该切片不新增 CLI/MCP real-provider surface、不运行 live provider、不启动后台 daemon、不突变 ExchangeArtifact/admission ledger、不从 scheduler code 突变 Local Work Trajectory。review evidence 位于 `review/host-loop-projection-workflow-polish-2026-06-19.md`；tracked focused validation 结果为 `285 passed, 1 skipped`。后续方向分析 `design_docs/host-loop-projection-workflow-polish-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Scheduler Loop Evidence Presentation Polish`，先改善 read-only evidence presentation，再进入 UI binding 或 live provider smoke。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-loop-evidence-presentation-polish.md` 已完成。当前只读 `dbc://host-evidence/presentation` 已能把 `scheduler_loop_evidence` 呈现为更适合 operator/UI 消费的 card：包含 runtime provider、host surface、host invocation id、tick/run/event counts、final queue counts，以及 evidence metadata 或 authority split 中可用的 scheduler projection path/role/refreshed state 与 Local Work Trajectory mutation clue。该切片保持 presentation-only：不改 evidence schema、不执行 provider、不刷新 scheduler projection、不突变 scheduler state / ExchangeArtifact / admission ledger / Local Work Trajectory、不绑定 UI、不启动 background daemon。review evidence 位于 `review/scheduler-loop-evidence-presentation-polish-2026-06-19.md`；tracked focused validation 结果为 `287 passed, 1 skipped`。后续方向分析 `design_docs/scheduler-loop-evidence-presentation-polish-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Host Loop Workflow Evidence Metadata`，把 composed host workflow 已知的 projection path/summary compact clues 写入 evidence metadata，供现有 presentation 面稳定读取。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-host-loop-workflow-evidence-metadata.md` 已完成。当前 composed host loop projection workflow 会在 projection refresh 后 enrich 其刚写入的 `scheduler_loop_evidence` metadata，使 durable evidence 携带 `workflow_surface="host-loop-projection-workflow"`、scheduler projection path/role/refreshed state 与 compact projection summary；`dbc://host-evidence/presentation` 可优先使用这些 workflow metadata 展示 projection refreshed state。该切片保持后端 readback 衔接：不改 evidence schema、不新增 provider execution/real-provider CLI/MCP surface、不绑定 UI、不启动 background daemon、不突变 ExchangeArtifact/admission ledger、不突变 agent-owned Local Work Trajectory、不把完整 trajectory JSON 写进 evidence metadata。review evidence 位于 `review/host-loop-workflow-evidence-metadata-2026-06-19.md`；tracked focused validation 结果为 `288 passed, 1 skipped`。后续方向分析 `design_docs/host-loop-workflow-evidence-metadata-followup-direction-analysis.md` 当前推荐下一条产品面 gate 为 `Host Evidence UI Binding`，但若继续后端编排可等待 live Qoder readiness 后做 credentialed smoke。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-host-evidence-ui-binding.md` 已完成。当前 VS Code progress graph preview 已接入只读 `dbc://host-evidence/presentation` resource，并把 backend-shaped presentation 显示为 Host Evidence operator section：覆盖 empty/card/malformed-row/read-error states，展示 runtime provider、host surface、invocation、stop reason/detail、run/output/permission review counts、key facts、refs 与 authority clues。UI 层保持 presentation-only，不解析 raw evidence artifacts、不执行 provider、不启动 daemon、不从 UI 突变 scheduler / ExchangeArtifact admission / Local Work Trajectory，也不改 backend presentation schema。review evidence 位于 `review/host-evidence-ui-binding-2026-06-19.md`；validation 结果为 VS Code extension build passed、focused preview tests `21 passed`、backend resource smoke `status=empty/card_count=0/error_count=0`，截图 artifact 位于 `output/playwright/host-evidence-ui/host-evidence-panel.png`。后续方向分析 `design_docs/host-evidence-ui-binding-followup-direction-analysis.md` 当前推荐下一条产品面 gate 为 `Scheduler Admission And Host Evidence Operator Workflow UI`，但 real credentialed provider smoke 与 background daemon lifecycle 仍应保持独立 gate。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-admission-host-evidence-operator-workflow-ui.md` 已完成。当前 VS Code progress graph preview 已新增 Scheduler Operator section：读取只读 `dbc://exchange-artifacts/bundle` 候选摘要，独立读取 `scheduler inspect-state` scheduler snapshot / event-log 摘要，展示默认 ExchangeArtifact store、admission ledger、scheduler snapshot、event log 与 scheduler-derived projection 路径，并把 admission、bounded fake-runtime loop、projection refresh 暴露为显式 operator button。三个 mutation action 均复用既有 CLI surface：`scheduler admit-exchange-artifact`、`scheduler daemon-loop --runtime-provider fake`、`scheduler project`；Host Evidence 仍通过 `dbc://host-evidence/presentation` 作为 durable scheduler-loop evidence 的 readback 面。该切片不新增 real-provider execution、不启动 background daemon、不自动 admission、不标记 ExchangeArtifact consumed、不从 UI 突变 agent-owned Local Work Trajectory、不改 backend scheduler/admission/evidence schema。review evidence 位于 `review/scheduler-admission-host-evidence-operator-workflow-ui-2026-06-19.md`；validation 结果为 VS Code extension build passed、focused preview tests `23 passed`、当前 workspace empty-state backend smoke 符合预期，截图 artifact 位于 `output/playwright/scheduler-operator-ui/scheduler-operator-panel.png`。后续方向分析 `design_docs/scheduler-admission-host-evidence-operator-workflow-ui-followup-direction-analysis.md` 当前推荐下一条产品面 gate 为 `Operator Workflow Dogfood Fixture`，先创建受控 candidate 并验证完整 UI sequence。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-operator-workflow-dogfood-fixture.md` 已完成。当前 Scheduler Operator workflow 已有 repeatable dogfood seed：`doc-based-coding scheduler seed-dogfood-fixture` 通过 `SchedulerTaskBatchSubmission` 与 `scheduler_task_batch_submission_to_artifact()` 创建一条 fake-runtime 两任务链 `dogfood:prepare -> dogfood:verify`，并写入默认 `.codex/orchestration/exchange-artifacts.json`。完整 CLI smoke 已覆盖 `seed -> resources read -> admit -> inspect -> daemon-loop fake -> project -> host-evidence presentation`；fixture 自身只突变 ExchangeArtifact store，不自动 admission、不运行 provider、不刷新 projection、不写 Host Evidence、不标记 consumed、不突变 Local Work Trajectory。review evidence 位于 `review/scheduler-operator-workflow-dogfood-fixture-2026-06-19.md`；validation 结果为 runtime fixture focused tests `2 passed`、CLI workflow focused tests `2 passed`、scheduler / ExchangeArtifact / Host Evidence focused regression `126 passed`。后续方向分析 `design_docs/scheduler-operator-workflow-dogfood-fixture-followup-direction-analysis.md` 当前推荐下一条 contract-first gate 为 `MCP/Host Unified Operator Workflow Surface`。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-operator-unified-workflow-surface.md` 已完成。当前 Scheduler Operator workflow 已提升为 host-neutral shared surface：`tools.progress_graph.run_scheduler_operator_workflow()`、MCP `schedulerOperatorWorkflow` 与 CLI `doc-based-coding scheduler operator-workflow` 共用同一个显式 request/result contract，可按 `admit` / `runLoop` / `refreshProjection` opt-in 组合候选 inspection、exact-version admission、bounded fake scheduler loop + scheduler-loop evidence、scheduler projection refresh 与 Host Evidence presentation readback。该 surface 默认 read-only，不自动 admission、不自动运行 provider、不运行 live Qoder、不启动 background daemon、不标记 ExchangeArtifact consumed、不改 scheduler/admission/evidence schema、不突变 agent-owned Local Work Trajectory；review evidence 位于 `review/scheduler-operator-unified-workflow-surface-2026-06-19.md`；validation 结果为 focused runtime workflow tests `3 passed`、focused CLI workflow tests `3 passed`、focused MCP workflow tests `1 passed`、scheduler / ExchangeArtifact / Host Evidence / operator workflow focused regression `134 passed`。后续方向分析 `design_docs/scheduler-operator-unified-workflow-surface-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Multi-Lane Scheduler Fixture`。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-operator-multilane-dogfood-fixture.md` 已完成。当前 Scheduler Operator dogfood surface 已新增第二个 deterministic fake-runtime fixture：`doc-based-coding scheduler seed-dogfood-fixture --fixture multilane` 可写入四任务、四 lane、四依赖的 scheduler-admission candidate，默认 seed 仍保持原 simple 两任务链。该多线 fixture 已通过 shared `schedulerOperatorWorkflow` backend/CLI/MCP 路径验证 exact admission、bounded fake loop、scheduler projection refresh 与 Host Evidence presentation readback；seed 只突变 ExchangeArtifact store，不自动 admission、不运行 provider、不刷新 projection、不写 Host Evidence、不标记 consumed、不突变 Local Work Trajectory。review evidence 位于 `review/scheduler-operator-multilane-dogfood-fixture-2026-06-19.md`；validation 结果为 focused runtime tests `5 passed`、focused CLI workflow tests `5 passed`、focused MCP workflow test `1 passed`、scheduler / ExchangeArtifact / Host Evidence / operator workflow focused regression `137 passed`。后续方向分析 `design_docs/scheduler-operator-multilane-dogfood-fixture-followup-direction-analysis.md` 当前推荐下一条产品面 gate 为 `Host UX Reuse Of Unified Workflow`，但 UI work 必须独立截图验证且不混入 live provider。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-operator-host-ux-unified-workflow-binding.md` 已完成。当前 VS Code Scheduler Operator Host UX 的三个显式按钮已复用共享 CLI surface `doc-based-coding scheduler operator-workflow`：`Admit` 只传 `--admit` 与 exact artifact/version，`Run bounded loop` 只传 `--run-loop` 与 fake runtime bounded loop/evidence 参数，`Refresh projection` 只传 `--refresh-projection` 与 guide context；artifact store、admission ledger、scheduler snapshot/event-log、projection output、evidence id/path 与 actor 均保持显式。Host UX last-action summary 已兼容 shared workflow nested payload。该切片不改视觉模型、不改 backend scheduler/admission/evidence schema、不运行 live provider、不启动 background daemon、不标记 ExchangeArtifact consumed、不从 UI 或 scheduler workflow 突变 agent-owned Local Work Trajectory。review evidence 位于 `review/scheduler-operator-host-ux-unified-workflow-binding-2026-06-19.md`；validation 结果为 VS Code extension build passed、panel test `10 passed`、HTML test `13 passed`、focused backend/CLI/MCP workflow regression `10 passed`，截图 artifact 位于 `output/playwright/scheduler-operator-ui/scheduler-operator-panel.png`。后续方向分析 `design_docs/scheduler-operator-host-ux-unified-workflow-binding-followup-direction-analysis.md` 当前建议在 release-grade Host UX 验证时做 extension-host click sequence smoke；若优先产品清晰度，则转向 scheduler projection readability review。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-operator-extension-host-click-sequence-smoke.md` 已完成。当前 Scheduler Operator Host UX 已有可执行 click/message contract smoke：`vscode-extension/src/views/schedulerOperatorContracts.ts` 统一 webview-shaped `schedulerOperatorAction` message coercion 与 shared `doc-based-coding scheduler operator-workflow` CLI args 构造，Progress Graph Preview panel 与 workflow runner 均复用该 helper。smoke 覆盖 `Admit -> Run bounded loop -> Refresh projection`，验证三步分别只携带 `--admit`、`--run-loop`、`--refresh-projection`，bounded loop 保持 fake runtime 与 deterministic evidence id/path 测试能力，缺参 admission 在 mutation 前被拒绝。该切片不新增 full Electron extension-host runner、不运行 live provider、不启动 background daemon、不改 backend scheduler/admission/evidence schema、不突变 agent-owned Local Work Trajectory、不改视觉模型。review evidence 位于 `review/scheduler-operator-extension-host-click-sequence-smoke-2026-06-19.md`；validation 结果为 VS Code extension build passed、click/message contract smoke `3 passed`、panel test `10 passed`、HTML test `13 passed`，截图 artifact 位于 `output/playwright/scheduler-operator-ui/scheduler-operator-panel.png`。后续方向分析 `design_docs/scheduler-operator-extension-host-click-sequence-smoke-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Scheduler Projection Readability Review`。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-scheduler-projection-readability-review.md` 已完成。当前 deterministic multi-lane Scheduler Operator fixture 已能生成可读的 scheduler-derived Local Work Trajectory projection，记录 `4 lanes / 6 events / 12 relations / 19 scheduler history lines`；backend projection 已修正 fan-in / scheduler-owned merge event order，使 merge event 排在目标 task 前并避免反向 lane-order sequence；frontend Local Work Trajectory renderer 对 scheduler-state projection 采用 earliest projected task order lane 排序、full-fit mode、分离宽高 fit 预算、初始 viewport 绑定与非动画 full-fit 定位，截图首帧不再裁切。该切片不新增 live provider、不启动 background daemon、不新增 full Electron runner、不改 scheduler/admission/evidence schema、不突变 agent-owned Local Work Trajectory、不替换 React Flow renderer。review evidence 位于 `review/scheduler-projection-readability-review-2026-06-19.md`；validation 结果为 VS Code extension build passed、Local Work Trajectory renderer test `2 passed`、Progress Graph Preview HTML test `13 passed`、focused scheduler projection/runtime pytest `4 passed, 243 deselected`，截图 artifact 位于 `output/playwright/scheduler-trajectory-preview/readability-review.png`。后续方向分析 `design_docs/scheduler-projection-readability-review-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Extension-Host Scheduler Projection Lifecycle Smoke`，先验证真实 VS Code webview lifecycle 的 refresh/display loop，再考虑更大图投影或 credentialed provider smoke。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-extension-host-scheduler-projection-lifecycle-smoke.md` 已完成。当前 VS Code Progress Graph Preview 已有 host-facing scheduler operator lifecycle seam：`schedulerOperatorAction` 会进入共享 helper，按 running-state render、runtime resolve、shared `scheduler operator-workflow` invocation、success/failure notification、disk reload 的顺序执行；Scheduler Trajectory Projection mount metadata 现在显式呈现 `lanes=4 / events=6 / relations=12`，并由 HTML evidence 与截图 artifact 验证。该切片不新增 live provider、不启动 background daemon、不新增 full Electron runner、不改 scheduler/admission/evidence schema、不突变 agent-owned Local Work Trajectory、不替换 React Flow renderer。review evidence 位于 `review/extension-host-scheduler-projection-lifecycle-smoke-2026-06-19.md`；validation 结果为 VS Code extension build passed、scheduler lifecycle smoke `3 passed`、Progress Graph Preview HTML test `13 passed`、panel test `10 passed`、Local Work Trajectory renderer test `2 passed`、scheduler operator contract test `3 passed`、focused scheduler projection/runtime pytest `4 passed, 243 deselected`，截图 artifact 位于 `output/playwright/scheduler-projection-lifecycle-smoke/lifecycle-smoke-trajectory-panel.png`。后续方向分析 `design_docs/extension-host-scheduler-projection-lifecycle-smoke-followup-direction-analysis.md` 当前推荐下一条窄 gate 为 `Electron Webview Runner Spike`，先判断 full Electron runner 的稳定性与成本，再决定是否纳入 release-grade validation。

2026-06-19 继续新增：`design_docs/stages/planning-gate/2026-06-19-electron-webview-runner-spike.md` 已完成。当前 VS Code Progress Graph Preview 已有窄 Electron extension-test runner seam：独立 `dist/electron-test/suite` bundle、deterministic fake workspace、direct `Code.exe` launch、test-mode-only rendered HTML snapshot command，以及 evidence-file guard。runner 验证目标为真实 VS Code extension host + real command/webview panel creation，并检查 Scheduler Trajectory Projection mount metadata `lanes=4 / events=6 / relations=12`。该切片不新增 live provider、不启动 background daemon、不改 scheduler/admission/evidence schema、不突变 agent-owned Local Work Trajectory、不替换 React Flow renderer；review evidence 位于 `review/electron-webview-runner-spike-2026-06-19.md`；validation 结果为 VS Code extension build passed、panel test `11 passed`、manifest guard `1 passed`、HTML test `13 passed`、scheduler lifecycle smoke `3 passed`、Local Work Trajectory renderer test `2 passed`、scheduler operator contract test `3 passed`、focused scheduler projection/runtime pytest `2 passed, 245 deselected`。真实 Electron smoke 当前到达 `Code.exe` 启动后被本机 VS Code `vscode-updating` mutex 阻塞，尚未产生 rendered Electron evidence；后续方向分析 `design_docs/electron-webview-runner-spike-followup-direction-analysis.md` 当前推荐在 VS Code 更新完成后原样重跑 smoke，若仍受用户安装态影响，再另起 isolated VS Code executable hardening slice。

2026-06-20 继续新增：`design_docs/stages/planning-gate/2026-06-20-electron-smoke-isolated-vscode-executable.md` 已完成。当前 Electron smoke runner 已把 VS Code executable 解析顺序显式化为 `VSCODE_ELECTRON_SMOKE_EXECUTABLE`、repo-local `output/electron/vscode-executable/Code.exe`、user-local fallback，并在启动前打印 selected source/path；当 fallback 到 user-local install 时，runner 会提示该路径可能受 update lock 影响，并在失败时给出 isolated executable rerun/remediation path。该切片不下载 VS Code、不新增 CI cache provisioning、不提升 Electron smoke 为 release-grade validation、不新增 live provider、不改 scheduler/admission/evidence schema；review evidence 位于 `review/electron-smoke-isolated-vscode-executable-2026-06-20.md`；validation 结果为 VS Code extension build passed、Electron runner executable resolution test `3 passed`、panel test `11 passed`、manifest guard `1 passed`。当前本机 smoke 仍因 user-local VS Code `vscode-updating` mutex 失败，但失败已能准确说明 selected executable source 与修复路径；后续方向分析 `design_docs/electron-smoke-isolated-vscode-executable-followup-direction-analysis.md` 当前推荐下一步提供 explicit isolated `Code.exe` 后重跑 smoke，成功后再讨论 provisioning policy 或 release-grade promotion。

2026-06-20 继续新增：`design_docs/stages/planning-gate/2026-06-20-electron-smoke-vscode-executable-provisioning-policy.md` 已完成。当前 Electron smoke isolated executable 已有第一版 manual provisioning policy：`design_docs/electron-smoke-vscode-executable-provisioning-policy.md` 定义 canonical local path `output/electron/vscode-executable/Code.exe`、sidecar `manifest.json`、必填版本/source/acquired_at/sha256 元数据、manual rerun 命令、integrity expectations、release-evidence boundary，以及 future automation boundary。该切片不下载 VS Code、不创建或提交 `Code.exe`、不新增 CI cache provisioning、不改 release packaging、不提升 Electron smoke 为 release-grade validation；review evidence 位于 `review/electron-smoke-vscode-executable-provisioning-policy-2026-06-20.md`；validation 结果为 docs grep passed。当前 rendered Electron evidence 仍依赖实际供应 isolated executable 或清除 user-local update lock；后续方向分析 `design_docs/electron-smoke-vscode-executable-provisioning-followup-direction-analysis.md` 当前推荐若能供应 stable executable 就走 manual placement evidence run，否则另开 provisioning automation slice。

2026-06-20 继续新增：`design_docs/stages/planning-gate/2026-06-20-electron-smoke-vscode-provisioning-automation.md` 已完成。当前 Electron smoke 已有显式 opt-in provisioning automation：`npm run provision:electron:vscode --prefix vscode-extension -- dry-run <exact-version>` 可无下载预览路径与选项，`... -- provision <exact-version>` 才会调用 `@vscode/test-electron` `downloadAndUnzipVSCode`，填充 `output/electron/vscode-executable` 并写 manifest。脚本强制 exact VS Code version，拒绝 floating `stable` / `insiders`，普通 build/test/smoke 不会隐式下载。该切片未执行下载、不提交 executable/manifest、不新增 CI cache provisioning、不提升 Electron smoke 为 release validation；review evidence 位于 `review/electron-smoke-vscode-provisioning-automation-2026-06-20.md`；validation 结果为 VS Code extension build passed、Electron provisioning test `4 passed`、Electron runner test `3 passed`、panel test `11 passed`、dry-run passed。后续方向分析 `design_docs/electron-smoke-vscode-provisioning-automation-followup-direction-analysis.md` 当前推荐选择 exact VS Code version 后执行 provisioning，再运行 Electron smoke 产出 rendered evidence。

2026-06-20 follow-up：`design_docs/electron-smoke-vscode-provisioning-automation-followup-direction-analysis.md` 的 Candidate A 已执行完成。使用 exact VS Code `1.93.1` 显式运行 `npm run provision:electron:vscode --prefix vscode-extension -- provision 1.93.1`，生成 repo-local isolated executable 与 `output/electron/vscode-executable/manifest.json`；随后 `npm run test:electron:smoke --prefix vscode-extension` 通过，runner 选择 `repo-local (output/electron/vscode-executable)`，真实 VS Code extension host + webview panel creation 路径产出 `output/electron/webview-runner-smoke/electron-webview-smoke-summary.json` 与 `rendered-progress-graph-preview.html`。summary 确认 `panelVisible=true`、scheduler root/payload present、`lanes=4`、`events=6`、`relations=12`；截图式验证 artifact 位于 `output/playwright/electron-webview-smoke/rendered-progress-graph-preview.png`，sanity check 为 `1600x1000` 且 `sampled_unique_colors=38`。Electron smoke 仍未自动提升为 release-grade validation；下一步方向分析 `design_docs/electron-smoke-release-validation-promotion-direction-analysis.md` 推荐先走 `Electron Smoke Release Checklist Pre-Provisioned Gate`，即 release checklist 只在本地预置 executable/manifest 时运行 smoke，并保持下载显式化。

2026-06-20 继续新增：`design_docs/stages/planning-gate/2026-06-20-electron-smoke-release-checklist-preprovisioned-gate.md` 已完成。当前 `scripts/release.py` 已把 Electron smoke 提升为 release checklist 中默认执行的 pre-provisioned gate：在 VSIX packaging 后、release zip packaging 前检查 `output/electron/vscode-executable/Code.exe` 与 `manifest.json`，要求 manifest `version == 1.93.1`，并在通过后运行既有 `npm run test:electron:smoke` 与 summary assertions（`ok=true`、`panelVisible=true`、scheduler root/payload present、`lanes=4`、`events=6`、`relations=12`）。`--skip-electron-smoke` 是显式 operator escape hatch；dry-run 只展示 gate、preflight 路径和 remediation command，不要求本地 executable 存在。该切片不新增 VS Code 下载路径、不引入 CI cache、不提交 `output/electron/`；review evidence 位于 `review/electron-smoke-release-checklist-preprovisioned-gate-2026-06-20.md`；validation 结果为 release versioning/preflight tests `26 passed`、Electron provisioning test `4 passed`、Electron runner test `3 passed`、release dry-run / skip dry-run passed、release smoke preflight/summary helper passed。

2026-06-20 继续新增：`design_docs/stages/planning-gate/2026-06-20-full-release-electron-smoke-evidence-run.md` 已完成。当前 pre-provisioned Electron smoke release gate 已通过完整 release flow 复验：`.\.venv\Scripts\python.exe scripts/release.py --no-isolation` 构建双 wheel、运行 full pytest `1754 passed, 3 skipped`、打包 VSIX `doc-based-coding-0.2.1.vsix`、运行 Electron smoke release gate 并断言 summary `ok=true / panelVisible=true / lanes=4 / events=6 / relations=12`、生成 `release/doc-based-coding-v0.9.8.zip`。第一次 full run 暴露 official instance pack lock 过期，已通过 MCP `pack_lock(pack_name="doc-loop-vibe-coding")` 刷新到 `sha256:6ef818671ce52695b1a7f81528ab0a2a395a5761c4ee9e986f3c9e4ba2913755`，并由 `pack_verify` 与 focused test 复验。review evidence 位于 `review/full-release-electron-smoke-evidence-run-2026-06-20.md`；release docs / commit message 已同步 Electron smoke gate 口径。CI-managed pinned VS Code cache/offline provenance 仍是后续独立 promotion line。

2026-06-20 继续新增：`design_docs/stages/planning-gate/2026-06-20-scheduler-event-log-compaction-and-replay-hardening.md` 已完成。当前 scheduler snapshot / JSONL event-log compaction 已具备显式 archive/reset replay boundary：`write_compacted_scheduler_snapshot()` 默认仍保持非破坏性，显式传入 `archive_event_log_path` 与 `reset_event_log=True` 时会将 compacted snapshot 已代表的 events 写入 archive JSONL，并将 active event log 重置为空，使后续 `recover_scheduler_state(compacted_snapshot, active_event_log)` 只 replay post-compaction events。`SchedulerCompactionResult` 暴露 archive/reset/replay-boundary metadata，`JsonlSchedulerEventLog` 新增 `write_all()` / `clear()`，strict unknown-task replay error 现明确说明 event log 不创建 scheduler task contract。review evidence 位于 `review/scheduler-event-log-compaction-and-replay-hardening-2026-06-20.md`；validation 结果为 compaction/replay focused pytest `17 passed`、full runtime orchestration pytest `185 passed`。该切片不启动 background daemon service、不运行 real provider、不绑定 UI、不实现 real sandbox provider、不突变 ExchangeArtifact/admission ledger、不从 scheduler code 突变 agent-owned Local Work Trajectory。

后续附加完成项：decision logs 最小字段设计、子 agent tracing 与 write-back 对接、多实例共存冲突解决策略、overrides 字段消费、hierarchical pack topology、completion boundary protocol、CI/CD 本地自动化脚本、Pack Index Metadata & CLI Pack Management、BL-1 Driver 职责定义文档、P4 handoff authority-doc footprint、`LLMWorker Structured Payload Producer Alignment`、`Payload + Handoff Footprint Controlled Dogfood`，以及 `LLMWorker Live Payload Contract Hardening`。详见上方"Post-v1.0 工作"条目。

低优先级 backlog（BL-2/3 adapter-registry/转接层）已结构化记录在 `design_docs/direction-candidates-after-phase-35.md`。

当前仓库已经完成 `Dogfood Issue Promotion / Feedback Packet Pipeline` 全链路：contract 定义（promotion threshold T1-T4 / suppression S1-S3 / issue candidate 12 字段 / feedback packet 9+3 字段 / 消费者边界 6×矩阵）→ dry-run 验证 → interface draft（5 数据结构 + 4 函数签名）→ 实现（`src/dogfood/` 4 模块：models / evaluator / builder / dispatcher）→ 16 单元测试 + 2 E2E 测试全部通过 → 全量基线 964 passed, 2 skipped。在此基础上，Slice A 将 pipeline 暴露为 MCP 工具 `promote_dogfood_evidence`，新增 `run_full_pipeline()` 协调函数 + 12 集成测试，全量基线升至 976 passed, 2 skipped。

## 当前 Handoff Footprint

- handoff_id: `2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close`
- source_path: `.codex/handoffs/history/2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close.md`
- scope_key: `knowledge-graph-engine-progress-preview-integration`
- created_at: `2026-06-02T10:16:21+08:00`

施工中提取的子 agent 机制需求（全部完成）：

1. ~~**Contract 生成接口**~~：已由 `src/subagent/contract_factory.py` 实现（Phase 8）。
2. ~~**Worker 调用运行时**~~：已由 `src/interfaces.py` WorkerBackend Protocol + `src/subagent/stub_worker.py` StubWorkerBackend 实现（Phase 8）。真正的 Worker adapter 留给后续 Phase。
3. ~~**Report 收集与校验**~~：已由 `src/subagent/report_validator.py` 实现（Phase 8）。
4. ~~**Handoff 落地**~~：已由 `src/subagent/handoff_builder.py` + PEP executor 实现（Phase 9）。
5. ~~**升级路径执行**~~：已由 `src/pep/notification_builder.py` + `src/pep/stub_notifier.py` + PEP executor 实现（Phase 10）。

子 agent 机制 5 项需求全部完成。Phase 33 已完成：Pipeline 初始化容错、MCP 降级模式、CLI --debug 模式。首个稳定 release 的边界与收口条件已写入 `docs/first-stable-release-boundary.md`。

