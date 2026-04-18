# 项目总清单与状态板

## 文档定位

本文件是 `doc-based-coding-platform` 的总入口、状态板与协作恢复入口。

若当前对话、workspace 现实状态与其他文档冲突，优先级应为：

1. 用户在最新对话中的明确决定
2. 当前 workspace 的现实状态
3. 正式设计文档与协议文档
4. 当前 active handoff

## 当前快照

- Snapshot Date: `2026-04-17`
- Project Name: `doc-based-coding-platform`
- Version: `0.9.3` (preview)
- Current Phase: `Post-v1.0 持续 dogfood — pack 预留接口已实现 + B-REF-1 Slice 1 测试覆盖完成`
- Active Slice: 无活跃 gate
- Latest Completed Slice: `B-REF-1 Slice 1 LoadLevel 三级渐进加载测试覆盖`（24 新测试）
- Safe Stop Status: `2026-04-17_2203_pack-reserved-interfaces-and-progressive-load-tests_stage-close`
- Test Baseline: `1104 passed, 2 skipped`

## 当前 Handoff Footprint

- handoff_id: `2026-04-17_2203_pack-reserved-interfaces-and-progressive-load-tests_stage-close`
- source_path: `.codex/handoffs/history/2026-04-17_2203_pack-reserved-interfaces-and-progressive-load-tests_stage-close.md`
- scope_key: `pack-reserved-interfaces-and-progressive-load-tests`
- created_at: `2026-04-17T22:03:34+08:00`

## 当前文档入口

