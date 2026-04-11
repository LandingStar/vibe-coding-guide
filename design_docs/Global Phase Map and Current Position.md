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
- Release 构建 + 安装 + adoption 端到端验证通过：`release/doc-based-coding-v1.0.0.zip` 已打包

## 阅读顺序

1. 先读本文件。
2. 再读 `design_docs/Project Master Checklist.md`。
3. 再读当前 active planning 或 phase 文档。
4. 再读 `docs/README.md` 与相关权威文档。
5. 若需要当前仓库的切片与协议细节，再读 `design_docs/stages/README.md` 与 `design_docs/tooling/`。

## 当前结论

Phase 3-35 均已完成。v1.0.0 已发布。Post-v1.0 的方向候选 A-J 标准化切片全部完成（双发行包、validator/check 收口、兼容元数据、MCP 刷新、doc-loop enforcement、handoff 主动调用、conversation progression、safe-stop writeback、external skill interaction）。

Release 封装已通过完整验证链：构建（双包 wheel/sdist）→ 安装（干净 venv + CLI 入口）→ Adoption（空项目 bootstrap → validate → MCP 启动）。可分发安装包为 `release/doc-based-coding-v1.0.0.zip`。

当前仓库处于无 active planning gate 的 safe stop。后续方向为继续受控 dogfood，仅在出现新回归/缺口信号时起新 planning-gate。低优先级 backlog（BL-1/2/3 driver/adapter/转接层）已结构化记录在 `design_docs/direction-candidates-after-phase-35.md`。

validator/check 契约收口切片现也已完成：权威文档已明确 `validators / checks / scripts` 的消费边界，官方实例 manifest 不再把 self-check 脚本误报为 runtime validators。当前更适合继续进入兼容元数据声明；另有一个低优先级后续项是修复 MCP `get_pack_info` 的缓存刷新一致性。

兼容元数据与版本声明切片现也已完成：官方实例 pack manifest 已用 `runtime_compatibility` 声明最小 runtime 兼容范围，并与包元数据依赖范围对齐。当前若继续推进，最自然的后续只剩 MCP `get_pack_info` 的缓存刷新一致性；否则已经可以视为一个合理的 post-v1.0 安全停点。

安装流程文档化与 MCP 客户端中立切片现也已完成：仓库已补齐安装态文档入口，明确 `doc-based-coding-mcp` 面向 Copilot、Codex 及其他 stdio-capable MCP host，而不是 Copilot 专用；同时修复了 active planning gate 的 `—` 哨兵值误判，并把 project-local pack 的 C1 文案对齐到当前正式规则。

strict doc-loop runtime enforcement 切片现也已完成：runtime constraint 结果已显式区分 machine-checked 与 instruction-layer 约束边界，MCP 对外文案已与真实能力对齐。

MCP pack info refresh consistency 切片现也已完成：长生命周期 `GovernanceTools` 现已在每次 public tool 调用前刷新 Pipeline，因此 pack manifest / prompts / resources 的磁盘变化会进入后续调用；源码级热重载仍需重启 host。

在此之后，用户又新增了一条直接影响 handoff 执行语义的窄需求：handoff 构建应可由 model 主动调用，且 handoff 分支内其他指令在未返回 `blocked` 时也应可由 model 继续执行。对应的 planning-gate `design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md` 现已完成：权威协议、workflow 文档、active skill 文本与 bootstrap / example 副本已统一到“安全停点下 model 可主动进入 handoff 分支，且只有 `blocked` 是停止信号”的口径。

safe-stop handoff 已生成并刷新 `.codex/handoffs/CURRENT.md` 后，用户又先行要求修补“未经用户许可不得终止对话、遇到选择/审批应以提问继续推进”这条约束的稳定生效问题。对应的 planning-gate `design_docs/stages/planning-gate/2026-04-12-conversation-progression-contract-stability.md` 现已完成：正式规则、project-local pack、prompt surfaces、instructions generator、MCP next-step outputs 与 official-instance always_on reference 已统一到同一套 conversation progression contract。

随后进入的 `design_docs/stages/planning-gate/2026-04-12-safe-stop-writeback-bundle.md` 现也已完成：仓库已新增显式 `safe-stop writeback bundle` helper，并让 `writeback_notify()` 返回 required/conditional bundle contract 与完整 `files_to_update`，同时把 workflow / handoff 协议同步到同一口径。当前仓库因此回到 post-v1.0 safe stop，且不处于新的 active planning-gate。

在 safe stop 下，用户先确认了 `H. 通用外部 Skill 交互接口能力 Slice` 需要先做方向分析，再在看到文档后决定是否激活。对应分析现已写入 `design_docs/phase-35-external-skill-interface-direction-analysis.md`，随后又已进入并完成 `design_docs/stages/planning-gate/2026-04-12-external-skill-interaction-interface.md`。

该切片现已把通用 external skill interaction contract、handoff reference implementation family 以及 `authority -> shipped copies` companion drift-check / distribution rule 收口到 authority docs、project-local pack、instructions / MCP surface、official instance reference 与 handoff skill texts。当前仓库因此再次回到无 active planning-gate 的 post-v1.0 safe stop。

当前更自然的下一步，不再是继续扩大平台能力面，而是二选一：

- 保持 `G. 持续 Pre-Release Dogfood / Gap Tracking Slice` 作为默认背景主线，等待真实 regression / gap signal 再起新 gate。
- 若用户希望先把后续实现边界写得更清楚，则再起一条“driver / adapter / 留空转接层 backlog 记录”类的轻量文档切片。

用户现已明确选择第一条：继续受控 dogfood，不立即起新的 planning-gate。因而当前仓库维持无 active planning-gate 的 safe stop，并把后续新切片的触发条件收紧为“dogfood 命中新的真实 regression / gap signal”或“用户明确要求先文档化 backlog 边界”。

施工中提取的子 agent 机制需求：

1. ~~**Contract 生成接口**~~：已由 `src/subagent/contract_factory.py` 实现（Phase 8）。
2. ~~**Worker 调用运行时**~~：已由 `src/interfaces.py` WorkerBackend Protocol + `src/subagent/stub_worker.py` StubWorkerBackend 实现（Phase 8）。真正的 Worker adapter 留给后续 Phase。
3. ~~**Report 收集与校验**~~：已由 `src/subagent/report_validator.py` 实现（Phase 8）。
4. ~~**Handoff 落地**~~：已由 `src/subagent/handoff_builder.py` + PEP executor 实现（Phase 9）。
5. ~~**升级路径执行**~~：已由 `src/pep/notification_builder.py` + `src/pep/stub_notifier.py` + PEP executor 实现（Phase 10）。

子 agent 机制 5 项需求全部完成。Phase 33 已完成：Pipeline 初始化容错、MCP 降级模式、CLI --debug 模式。首个稳定 release 的边界与收口条件已写入 `docs/first-stable-release-boundary.md`。
