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
- 下一步：方向选择

## 阅读顺序

1. 先读本文件。
2. 再读 `design_docs/Project Master Checklist.md`。
3. 再读当前 active planning 或 phase 文档。
4. 再读 `docs/README.md` 与相关权威文档。
5. 若需要当前仓库的切片与协议细节，再读 `design_docs/stages/README.md` 与 `design_docs/tooling/`。

## 当前结论

Phase 3-21 均已完成。平台已有 9 个 JSON Schema + PDP 完整决策链 + PEP 委派管线 + Handoff 落地 + 升级路径执行 + Review 状态机 + 文档写回 + ReviewOrchestrator + 3 种通知适配器 + Markdown 语义更新 + FeedbackAPI + E2E 治理测试 + Real Worker Adapter + Pack Runtime Loader + Audit & Tracing System + Validator/Checks/Trigger Framework + Official Instance E2E Validation + Worker Collaboration Modes (Handoff + Subgraph) + Checkpoint Persistence + Direction Template。431 项 pytest 通过。

施工中提取的子 agent 机制需求：

1. ~~**Contract 生成接口**~~：已由 `src/subagent/contract_factory.py` 实现（Phase 8）。
2. ~~**Worker 调用运行时**~~：已由 `src/interfaces.py` WorkerBackend Protocol + `src/subagent/stub_worker.py` StubWorkerBackend 实现（Phase 8）。真正的 Worker adapter 留给后续 Phase。
3. ~~**Report 收集与校验**~~：已由 `src/subagent/report_validator.py` 实现（Phase 8）。
4. ~~**Handoff 落地**~~：已由 `src/subagent/handoff_builder.py` + PEP executor 实现（Phase 9）。
5. ~~**升级路径执行**~~：已由 `src/pep/notification_builder.py` + `src/pep/stub_notifier.py` + PEP executor 实现（Phase 10）。

子 agent 机制 5 项需求全部完成。下一步应评估 Phase 11 方向。