- `docs/README.md`
- `docs/installation-guide.md`
- `docs/official-instance-doc-loop.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/tooling/Dual-Package Distribution Standard.md`
- `design_docs/tooling/Backlog and Reserve Management Standard.md`
- `design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md`
- `design_docs/dogfood-evidence-issue-feedback-integration-direction-analysis.md`
- `design_docs/dogfood-evidence-issue-feedback-boundary.md`
- `design_docs/dogfood-issue-promotion-feedback-packet-contract-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-evidence-issue-feedback-integration.md`
- `design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`
- `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`
- `design_docs/live-payload-rerun-followup-direction-analysis.md`
- `design_docs/live-payload-rerun-verification-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-16-live-payload-rerun-verification.md`
- `design_docs/stages/planning-gate/2026-04-16-real-worker-payload-adoption-judgment.md`
- `review/live-payload-rerun-verification-2026-04-16.md`
- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/dogfood-pipeline-workflow-integration-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-pipeline-mcp-exposure.md`
- `design_docs/overrides-field-consumption-direction-analysis.md`
- `design_docs/hierarchical-pack-topology-direction-analysis.md`
- `design_docs/phase-35-external-skill-interface-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-12-external-skill-interaction-interface.md`
- `design_docs/stages/planning-gate/2026-04-13-ci-cd-build-release-automation.md`
- `design_docs/stages/planning-gate/2026-04-13-pack-index-and-cli-management.md`
- `design_docs/stages/planning-gate/2026-04-13-bl1-driver-responsibilities.md`
- `design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md`
- `design_docs/stages/planning-gate/2026-04-11-mcp-pack-info-refresh-consistency.md`
- `design_docs/stages/planning-gate/2026-04-11-strict-doc-loop-runtime-enforcement.md`
- `design_docs/stages/planning-gate/2026-04-11-doc-loop-enforcement-and-mcp-client-neutrality.md`
- `design_docs/stages/planning-gate/2026-04-11-installation-flow-documentation.md`
- `design_docs/stages/planning-gate/2026-04-11-compatibility-metadata-and-version-declaration.md`
- `design_docs/stages/planning-gate/2026-04-11-official-instance-validator-check-contract.md`
- `design_docs/stages/planning-gate/2026-04-11-dual-package-minimal-install-implementation.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-11-first-stable-release-closure.md`
- `docs/first-stable-release-boundary.md`
- `design_docs/stages/planning-gate/2026-04-11-error-recovery-entry-points.md`
- `design_docs/stages/planning-gate/2026-04-11-structured-error-format.md`
- `design_docs/stages/planning-gate/2026-04-11-v1-stable-release-confirmation.md`
- `design_docs/stages/planning-gate/2026-04-11-dual-package-install-standard.md`
- `design_docs/direction-candidates-after-phase-34.md`
- `CHANGELOG.md`
- `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/direction-candidates-after-phase-31.md`
- `design_docs/phase-0-26-review.md`
- `design_docs/stages/README.md`
- `design_docs/tooling/README.md`
- `.codex/handoffs/CURRENT.md`

## 已确认决策

- 本项目默认采用“生成/更新 doc 规划 -> 按 doc 实施 -> 结果回写 doc”的工作流。
- 根目录 `docs/` 是当前仓库里关于平台与官方实例定位的最高权威来源。
- `design_docs/` 现在主要承载状态板、planning/phase 文档与内部设计推导。
- 重要设计节点默认必须先交用户审核，再进入下一大步。
- handoff 只负责安全停点交接，不替代正式设计文档。
- 本仓库已经开始使用自身产出的文档型成果作为默认控制面。
- Pipeline / CLI / MCP / Instructions / project-local pack 等运行时入口在首个稳定 release 前保持 pre-release dogfood 定位，不作为所有切片的强制默认依赖。

## 当前待办与风险

> Phase 4–26 的详细完成记录已归档至 `design_docs/phase-0-26-review.md`。

### 活跃待办

- [x] 首个稳定 release 收口：定义默认自用入口的稳定条件 — `docs/first-stable-release-boundary.md`
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-11-dual-package-minimal-install-implementation.md` 落地双发行包最小可安装实现
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-11-official-instance-validator-check-contract.md` 收口官方实例 validator/check 契约边界
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-11-compatibility-metadata-and-version-declaration.md` 收口兼容元数据与版本声明
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-11-installation-flow-documentation.md` 固定安装流程说明与 MCP 安装态接入文档
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-11-doc-loop-enforcement-and-mcp-client-neutrality.md` 修补严格 doc-loop 执行缺口与 MCP 客户端中立表述
- [x] post-v1.0：评估是否进入 strict doc-loop runtime enforcement 切片
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-11-strict-doc-loop-runtime-enforcement.md` 收口 runtime 可审计的 doc-loop 约束边界
- [x] post-v1.0：评估是否进入 MCP pack info 刷新一致性切片
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-11-mcp-pack-info-refresh-consistency.md` 修复长生命周期 MCP pack state 刷新一致性
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md` 收口 handoff model 主动调用与 blocked 停止语义
- [x] post-v1.0：在当前安全停点生成 handoff
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-12-conversation-progression-contract-stability.md` 收口“非用户许可不终止 + 选择/审批时以提问推进”的稳定行为支架
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-12-safe-stop-writeback-bundle.md` 将 safe-stop writeback 收口为 bundle 能力，使 handoff generation / `CURRENT.md` refresh / Checklist / Phase Map / direction / checkpoint 同步成为 first-class workflow contract（crucial）
- [x] post-v1.0：完成与当前项目和具体 skill 解耦的通用外部 skill 交互接口方向分析（首个目标可围绕当前 handoff skill）
- [x] post-v1.0：按 `design_docs/phase-35-external-skill-interface-direction-analysis.md` 的边界起草 H planning-gate，并将 `authority -> shipped copies` 作为 companion mechanism 收口
- [x] post-v1.0：按 `design_docs/stages/planning-gate/2026-04-12-external-skill-interaction-interface.md` 收口通用外部 skill 交互接口能力，并将 `authority -> shipped copies` 作为 companion mechanism 落地
- [x] post-v1.0：记录 driver 与外部 skill 交互标准 / 接口 / 留空转接层，以及本轮其余 skill 特化后续项（暂不实现）— 已结构化记录为 `design_docs/direction-candidates-after-phase-35.md` §Driver / Adapter / 转接层 Backlog（BL-1 / BL-2 / BL-3）
- [x] post-v1.0：release 构建与安装验证 — 双包 wheel 构建通过、干净 venv 安装验证通过（原 v1.0.0，后降级为 preview；当前产物为 `release/doc-based-coding-v0.9.3.zip`）
- [x] post-v1.0：对话中临时规则突破 / 修改能力（BL-4）— 已收口为可追溯、可审计、可撤销的 runtime contract：`TemporaryOverride` 数据模型 + `.codex/temporary-overrides.json` 持久化 + `governance_override` MCP tool + 约束可突破性分类（C1/C2/C3/C6/C7 overridable, C4/C5/C8 non-overridable）+ safe-stop writeback bundle 自动过期 + instructions generator 与 pack rules 同步
- [x] post-v1.0：driver 本体与 doc-loop 实例包资产及 release 产物的分离审查 — 审查完成：交叉导入/包配置/CLI 入口/发布包/根级文件/docs/测试组织均边界清晰；唯一违规（`src/` 硬编码实例路径）已修复为 pack-declared `shipped_copies` 动态发现；Slice B（reference 放置策略）暂存待决
- [x] post-v1.0：pack manifest schema 版本化 — `manifest_version` 字段 + 版本感知 loader（major 不兼容拒绝 / minor 向前兼容警告）+ 全部 4 个 manifest 文件已标注 `"1.0"` + `docs/pack-manifest.md` Schema Versioning 节已文档化
- [x] post-v1.0：修复 pre-existing test failure（`test_mcp_require_pipeline_uses_error_info`）— 全套测试 669 passed, 0 failures
- [x] post-v1.0：validate 命令治理阻塞 vs 运行失败语义区分 — 退出码三级（0/1/2）+ `command_status`/`governance_status`/`blocking_constraints` JSON 字段 + 终端文案显式区分 + C5 在初始状态降级为 warn — 675 passed, 0 failures
- [ ] 持续 pre-release dogfood：在实际开发中受控使用 CLI / MCP / Instructions，并收集反馈
- [ ] post-v1.0 backlog：将 dogfood 所需的证据收集、问题收集、问题反馈整合收口为组件或 skill；当前先完成 adoption judgment，并在其 1/2 步里同步观察哪些流程值得抽象固化，再决定是否起独立 planning-gate
- [x] dogfood 发现 #1：`query_decision_logs` MCP 工具未注册 — 方法已在 `src/mcp/tools.py` 实现但未在 `src/mcp/server.py` 的 `list_tools` 中注册路由，导致工具不可达（低工作量修复）—— 已修复，803 passed
- [x] dogfood 发现 #2：decision log 持久化与 dry_run 耦合 — MCP 默认 `dry_run=True`，decision_log_entry 只在返回值中出现但不写 `.codex/decision-logs/` 文件—— 已解耦，审计日志现始终持久化
- [x] dogfood 发现 #3：v0.9.1 安装验证中发现 4 类问题（版本漂移、pack 自动发现缺失、本地 wheel 安装不顺畅、状态提取不完整）— 详见 `issues/issue_doc_loop_v091_release_and_pack_discovery.md`；所有问题已修复：site-packages 自动发现已实现（`_discover_packs` + `include_site_packages` 测试隔离参数）、版本一致性检查脚本 `release/verify_version_consistency.py` 已新增、INSTALL_GUIDE.md 已覆盖离线安装、状态提取已正常工作 — 803 passed, 0 failures
- [x] dogfood 发现 #3：v0.9.1 安装验证中发现 4 类问题（版本漂移、pack 自动发现缺失、本地 wheel 安装不顺畅、状态提取不完整）— 详见 `issues/issue_doc_loop_v091_release_and_pack_discovery.md`；所有问题已修复：site-packages 自动发现已实现（`_discover_packs` + `include_site_packages` 测试隔离参数）、版本一致性检查脚本 `release/verify_version_consistency.py` 已新增、INSTALL_GUIDE.md 已覆盖离线安装、状态提取已正常工作；当前全量回归为 823 passed, 2 skipped
- [x] CI/CD 本地自动化脚本 — `scripts/build.py`（双包 wheel 一键构建 + clean + 版本校验 + 内容物验证）+ `scripts/release.py`（构建 + pytest + release zip 打包）+ `--no-isolation` 选项避免 PyPI 网络依赖 — E2E 验证通过（823 passed, 2 skipped, release zip 147.0 KB）
- [x] dogfood 发现 #4：4 个测试硬编码版本号 `0.9.1`，导致 version bump 时 CI 失败 — 已改为动态读取 `pyproject.toml` 版本（`_read_canonical_version()`），v0.9.2 release 验证通过
- [x] Pack Index Metadata & CLI Pack Management — `src/pack/pack_manager.py`（install/remove/list/info）+ CLI `pack` 子命令 + `docs/pack-index-format.md` 格式文档 + `docs/plugin-model.md` Pack Origins 更新 + 20 targeted tests — 823 passed, 2 skipped
- [x] dogfood 发现 #5：`pack install` 创建 `platform.json pack_dirs` 后，config 路径不再扫描 `.codex/packs/` 散装 `.pack.json` 文件，导致原有 pack 不可见 — 已修复：config 路径增加 fallback 扫描 — 823 passed
- [x] 状态面一致性收口 — `design_docs/stages/planning-gate/2026-04-14-state-surface-consistency-closeout.md` 已完成；Checklist / Phase Map / CURRENT / checkpoint 已统一到 v0.9.3 preview 口径，并回到无 active planning-gate 的 safe stop
- [x] BL-1 Driver 职责定义文档 — `docs/driver-responsibilities.md` 定义 driver 角色、职责边界、输入来源/结果分发路径，与 `external-skill-interaction.md` 形成消费方-提供方对称引用，与 `subagent-management.md` supervisor 角色对齐
- [x] depends_on 依赖校验（gap analysis #11）—— warning-only 校验 + Pipeline.info() 暴露
- [x] provides 消费用于 delegation capability check（gap analysis #5）—— `RuleConfig.available_capabilities` + delegation advisory warning + review 升级
- [x] checks 字段与 manifest 直连（gap analysis #16）—— `PackRegistrar` 自动注册 `check(context)` 脚本 + `Pipeline.info().registered_checks` 暴露 + runtime writeback 前可消费
- [x] hierarchical pack topology（tree-scoped packs）—— `PackManifest.parent/scope_paths` + `PackTree` + `ContextBuilder.build_scoped()` + `Pipeline.process_scoped()` / MCP `scope_path` + authority docs sync
- [x] overrides 字段消费（gap analysis #12）—— `PackContext.merged_overrides` 提取 + `check_overrides()` warning-only 验证 + `PrecedenceResolver` explicit_override 标注 + `Pipeline.info()` 暴露 override_declarations / override_warnings + 权威文档 `overrides` 开放问题已回答
- [x] completion boundary protocol（完成边界失忆修复）—— pack 规则 `completion_boundary_protocol` + `get_next_action()` `completion_boundary_reminder` + instructions generator 静态冗余 + Document-Driven Workflow Standard 第 6 条
- [x] 类型/接口依赖关系图谱提取（Slice 1）—— `tools/dependency_graph/` 模块：基于 Pylance MCP 的图谱聚合（而非自写 AST 提取器），186 节点 / 56 边，`dependents_of` / `dependencies_of` / `implementors_of` 查询 + AST 符号发现 174 个 + dogfood 验证 9 个 Protocol 依赖链 + 27 测试 — 850 passed, 2 skipped
- [x] 对话行为约束规则重写 — 正面模板 + 4 项发送前检查清单替代原有负面禁止列表；同步 `.github/copilot-instructions.md`、`AGENTS.md`、bootstrap `AGENTS.md`、`doc-loop-vibe-coding/references/conversation-progression.md`
- [x] 变更影响分析与耦合钩子（Slice 2）—— `tools/dependency_graph/impact.py` ImpactAnalyzer BFS 传播 + `coupling.py` CouplingStore/CouplingChecker + `coupling_annotations.json` 5 个耦合标注 + query.py 扩展 + 22 测试 — 872 passed, 2 skipped
- [x] VibeCoding-Workflow 外部项目分析 — `review/vibecoding-workflow-sakura1618.md` 逐条模式映射：Run Budget / Anti-Drift / Milestone Replan 触发条件 + 博客半自动→全自动交叉验证
- [x] Anti-Drift 规则采纳 — AD-1~AD-5 + slice_budget + milestone_replan_triggers 已加入 `project-local.pack.json` rules
- [x] External Project Review Standard — `design_docs/tooling/External Project Review Standard.md`：5 步标准流程（快速概览→结构化对比→借鉴点提取→差异分析→行动项生成）+ review 文档模板 + 质量门
- [x] MCP 变更影响与耦合检查工具（Slice 3）—— `impact_analysis` + `coupling_check` MCP 工具注册 + GovernanceTools 方法 + server 分发 + 9 测试 — 881 passed, 2 skipped
- [x] 子 agent 研究综合报告 —— `design_docs/subagent-research-synthesis.md`：5 份外部研究 + 内部设计 + gap 分析综合、P1-P4 优先级排序、Gap A/C/D 已验证修复
- [x] Worker Registry 驱动 Executor 动态选择（P1/BL-2）—— Executor 接受 WorkerRegistry、`_resolve_worker` 动态路由、`worker_selected`/`worker_fallback` audit 事件、向后兼容旧 `worker=` 注入 + 11 测试 — 892 passed, 2 skipped
- [x] Handoff Recovery Hardening —— `CURRENT.md` intake 新增 `source_hash` 校验 + 唯一 active canonical 断言 + refresh-current 冲突明细 + Authoritative Sources 降噪 + 6 测试 — 898 passed, 2 skipped
- [x] Handoff Validator 独立化（P2）—— `HandoffValidator` protocol + 默认 schema/invariant validator + `_execute_handoff_mode()` 独立 validation 分支 + `handoff_validated`/`handoff_validation_failed` 审计事件 + 7 测试 — 905 passed, 2 skipped
- [x] Subagent Report richer writeback payload 前置切片（P3-prep）—— `Subagent Report` schema 新增可选 `artifact_payloads`（`path` / `content` / `operation` / `content_type`），`docs/subagent-schemas.md` 固定其与 `changed_artifacts` 的边界，schema-driven report validator 接受合法 payload，HTTP worker 透传远端 payload + 7 测试 — 912 passed, 2 skipped
- [x] artifact_payloads -> WritebackPlan Mapping（P3）—— `WritebackEngine.plan()` 直接消费 `report.artifact_payloads`，对 `allowed_artifacts`、绝对/越界路径与空路径执行硬边界校验，summary writeback 增加 payload planned/skipped 摘要，`create` 不再覆盖已有文件，补齐单元与集成回归 — 922 passed, 2 skipped
- [x] StubWorker Payload Producer Alignment（A1）—— `StubWorkerBackend` 在 `allowed_artifacts` 非空时产出受控 `artifact_payloads`，目录边界映射到固定子路径，官方示例 report 与实例 schema 校验同步，first-party delegation -> payload-derived writeback 最小闭环打通 — targeted 51 passed, 1 skipped；full 931 passed, 2 skipped
- [x] Handoff Authority-Doc Footprint（P4）—— latest canonical handoff 的 4 字段 pointer contract 已同步到 authority docs / checkpoint / safe-stop helper；新增 `Current Handoff` 结构段与 `current_handoff_footprint` helper 输出，保持 handoff 正文仍以 canonical 文件为真相源 — targeted 72 passed；full 936 passed, 2 skipped
- [x] LLMWorker Structured Payload Producer Alignment —— `LLMWorker` 现在返回 schema-valid `Subagent Report`，受控 prompt / response contract 下最多产出 1 个 `artifact_payloads` candidate；非结构化响应回退为 schema-valid `partial` report，API 错误回退为 schema-valid `blocked` report，delegation -> LLMWorker -> payload-derived writeback mock 链打通 — targeted 51 passed, 1 skipped；full 942 passed, 2 skipped
- [x] Payload + Handoff Footprint Controlled Dogfood —— baseline `StubWorker` payload path 在临时目录里稳定触发 payload-derived writeback，且 `CURRENT.md` / checkpoint 的 latest handoff footprint 一致；live DashScope `LLMWorker` 返回 schema-valid `completed` report，但真实 payload candidate 使用了 schema 不接受的 `operation` / `content_type` 枚举，导致 payload 被保守丢弃，结果已写入 `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md` — baseline/runtime observation only；full baseline 保持 942 passed, 2 skipped
- [x] LLMWorker Live Payload Contract Hardening —— prompt contract 显式收紧到允许枚举并增加禁止示例；`content_type` 只接受极窄 alias normalization（`text/markdown -> markdown`、`text/plain -> text`、`application/json -> json`）；当 LLM 主动尝试 payload 但所有 candidate 都被 guard 拒绝时，`status` 从 `completed` 下调为 `partial` — targeted 55 passed, 1 skipped；full 946 passed, 2 skipped
- [x] Live Payload Rerun Verification —— 单次受控 live DashScope rerun 在临时目录中成功返回合法 `artifact_payloads`，`path=docs/controlled-dogfood-llm.md`、`operation=update`、`content_type=markdown`，最终 payload writeback 成功命中目标文件；结果已写入 `review/live-payload-rerun-verification-2026-04-16.md` — runtime observation only；code baseline 保持 946 passed, 2 skipped
- [x] Real-Worker Payload Adoption Judgment —— 当前权威口径已收口为“`LLMWorker` real-worker payload path 已有 1 条正向 live signal，可继续作为受控 dogfood 路径观察，但仍不属于默认稳定面”；扩大 wording 的最小额外证据门已定义为“在无新 runtime 改动前提下再拿到 1 条独立受控 live success”；dogfood evidence / issue / feedback integration 继续保留为 backlog — doc-only slice，结果已写入 `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- [x] Controlled Real-Worker Payload Evidence Accumulation —— 在无新 runtime code、schema 或 worker 语义变更前提下，`LLMWorker` 受控 payload path 再获得 1 条独立正向 live signal，raw response、final report 与 payload-derived writeback 三层再次同时成立；当前权威口径已收紧为“`LLMWorker` 受控 payload path 已具备最小可重复 dogfood 能力”，结果已写入 `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`
- [x] Dogfood Evidence / Issue / Feedback Integration —— docs-only boundary consolidation 已完成：`design_docs/dogfood-evidence-issue-feedback-boundary.md` 已明确 evidence / issue / feedback 三类对象边界、文档映射与未来 component / skill 的最小 I/O ceiling，当前已据此收窄下一条实现前切片

