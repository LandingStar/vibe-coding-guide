# Phase 0–26 回顾整理

> 生成日期: 2026-04-10
> 基线: 555 passed, 2 skipped

---

## 1. 项目定位

**doc-based-coding-platform** — 一个 human-governed, AI-operated, artifact-mediated workflow 平台。

- 平台提供治理引擎（PDP→PEP）、Pack 插件系统、审计链路
- 官方实例 `doc-loop-vibe-coding`：面向 AI 辅助开发的文档驱动工作流
- 当前已 dogfood：通过 MCP Server 接入 VS Code Copilot

---

## 2. Phase 旅程总览

| Phase | 名称 | 性质 | 关键产出 | 测试数 |
|-------|------|------|----------|--------|
| 0 | 平台权威文档定型 | 文档 | `docs/platform-positioning.md`, `core-model.md` | — |
| 1 | repo-local adoption 对齐 | 文档 | `docs/project-adoption.md` | — |
| 2 | prototype authority rereview | 文档 | `doc-loop-prototype-authority-rereview.md` | — |
| 3 | prototype cleanup | 文档 | SKILL.md / 模板对齐 | — |
| 4 | 平台对象规格化 | Schema | 9 个 JSON Schema (PDP/PEP/Subagent) | — |
| 5 | 子 agent 对象规格化 | Schema | Contract/Report/Handoff schema | — |
| 6 | PDP/PEP Runtime 骨架 | 代码 | `src/pdp/`, `src/pep/` 核心 | 25 |
| 7 | PDP 完整决策链 | 代码 | delegation/escalation/precedence resolver | 47 |
| 8 | PEP + Subagent 接口 | 代码 | `src/subagent/`, 依赖反转 Protocol | 71 |
| 9 | Handoff 落地 | 代码 | handoff_builder + 文件持久化 | 85 |
| 10 | 升级路径执行 | 代码 | notifier + escalation 执行 | 93 |
| 11 | Review 状态机引擎 | 代码 | 6 状态/7 事件/8 迁移规则 | 129 |
| 12 | 文档写回 + 工作流闭环 | 代码 | WritebackEngine + 原子写入 | 155 |
| 13 | Review 完整流程 + 真实通知 | 代码 | 3 种 Notifier + ReviewOrchestrator | 183 |
| 14 | Write-Back 语义更新 + E2E | 代码 | MarkdownUpdater + FeedbackAPI + 5 E2E 路径 | 228 |
| 15 | Real Worker Adapter | 代码 | LLMWorker + HTTPWorker (DashScope 验证) | 253 |
| 16 | Pack Runtime Loader | 代码 | ManifestLoader + ContextBuilder + OverrideResolver | 288 |
| 17 | Audit & Tracing System | 代码 | AuditLogger + TraceContext + 2 Backend | 313 |
| 18 | Validator/Checks/Trigger | 代码 | 3 Protocol + Registry + ScriptValidator | 348 |
| 19 | Official Instance E2E | 测试 | 40 项 E2E 官方实例全链路验证 | 387 |
| 20 | Worker Collaboration Modes | 代码 | Handoff/Subgraph 协作模式 + PDP 模式选择 | 414 |
| 21 | Checkpoint Persistence | 代码 | checkpoint 工具 + 方向模板 | 431 |
| 22 | v0.1-dogfood Release | 集成 | Pipeline + CLI + MCP Server + Instructions Gen | 494 |
| 23 | PackContext Downstream Wiring | 代码 | merged_intents/gates → PDP 行为控制 | 512 |
| 24 | MCP Prompts/Resources | 代码 | Prompts + Resources + always_on 注入 | 531 |
| 25 | Extension Bridging | 代码 | PackRegistrar (Pack → Registry) | 544 |
| 26 | on_demand 懒加载 | 代码 | load_on_demand() + 缓存 | 555 |

---

## 3. 架构总览

### 3.1 模块拓扑

