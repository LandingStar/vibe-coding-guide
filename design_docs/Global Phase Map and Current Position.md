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
## 阅读顺序

1. 先读本文件。
2. 再读 `design_docs/Project Master Checklist.md`。
3. 再读当前 active planning 或 phase 文档。
4. 再读 `docs/README.md` 与当前任务直接相关的 `docs/` 权威文档。
5. 若需要当前仓库的切片与协议细节，再读 `design_docs/stages/README.md` 与 `design_docs/tooling/`。

## 当前结论

Phase 3-35 均已完成。原 v1.0.0 已降级为 preview 定位，当前版本为 **v0.9.3**。Post-v1.0 的方向候选 A-J 标准化切片全部完成（双发行包、validator/check 收口、兼容元数据、MCP 刷新、doc-loop enforcement、handoff 主动调用、conversation progression、safe-stop writeback、external skill interaction），并继续完成了真实模型 producer 主线上的 `LLMWorker Structured Payload Producer Alignment` 与后续 `Payload + Handoff Footprint Controlled Dogfood`。

Release 封装已通过完整验证链：构建（双包 wheel/sdist）→ 测试 → 打包。当前可分发安装包为 `release/doc-based-coding-v0.9.3.zip`（147.0 KB），最新全量回归基线为 946 passed, 2 skipped。

后续附加完成项：decision logs 最小字段设计、子 agent tracing 与 write-back 对接、多实例共存冲突解决策略、overrides 字段消费、hierarchical pack topology、completion boundary protocol、CI/CD 本地自动化脚本、Pack Index Metadata & CLI Pack Management、BL-1 Driver 职责定义文档、P4 handoff authority-doc footprint、`LLMWorker Structured Payload Producer Alignment`、`Payload + Handoff Footprint Controlled Dogfood`，以及 `LLMWorker Live Payload Contract Hardening`。详见上方"Post-v1.0 工作"条目。

低优先级 backlog（BL-2/3 adapter-registry/转接层）已结构化记录在 `design_docs/direction-candidates-after-phase-35.md`。

当前仓库已经完成 `Dogfood Issue Promotion / Feedback Packet Pipeline` 全链路：contract 定义（promotion threshold T1-T4 / suppression S1-S3 / issue candidate 12 字段 / feedback packet 9+3 字段 / 消费者边界 6×矩阵）→ dry-run 验证 → interface draft（5 数据结构 + 4 函数签名）→ 实现（`src/dogfood/` 4 模块：models / evaluator / builder / dispatcher）→ 16 单元测试 + 2 E2E 测试全部通过 → 全量基线 964 passed, 2 skipped。在此基础上，Slice A 将 pipeline 暴露为 MCP 工具 `promote_dogfood_evidence`，新增 `run_full_pipeline()` 协调函数 + 12 集成测试，全量基线升至 976 passed, 2 skipped。

## 当前 Handoff Footprint

- handoff_id: `2026-04-16_1645_dogfood-promotion-packet-pipeline_stage-close`
- source_path: `.codex/handoffs/history/2026-04-16_1645_dogfood-promotion-packet-pipeline_stage-close.md`
- scope_key: `dogfood-promotion-packet-pipeline`
- created_at: `2026-04-16T16:45:00+08:00`

施工中提取的子 agent 机制需求（全部完成）：

1. ~~**Contract 生成接口**~~：已由 `src/subagent/contract_factory.py` 实现（Phase 8）。
2. ~~**Worker 调用运行时**~~：已由 `src/interfaces.py` WorkerBackend Protocol + `src/subagent/stub_worker.py` StubWorkerBackend 实现（Phase 8）。真正的 Worker adapter 留给后续 Phase。
3. ~~**Report 收集与校验**~~：已由 `src/subagent/report_validator.py` 实现（Phase 8）。
4. ~~**Handoff 落地**~~：已由 `src/subagent/handoff_builder.py` + PEP executor 实现（Phase 9）。
5. ~~**升级路径执行**~~：已由 `src/pep/notification_builder.py` + `src/pep/stub_notifier.py` + PEP executor 实现（Phase 10）。

子 agent 机制 5 项需求全部完成。Phase 33 已完成：Pipeline 初始化容错、MCP 降级模式、CLI --debug 模式。首个稳定 release 的边界与收口条件已写入 `docs/first-stable-release-boundary.md`。