### 当前待推进切片

- [x] Dogfood Issue Promotion / Feedback Packet Contract —— contract gate 已完成（6/6）、dry-run 验证通过、interface draft gate 已完成（8/8）、`src/dogfood/` pipeline 已实现（models + evaluator + builder + dispatcher）、18 项新测试全部通过、全量基线 964 passed, 2 skipped
- [x] Dogfood Promotion Packet Interface Draft + Implementation —— 产出 `design_docs/dogfood-promotion-packet-interface-draft.md`、`src/dogfood/` 4 个模块、`tests/test_dogfood_pipeline.py`（16 单元测试）+ `tests/test_dogfood_e2e.py`（2 E2E 测试）
- [x] decision logs 最小字段设计（research gap #1）—— `DecisionLogEntry` 19 字段 + `DecisionLogStore` JSON Lines 持久化 + Pipeline 后处理聚合 + MCP `query_decision_logs()` 工具 + 785 passed
- [x] 子 agent tracing 与 write-back 对接（research gap #2）—— ExecutionResult trace_id/delegation_mode + WritebackEngine audit event 发射（writeback_planned/artifact_changed）+ Executor contract_generated/subagent_report_received/writeback_blocked_by_check event + 793 passed
- [x] 多实例共存冲突解决策略（research gap #4）—— `_deep_merge()` 冲突收集器 + `PackContext.merge_conflicts` 字段 + `PrecedenceResolver` 同层 tie_broken_by 标记 + `Pipeline.info()` merge_conflicts 暴露 + 801 passed