```
src/
├── pdp/                    # Policy Decision Point（决策层）
│   ├── intent_classifier    # 意图分类（6 种 + 扩展）
│   ├── gate_resolver        # 门级判定（inform/review/approve）
│   ├── delegation_resolver  # 委派决策（worker/handoff/subgraph 模式）
│   ├── escalation_resolver  # 升级决策（human/main-agent）
│   ├── precedence_resolver  # 优先级仲裁
│   └── decision_envelope    # 统一决策信封
│
├── pep/                    # Policy Enforcement Point（执行层）
│   ├── executor             # 核心执行器（模式分发）
│   ├── review_orchestrator  # 审核编排（approve/reject/revision）
│   ├── writeback_engine     # 文档写回（原子写入）
│   ├── markdown_updater     # Section 级语义更新
│   ├── notification_builder # 通知构建
│   ├── notifiers/           # Console / File / Webhook
│   ├── action_log           # 行动日志
│   └── stub_notifier        # 测试用 stub
│
├── pack/                   # Pack 插件系统
│   ├── manifest_loader      # JSON manifest 解析
│   ├── context_builder      # 多层 pack 合并 → PackContext
│   ├── override_resolver    # PackContext → RuleConfig (PDP 规则注入)
│   └── registrar            # Pack → ValidatorRegistry/TriggerDispatcher 桥接
│
├── subagent/               # 子 agent 基础设施
│   ├── contract_factory     # delegation → Contract
│   ├── report_validator     # Report schema 校验
│   ├── handoff_builder      # Handoff 对象构建
│   └── stub_worker          # 测试用 worker
│
├── collaboration/          # 协作模式
│   ├── modes                # CollaborationMode 枚举
│   ├── handoff_mode         # fire-and-transfer
│   └── subgraph_mode        # 隔离执行 + delta 合并
│
├── workers/                # Worker 后端
│   ├── config               # WorkerConfig + Registry
│   ├── llm_worker           # OpenAI-compatible (DashScope)
│   └── http_worker          # HTTP REST endpoint
│
├── validators/             # 校验+触发器框架
│   ├── base                 # Validator/Check/Trigger Protocol
│   ├── registry             # 按名注册/查询
│   ├── schema_validator     # JSON Schema 校验
│   ├── script_validator     # Python 函数包装
│   └── trigger_dispatcher   # 事件路由
│
├── audit/                  # 审计追踪
│   ├── audit_logger          # 事件日志 + 多后端
│   └── trace_context         # trace_id 串联全链路
│
├── review/                 # Review 引擎
│   ├── state_machine        # 6 状态 / 7 事件 / 8 迁移
│   └── feedback_api         # 外部 reviewer 入口
│
├── workflow/               # 工作流编排
│   ├── pipeline             # Pipeline（PDP→PEP 统一链）
│   ├── instructions_generator # PackContext → copilot-instructions
│   └── checkpoint           # 断点持久化
│
├── mcp/                    # MCP Server
│   ├── server               # stdio transport + handlers
│   └── tools                # GovernanceTools 状态包装
│
├── interfaces.py           # 核心 Protocol 定义
└── __main__.py             # CLI 入口
```

### 3.2 数据流

```
输入文本
  │
  ▼
Pipeline.process()
  │
  ├─ PackContext (from manifest_loader → context_builder)
  │    └─ RuleConfig (from override_resolver)
  │
  ├─ PDP Chain ────────────────────────┐
  │  intent_classifier                 │
  │  → gate_resolver                   │ → Decision Envelope
  │  → delegation_resolver             │
  │  → escalation_resolver             │
  │  → precedence_resolver ────────────┘
  │
  ├─ PEP Executor ─────────────────────┐
  │  ReviewStateMachine                │
  │  → Worker/Handoff/Subgraph 执行    │ → Execution Result
  │  → Validators + Checks            │
  │  → WritebackEngine ───────────────┘
  │
  └─ AuditLogger (全链路 9 种事件)
```

### 3.3 外部接口

| 接口 | 方式 | 用途 |
|------|------|------|
| CLI | `python -m src {process,info,validate,check,generate-instructions}` | 本地开发/调试 |
| MCP Server | stdio transport, 5 Tools + Prompts + Resources | Copilot 集成 |
| copilot-instructions.md | 静态文件生成 | Copilot 上下文注入 |

---

## 4. Pack 系统字段覆盖 (Gap Analysis)

19 个 manifest 字段中的覆盖情况：