### 研究参考待办（来源：Claude Managed Agents Platform 分析 — `review/claude-managed-agents-platform.md`）

- [x] B-REF-1: Pack 渐进式加载设计 — 三级加载（METADATA/MANIFEST/FULL）已实现：Slice 1 LoadLevel enum + ContextBuilder 分阶段 build + upgrade()；Slice 2 Pipeline MANIFEST 降级 + pack_context lazy upgrade；Slice 3 MCP get_pack_info level/scope_path 参数 + description 字段 — 1095 passed, 2 skipped
- [x] B-REF-2: Pack description 质量标准 — 已建立质量标准文档（`design_docs/tooling/Pack Description Quality Standard.md`）+ `validate_description()` 验证函数 + 现有 pack 已添加符合标准的 description + 9 个新测试 — 1104 passed, 2 skipped

> **当前测试基线**: 1133 passed, 2 skipped
- [x] B-REF-3: Pack 内部组织规范 — 引用深度 ≤ 1 + 按域拆分 + TOC 规则已建立（`design_docs/tooling/Pack Internal Organization Standard.md`）+ `validate_pack_organization()` 验证函数 + 13 个新测试 — 1117 passed, 2 skipped
- [ ] B-REF-4: Permission policy 分层覆盖模型 — 在 governance_decide 之外补充工具粒度的权限策略：pack 级默认 + 单 tool 级 override + deny_message 机制（参考 Claude permission policies）
- [ ] B-REF-5: 工作流中断原语 (interrupt primitive) — 在 workflow 引擎层显式化中断与重定向操作，对应"发现超出 scope 时回退到 planning-gate"的模式（参考 Claude `user.interrupt`）
- [ ] B-REF-6: 子 agent 上下文隔离评估 — 评估当前子 agent 共享全部上下文是否合理，是否应改为"共享工作区文件 + 隔离对话/状态上下文"（参考 Claude multi-agent 共享文件系统 + 隔离 context）
- [x] B-REF-7: Custom tool surface 合并审计 — 审计报告已完成 + `analyze_changes` 统一入口已实施（`design_docs/tooling/MCP Tool Surface Audit.md`）：11 个 MCP tools + 旧名保留为别名 + 6 个新测试 — 1133 passed, 2 skipped

### VS Code Extension

- [x] P0+P1: Extension 骨架 + MCP Client + Constraint Dashboard — 15 个 TS 文件，esbuild 编译通过，`.vsix` 已打包（`design_docs/stages/planning-gate/2026-04-18-vscode-extension-p0-p1.md`）
- [x] F5 端到端验证 — Extension Dev Host 中成功运行：Activity Bar 图标、MCP stdio 连接、Constraint Dashboard 显示 C1-C8 状态、Output Channel 日志正常（`design_docs/stages/planning-gate/2026-04-18-vscode-extension-f5-e2e-verification.md`）— 1133 passed, 2 skipped

### 已完成里程碑

- ✅ Phase 0–3：文档定型 + prototype cleanup
- ✅ Phase 4–5：平台对象规格化（9 JSON Schema）
- ✅ Phase 6–10：PDP/PEP Runtime + Subagent + Handoff + 升级路径
- ✅ Phase 11–14：Review 状态机 + 写回 + 审核编排 + E2E 治理测试
- ✅ Phase 15：Real Worker Adapter (LLM + HTTP)
- ✅ Phase 16：Pack Runtime Loader
- ✅ Phase 17：Audit & Tracing System
- ✅ Phase 18：Validator/Checks/Trigger Framework
- ✅ Phase 19：Official Instance E2E Validation (40 项)
- ✅ Phase 20：Worker Collaboration Modes
- ✅ Phase 21：Checkpoint Persistence + Direction Template
- ✅ Phase 22：v0.1-dogfood Release (Pipeline + MCP + Instructions)
- ✅ Phase 23：PackContext Downstream Wiring
- ✅ Phase 24：MCP Prompts/Resources + always_on 注入
- ✅ Phase 25：Extension Bridging (Pack → Registry)
- ✅ Phase 26：on_demand 懒加载 API
- ✅ Phase 27：Dogfood 深度验证
- ✅ Phase 28：Dogfood Feedback Remediation
- ✅ Phase 29：Self-Hosting Workflow Rule Formalization
- ✅ Phase 30：Dogfood Feedback Remediation Part 2 (F8 First)
- ✅ Phase 31：F4 Validator Diagnostics Follow-up
- ✅ Phase 32：First Stable Release Closure（边界定义 + 收口清单）
- ✅ Phase 33：Error Recovery for Entry Points（Pipeline/MCP/CLI 容错）
- ✅ Phase 34：Structured Error Format Unification（ErrorInfo 统一错误结构）
- ✅ Phase 35：v1.0 Stable Release Confirmation（B7 用户确认 + 版本标记）