| # | 字段 | 状态 | 实现 Phase |
|---|------|------|-----------|
| 1 | name | ✅ 加载+标识 | 16 |
| 2 | version | ✅ 加载+展示 | 16 |
| 3 | kind | ✅ 加载+分类 | 16 |
| 4 | scope | ✅ 隐式 (注册层级) | 16 |
| 5 | provides | ⚠️ 合并但未消费 | 16 (partial) |
| 6 | document_types | ✅ 合并+传递 | 16 |
| 7 | intents | ✅ → platform_intents → PDP 限制 | 23 |
| 8 | gates | ✅ → allowed_gates → PDP fallback | 23 |
| 9 | always_on | ✅ 内容加载+Instructions 注入+MCP Resource | 24 |
| 10 | on_demand | ✅ 懒加载+缓存+MCP Resource | 26 |
| 11 | depends_on | ❌ 声明但未校验 | — |
| 12 | overrides | ⚠️ 未消费 | — |
| 13 | prompts | ✅ MCP Prompts 暴露 | 24 |
| 14 | templates | ✅ MCP Prompts (模板即提示) | 24 |
| 15 | validators | ✅ → ScriptValidator → Registry | 25 |
| 16 | checks | ⚠️ Registry 声明但未与 manifest 直连 | 18 (partial) |
| 17 | scripts | ✅ 动态模块加载 → ScriptValidator | 25 |
| 18 | triggers | ✅ → EventStubTrigger → TriggerDispatcher | 25 |
| 19 | rules | ✅ → RuleConfig → PDP 全链路 | 16+23 |

**完整贯通：15/19**，部分贯通：3/19，未贯通：1/19。

---

## 5. 权威文档体系

### 5.1 平台文档 (`docs/`)

| 文件 | 内容 |
|------|------|
| platform-positioning.md | 平台定位与边界 |
| core-model.md | 核心对象与 Actor 关系 |
| plugin-model.md | Pack 插件体系 |
| pack-manifest.md | manifest 字段规范 |
| governance-flow.md | PDP→PEP 治理流程 |
| review-state-machine.md | 6 状态 / 7 事件 |
| pdp-decision-envelope.md | 决策信封结构 |
| intent-classification.md | 意图分类规则 |
| gate-decision.md | 门级判定 |
| delegation-decision.md | 委派决策 |
| escalation-decision.md | 升级决策 |
| precedence-resolution.md | 优先级仲裁 |
| subagent-management.md | 子 agent 管理 |
| subagent-schemas.md | 子 agent 对象 Schema |
| official-instance-doc-loop.md | 官方 doc-loop 实例 |
| project-adoption.md | 项目接入指南 |

### 5.2 Schema (`docs/specs/`)

9 个 JSON Schema (draft-2020-12)：
- pdp-decision-envelope, intent-classification-result, gate-decision-result
- delegation-decision-result, escalation-decision-result, precedence-resolution-result
- subagent-contract, subagent-report, handoff

### 5.3 设计文档 (`design_docs/`)

- Project Master Checklist — 总状态板
- Global Phase Map — 阶段索引
- direction-candidates-after-phase-{N}.md — 方向候选分析
- stages/planning-gate/ — 各 Phase 规划文档
- tooling/ — 长期协议与标准

---

## 6. 测试体系

29 个测试文件，555 项测试：

| 文件 | 测试数 | 覆盖范围 |
|------|--------|---------|
| test_pdp_basic | PDP 基础 | intent/gate |
| test_pdp_full_chain | PDP 全链 | 5 resolver 联动 |
| test_e2e_flow | PEP 端到端 | 基础执行流 |
| test_pep_delegation | PEP 委派 | worker 管线 |
| test_subagent_modules | 子 agent | contract/report/handoff |
| test_handoff | Handoff | 落地+持久化 |
| test_escalation_execution | 升级 | notifier+状态 |
| test_review_state_machine | RSM | 状态迁移 |
| test_review_orchestrator | 审核编排 | approve/reject/revision |
| test_pep_review_integration | PEP+RSM | 集成 |
| test_writeback_engine | 写回 | 原子写入 |
| test_pep_writeback_integration | PEP+WB | 写回集成 |
| test_markdown_updater | MD更新 | section操作 |
| test_notifiers | 通知 | 3种适配器 |
| test_governance_e2e | 治理E2E | 5条完整路径 |
| test_workers | Worker | LLM+HTTP |
| test_pack_runtime | Pack加载 | manifest/context/override |
| test_audit_system | 审计 | logger+backend+全链路 |
| test_validator_framework | 校验框架 | validator/check/trigger |
| test_official_instance_e2e | 实例E2E | 官方实例40项全链路 |
| test_collaboration | 协作 | handoff/subgraph模式 |
| test_checkpoint | 断点 | write/read/validate |
| test_pipeline | Pipeline | 编排+集成 |
| test_instructions_generator | 指令生成 | PackContext→MD |
| test_mcp_tools | MCP工具 | 5 tools |
| test_packcontext_wiring | 贯通 | intents/gates→PDP |
| test_mcp_prompts_resources | MCP扩展 | prompts/resources |
| test_extension_bridging | 扩展桥接 | registrar |
| test_on_demand | 懒加载 | load_on_demand |