### 风险

- 无当前阻塞项。- `pack_manager.py` 中 `runtime_compatibility` 字段在 install/list 时仅存储但从未校验兼容性（缺少 runtime 版本比对逻辑）；`_compute_checksum()` 已定义但未被任何代码路径调用——两者均为预留接口，可在后续 pack 升级/完整性校验需求时补充实现。
  - **已实现**（`design_docs/stages/planning-gate/2026-04-17-pack-manager-reserved-interfaces.md`）：`_check_runtime_compatibility()` + `_get_runtime_version()` + install 前 hard reject + checksum 记录到 `platform.json` + `PackInfo.checksum` 字段 — 1058 passed, 2 skipped- safe-stop writeback 现已显式化为 bundle contract、`current_handoff_footprint` 与 MCP helper 输出；当前残余风险在于它仍主要是“contract + validation + files_to_update”层，而不是自动执行所有写回动作的全自动 executor。
- 当前“外部 skill 交互”已经有通用 contract 与 handoff reference implementation；当前残余风险在于它仍只在 handoff family 与本轮触达的 shipped copies 上得到验证，尚未扩展到更多 future skill families。
- 当前 runtime contract 已明确声明：`check_constraints()` 只 machine-check C4/C5；更严格的对话推进约束仍由规则/提示词层承担，而非完整运行时审计层。
- `_summarize_content` 对 flat 内容可能丢信息（已知，低影响）。
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
- Phase 22 已启动：v0.1-dogfood Release — Pipeline + MCP Server。
- 集成方案分析完成 → 方案 E（MCP + Instructions 生成）已确认。
  - 5 种 Copilot 集成方案运行时模拟 → 见 `design_docs/stages/planning-gate/copilot-integration-runtime-simulation.md`
  - 约束执行力从 advisory 提升到 structural。
- Pack Manifest 字段间隙分析完成 → 见 `design_docs/stages/planning-gate/pack-context-wiring-gap-analysis.md`
  - 19 个字段中仅 `rules` 一条完整贯通路径。
  - 4 个 merged 集合为死数据，6 个扩展件字段未接线。
- `src/workflow/pipeline.py`：Pipeline 编排类。
  - `Pipeline.from_project(root)` 自动发现 pack 并加载。
  - `Pipeline.process(input_text)` → PipelineResult（envelope + execution + audit）。
  - `Pipeline.check_constraints()` → ConstraintResult（C5 等约束检查）。
  - Pack 自动发现：.codex/platform.json 配置优先，否则约定扫描。
- `src/__main__.py`：CLI 入口。
  - `python -m src process "input"` / `info` / `validate` / `check` 四个命令。
- `src/mcp/tools.py`：GovernanceTools 层。
  - `governance_decide(input)` → BLOCK/ALLOW + 约束检查 + PDP/PEP 结果。
  - `check_constraints()` → 约束状态 + files_to_reread + 当前 phase。
  - `get_next_action()` → 下一步推荐 + 文档引用 + ask_user 标志。
  - `writeback_notify(phase)` → 自动推进建议 + 待更新文件列表。
  - `get_pack_info()` → 已加载 pack 信息。
- `src/mcp/server.py`：MCP Server（stdio 传输）。
  - VS Code 配置 `.vscode/mcp.json` 已就绪。
  - E2E 协议验证通过：initialize → tools/list → tools/call。
- 474 项 pytest 测试全部通过（2 skipped）。
- Phase 22 Slice 1+2 已完成。
- Phase 22 MCP dogfood 验证通过，修复 checkpoint 解析 bug。
- Phase 22 Slice 3（Instructions Generator）已完成：
  - `src/workflow/instructions_generator.py`：从 PackContext 生成 copilot-instructions 段落。
  - CLI：`python -m src generate-instructions [--output PATH]`。
  - 20 项 pytest 测试全部通过。
- Phase 22 Slice 4（project-local pack 约束声明）已完成：
  - `.codex/packs/project-local.pack.json` 新增 `rules.constraints`（C1-C8 完整约束）。
  - 生成的 instructions 包含所有约束（含 severity 标签）。
- Phase 22 Slice 5 推迟（PackContext downstream wiring，留待 dogfood 反馈后精准设计）。
- 494 项 pytest 测试全部通过（2 skipped）。
- Phase 22 v0.1-dogfood Release 已收口完成。
- Phase 23 已启动：PackContext Downstream Wiring + Dogfood。
- `src/pack/override_resolver.py` 进化：RuleConfig 新增 `allowed_gates: set[str]` 字段。
  - resolve() 将 PackContext.merged_intents → platform_intents、merged_gates → allowed_gates。
  - wiring 代码移到 early return 之前，确保即使无显式 rules 也能传递 merged 集合。
- `src/pdp/intent_classifier.py` 进化：classify() 新增 platform_intents 限制检查。
  - 若 rule_config.platform_intents 非空且分类结果不在其中，返回 "unknown"。
  - platform_intents 为权威来源，keyword_map 不自动豁免。
- `src/pdp/gate_resolver.py` 进化：resolve() 新增 allowed_gates 校验。
  - 若 rule_config.allowed_gates 非空且结果不在其中，fallback 到最高可用 gate（approve→review→inform）。
- `tests/test_packcontext_wiring.py`：18 项新测试覆盖三个切片。
- 512 项 pytest 测试全部通过（2 skipped）。
- Phase 23 PackContext Downstream Wiring + Dogfood 已全部完成。
- Phase 24 已启动：MCP Prompts/Resources + always_on 注入。
- `src/mcp/server.py` 进化：新增 list_prompts / get_prompt / list_resources / read_resource 处理器。
  - Pack 声明的 prompts 可通过 `/<server>.<prompt>` 调用。
  - always_on 文件作为 MCP Resources 暴露（内存读取）。
  - on_demand 文件作为 MCP Resources 暴露（按需磁盘读取）。
- `src/mcp/tools.py` 进化：GovernanceTools 新增 list_prompts / get_prompt / list_resources / read_resource 方法。
  - prompt 描述自动从文件首行非标题文本提取。
  - Resource URI 格式：`pack://always-on/{filename}` 和 `pack://{pack}/on-demand/{path}`。
- `src/workflow/instructions_generator.py` 进化：_always_on_section() 现输出文件内容摘要。
  - _summarize_content() 提取标题和关键段落，最多 20 行。
- `tests/test_mcp_prompts_resources.py`：19 项新测试覆盖三个切片。
- 531 项 pytest 测试全部通过（2 skipped）。
- Phase 24 MCP Prompts/Resources + always_on 注入已全部完成。
- Phase 25 已启动：Extension Bridging (Pack → Registry)。
- `src/pack/registrar.py`：PackRegistrar 桥接组件。
  - 读取 manifest.validators，动态加载 Python 模块，找 validate() 函数包装为 ScriptValidator。
  - 读取 manifest.triggers，创建 EventStubTrigger 注册到 TriggerDispatcher。
  - 无 validate() 函数的脚本自动跳过（记录到 skipped）。
  - 文件不存在时优雅降级（警告而不崩溃）。
- `src/workflow/pipeline.py` 进化：_load_packs() 现调用 PackRegistrar 注册扩展件。
  - Pipeline.info() 新增 registered_validators / registered_triggers / skipped 字段。
- `tests/test_extension_bridging.py`：13 项新测试覆盖所有切片。
- 544 项 pytest 测试全部通过（2 skipped）。
- Phase 25 Extension Bridging 已全部完成。
- Phase 26 已启动：on_demand 懒加载 API。
- `src/pack/context_builder.py` 进化：PackContext 新增 on_demand_entries 字段和 load_on_demand()/list_on_demand() 方法。
  - ContextBuilder.build() 现收集所有 pack 的 on_demand 条目到 on_demand_entries。
  - load_on_demand(key) 按需读取文件并缓存。
  - 多 pack 同 key 时高优先级 pack 覆盖。