---

## 7. 设计决策摘要

### 核心架构决策

1. **PDP/PEP 分离** — 决策与执行解耦，支持 dry-run
2. **依赖反转 (Protocol)** — `interfaces.py` 定义 WorkerBackend / ContractFactory / ReportValidator / EscalationNotifier
3. **Pack 三层覆盖** — platform → instance → project-local，高优先级覆盖低优先级
4. **Method E 集成** — 双层防线：静态 (copilot-instructions.md) + 动态 (MCP tools)
5. **全链路审计** — trace_id 串联 PDP→PEP→Writeback，9 种事件类型

### 技术选型

- **零外部依赖** — stdlib only (urllib.request 替代 requests, json 替代 pydantic)
- **MCP SDK** — mcp==1.27.0, stdio transport
- **LLM** — OpenAI-compatible API (支持 DashScope)
- **测试** — pytest, 无 mock 框架依赖

### 未实施的有意省略

- `depends_on` 依赖校验 — 当前单 pack 场景下优先级低
- `provides` 消费 — 已合并但 PDP 未使用，需要 delegation capability check 场景驱动
- `overrides` — 声明未消费，需要跨 pack 覆盖场景
- `checks` 与 manifest 直连 — Registry 已有框架，但 pack manifest 的 checks 字段未自动注册

---

## 8. 当前能力矩阵

| 能力 | 状态 | 说明 |
|------|------|------|
| 意图分类 | ✅ | 6 种内建 + pack 扩展 + platform_intents 限制 |
| 门级判定 | ✅ | inform/review/approve + allowed_gates 校验 |
| 委派决策 | ✅ | worker/handoff/subgraph 三种协作模式 |
| 升级处理 | ✅ | human/main-agent + 通知 |
| 优先级仲裁 | ✅ | severity×impact 矩阵 |
| Review 状态机 | ✅ | 6 状态 / 7 事件完整流转 |
| 文档写回 | ✅ | 原子写入 + section 级语义更新 |
| 审核编排 | ✅ | approve/reject/revision + 修订循环 |
| 外部反馈 | ✅ | FeedbackAPI (in-memory) |
| Worker 执行 | ✅ | LLM + HTTP + Stub |
| Pack 加载 | ✅ | manifest → context → rules |
| Pack 扩展件 | ✅ | validators/triggers 自动注册 |
| 审计追踪 | ✅ | 全链路 9 种事件 + Memory/File backend |
| 校验框架 | ✅ | Validator/Check/Trigger 3 Protocol |
| MCP 集成 | ✅ | 5 Tools + Prompts + Resources |
| 指令生成 | ✅ | PackContext → copilot-instructions.md |
| 断点持久化 | ✅ | checkpoint read/write/validate |
| CLI | ✅ | 5 个命令 |
| on_demand 加载 | ✅ | 懒读取 + 缓存 |

---

## 9. 已知技术债

1. **CURRENT.md 残留内容** — handoff 文件中残留了早期 Phase 22 的 Next Step Contract，应清理
2. **Phase Map 结论冗长** — 结论段落累积了所有 Phase 名称，可精简为引用 Phase 表
3. **Checklist 待办累积** — 当前待办区包含 Phase 4 以来的全部完成项，应归档
4. **测试 skip 原因** — 2 个 skipped 测试（可能是 LLM 真实调用相关），应标注原因
5. **instructions_generator 摘要算法** — `_summarize_content` 仅保留 heading+首行，对 flat 内容可能丢信息

---

## 10. 后续候选方向

| 方向 | 来源 | 优先级 | 说明 |
|------|------|--------|------|
| depends_on 校验 | gap analysis #11 | 低 | 单 pack 场景下无实际需求 |
| provides 消费 | gap analysis #5 | 低 | 需要 delegation capability check 驱动 |
| Dogfood 深度验证 | 自身使用反馈 | 中 | 实际开发中收集 MCP 工具优化需求 |
| 错误恢复 | research-compass | 中 | Pipeline 异常处理 + 重试策略 |
| Pack 分发 | plugin-model.md | 低 | 远程 pack registry |
| 持久化后端扩展 | 审计/检查点 | 低 | SQLite/Redis backend |
| CI/CD 集成 | project-adoption | 中 | pre-commit hook + GitHub Actions |