- `src/mcp/tools.py` 进化：read_resource() 现使用 PackContext.load_on_demand()。
- `tests/test_on_demand.py`：11 项新测试覆盖所有场景。
- 555 项 pytest 测试全部通过（2 skipped）。
- Phase 26 on_demand 懒加载 API 已全部完成。
- gap analysis 19 个字段中的 `depends_on` 校验、`provides` 消费、`checks` manifest 直连与 `overrides` 字段消费现已全部完成；所有已知实现型 gap 均已关闭。
- Phase 27 已完成：Dogfood 深度验证。
- Phase 28 已完成：Dogfood Feedback Remediation。
- `src/pdp/intent_classifier.py`：保留既有 `correction` 关键词，同时新增 `issue-report` 扩展关键词，并加入 `correction/issue-report` 窄 tie-break 规则。
- `src/workflow/checkpoint.py`：新增 `sync_checkpoint_phase()`，用于在 write-back 完成后刷新 checkpoint phase 且保留其他字段。
- `src/mcp/tools.py`：`writeback_notify()` 在 live 路径下调用 checkpoint 同步。
- `src/workflow/pipeline.py`：暴露 `is_dry_run` 属性，供上层工具判断是否允许写入 checkpoint。
- `tests/test_pdp_basic.py`、`tests/test_checkpoint.py`、`tests/test_mcp_tools.py`：新增 7 项回归测试覆盖 issue-report 分类与 live checkpoint 同步。
- 566 项 pytest 测试全部通过（2 skipped）。
- Phase 28 Dogfood Feedback Remediation 已全部完成。
- 下一步：基于 `design_docs/direction-candidates-after-phase-28.md` 选择 Phase 29 方向。
- 风险：当前无 blocking 项；剩余 dogfood 问题主要是 F4/F8。

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
- `2026-04-10`: Phase 22 Slice 1-4 完成——v0.1-dogfood Release：Pipeline 编排器（PDP→PEP 统一链）+ CLI 入口（4 命令）+ MCP Server（stdio, 5 工具）+ Instructions Generator（PackContext→Markdown）+ project-local pack 约束声明（C1-C8）。MCP dogfood 验证通过，修复 checkpoint 解析 bug。494 项 pytest 全部通过，Phase 22 收口。
- `2026-04-10`: Phase 23 Slice A+B+C 完成——PackContext Downstream Wiring：OverrideResolver 将 merged_intents/merged_gates 传入 RuleConfig（platform_intents + allowed_gates），intent_classifier 新增 platform_intents 限制检查，gate_resolver 新增 allowed_gates 校验与 fallback。Pack 声明现可真正控制 PDP 分类与门级行为。512 项 pytest 全部通过，Phase 23 完结。
- `2026-04-10`: Phase 24 Slice A+B+C 完成——MCP Prompts/Resources + always_on 注入：MCP server 新增 list_prompts/get_prompt/list_resources/read_resource 处理器，Pack prompts 可通过 Copilot `/<server>.<prompt>` 调用，always_on/on_demand 作为 MCP Resources 暴露，Instructions Generator 现输出 always_on 文件内容摘要。531 项 pytest 全部通过，Phase 24 完结。
- `2026-04-10`: Phase 25 Slice A+B 完成——Extension Bridging：创建 PackRegistrar 桥接组件，Pack 声明的 validators 自动加载并注册到 ValidatorRegistry，triggers 自动注册到 TriggerDispatcher。Pipeline 集成 PackRegistrar，info() 暴露注册状态。544 项 pytest 全部通过，Phase 25 完结。
- `2026-04-10`: Phase 26 完成——on_demand 懒加载 API：PackContext 新增 on_demand_entries + load_on_demand()/list_on_demand() 方法，按需读取文件并缓存。MCP read_resource() 现使用 load_on_demand()。gap analysis 最大间隙已闭合。555 项 pytest 全部通过，Phase 26 完结。
- `2026-04-10`: Phase 27 完成——Dogfood 深度验证：执行 governance_decide / check_constraints / writeback_notify 三个真实场景，沉淀 11 个反馈项到 `design_docs/dogfood-feedback-phase-27.md`，修复 planning gate 状态扫描误报、README 被误识别为 gate、checkpoint 未纳入 files_to_reread、active gate 回退检测缺失等问题，并新增 5 项回归测试。559 项 pytest 全部通过，Phase 27 完结。
- `2026-04-10`: Phase 28 完成——Dogfood Feedback Remediation：修复 `issue-report` 分类准确率（中文/英文 bug report）并保持 `correction` 既有行为稳定；新增 `sync_checkpoint_phase()` 并在 live `writeback_notify()` 路径下自动刷新 checkpoint phase。新增 7 项回归测试，566 项 pytest 全部通过，Phase 28 完结。
- `2026-04-11`: Phase 29 完成——Self-Hosting Workflow Rule Formalization：将“文档型成果立即自用、运行时入口在首个稳定 release 前只作为 pre-release dogfood”写入 Workflow Standard、官方实例定位、Checklist 与 doc-loop prompts。当前确认核心链条已可运行，但尚未达到可默认依赖的稳定版门槛；本 Phase 只做文档与提示词收口，不修改代码，也未新增自动化测试。
- `2026-04-11`: Phase 30 完成——Dogfood Feedback Remediation Part 2 (F8 First)：按用户审核先只处理 F8。`src/__main__.py` 中 `check` 命令现默认只输出约束 / 状态信息，不再混入完整治理链；若提供文本输入，会明确提示改用 `process`。新增 `tests/test_cli.py`，针对 `check` 无输入、有输入、帮助文本 3 个场景做回归验证；`pytest tests/test_cli.py` 通过（3 passed）。F4 保留为下一条独立诊断切片。
- `2026-04-11`: Phase 31 完成——F4 Validator Diagnostics Follow-up：`src/pack/registrar.py` 新增 `skipped_details` 诊断层，区分 `missing-path`、`unsupported-extension`、`load-failed`、`missing-validate` 四类 skipped 原因，并通过 `summary()` / `Pipeline.info()` 暴露。新增官方实例 real-pack 场景覆盖，确认当前两个 validator 脚本被 skipped 的原因是 `missing-validate`，不是路径 bug。`pytest tests/test_extension_bridging.py` 通过（15 passed）。
