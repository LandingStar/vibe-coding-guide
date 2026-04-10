# Phase 14 — 方向分析文档

- Date: 2026-04-10
- 前序阶段: Phase 13 (Review 完整流程 + 真实通知) CLOSED
- 测试基线: 183 passed, 1 skipped

## Phase 0–13 实现总览

| Phase | 成果 | 测试 |
|-------|------|------|
| 0–3 | 平台权威文档、repo-local adoption、原型 rereview | — |
| 4 | 5 个决策类型 JSON Schema (draft-2020-12) | — |
| 5 | 3 个子 agent Schema (Contract/Report/Handoff) | — |
| 6 | PDP 核心 + PEP 执行骨架 | 25 |
| 7 | 完整决策链 (delegation/escalation/precedence) | 47 |
| 8 | PEP+Subagent 接口 (依赖反转 + Protocol) | 71 |
| 9 | Handoff 落地与持久化 | 85 |
| 10 | 升级路径执行与通知 | 93 |
| 11 | Review 状态机引擎 + PEP 集成 | 129 |
| 12 | WritebackEngine + 工作流闭环 | 155 |
| 13 | Notifier 适配器 + ReviewOrchestrator | 183 |

---

## 权威文档（docs/）中仍存在的关键缺口

### 缺口 1：规则全部硬编码，无配置化加载

| 文件 | 缺口 | 影响 |
|------|------|------|
| `docs/pack-manifest.md` | Pack manifest 仅有 schema，无运行时加载器 | 🔴 多实例/多 pack 支持完全阻塞 |
| `docs/plugin-model.md` | always-on / on-demand 上下文加载未实现 | 🔴 实例 overlay 不可用 |
| `docs/intent-classification.md` | 12 种 intent 硬编码在 classifier，实例无法扩展 | 🟡 可扩展性阻塞 |
| `docs/gate-decision.md` | gate 规则硬编码在 resolver | 🟡 同上 |

### 缺口 2：子 agent 只有 Stub，无真实执行

| 文件 | 缺口 | 影响 |
|------|------|------|
| `docs/subagent-management.md` | 仅 StubWorkerBackend，无 LLM/进程/HTTP 执行 | 🔴 平台无法真正执行任务 |
| `docs/subagent-schemas.md` | 无错误恢复/重试/超时策略 | 🟡 生产可靠性缺失 |

### 缺口 3：WritebackEngine 只生成摘要文件，无语义文档更新

| 文件 | 缺口 | 影响 |
|------|------|------|
| `docs/governance-flow.md` Step 7 | plan() 仅输出通用 .md 摘要 | 🔴 无法更新真实文档内容 |
| `docs/core-model.md` | "起草、修改、整合和回写文档"未实现 | 🟡 write-back 名不符实 |

### 缺口 4：Reviewer 反馈缺少外部入口

- `ReviewOrchestrator` 逻辑完整但仅能通过 Python 内部调用
- 无 CLI / REST / 事件入口供外部 reviewer 使用

---

## 候选方向

### A. Pack 运行时 — 规则配置化与多层装载

**描述：** 实现 `docs/pack-manifest.md` 和 `docs/plugin-model.md` 定义的完整 pack 运行时。解析 manifest JSON → 装载 `always_on` 内容至 PDP context → 按需加载 `on_demand` 内容 → 三层 override（平台 → 实例 → 项目本地）覆盖与冲突仲裁。classifier 和 resolver 改为从 pack 配置读取规则，不再硬编码。

**权威来源：** `docs/pack-manifest.md`、`docs/plugin-model.md`、`docs/project-adoption.md`

**新增文件预估：**
- `src/pack/manifest_loader.py` — JSON manifest 解析与校验
- `src/pack/context_builder.py` — always_on / on_demand 上下文装载
- `src/pack/override_resolver.py` — 三层 override 冲突仲裁
- `src/pdp/configurable_classifier.py` — 从 pack 配置读取 intent/keyword/impact
- `tests/test_pack_runtime.py`

**收益：**
- 解锁实例级可扩展性（自定义 intent、gate 规则、委派策略）
- 规则不再硬编码，支持多 pack 叠加与冲突检测
- 为"官方实例 E2E 验证"铺路

**风险：** 三层 override 组合爆炸、格式决策（JSON vs YAML vs Python DSL）、需先确定 pack 配置源格式  
**复杂度：** ⭐⭐⭐⭐ 高  
**优先级：** ⭐⭐⭐⭐ 极高 — 不做此项，平台永远只是单一硬编码配置

---

### B. 子 Agent 真实执行能力（Real Worker Adapter）

**描述：** 将 StubWorkerBackend 替换为真实执行后端。首选 LLM Worker（调用 OpenAI/Claude API）：接收 contract 任务描述 → 生成 prompt → 调用 LLM → 解析输出 → 构造 report。可选扩展 Subprocess Worker（本地脚本执行，沙箱隔离）和 HTTP Worker（外部 API endpoint 委派）。含超时/重试/错误恢复策略。

**权威来源：** `docs/subagent-management.md`、`docs/subagent-schemas.md`

**新增文件预估：**
- `src/workers/llm_worker.py` — LLM API 调用 + contract→prompt 翻译
- `src/workers/subprocess_worker.py` — 沙箱化本地执行
- `src/workers/http_worker.py` — 外部 API 委派
- `src/workers/worker_registry.py` — 按 worker_type 分发
- `tests/test_workers.py`

**收益：**
- 平台从"决策引擎"升级为"执行引擎"
- LLM Worker 是最直接的价值点——contract→LLM→report 自动完成
- Protocol 接口已在 Phase 8 定义，集成代价低

**风险：** LLM API 成本与速率限制、subprocess 安全隔离、需 API key 配置  
**复杂度：** ⭐⭐⭐ 中  
**优先级：** ⭐⭐⭐⭐ 极高 — 平台无此项则无法真正"工作"

---

### C. Write-Back 增强 — 语义文档更新

**描述：** 增强 WritebackEngine 从"生成摘要文件"升级为"操作真实文档"。定义 write-back directive schema（JSON），指定目标文件、操作类型（section-replace / section-append / line-insert / full-rewrite）、匹配策略（heading / line-pattern / anchor marker）、内容模板。实现 Markdown section 级别的更新（如自动更新 checklist 中某行状态）。

**权威来源：** `docs/governance-flow.md`（Step 7）、`docs/core-model.md`

**新增文件预估：**
- `docs/specs/writeback-directive.schema.json` — 指令格式
- `src/pep/writeback_directives.py` — directive 解析器
- `src/pep/markdown_updater.py` — Markdown section 定位与更新
- `tests/test_writeback_directives.py`

**收益：**
- write-back 从形式化变为实用化
- 可自动更新 Checklist、Phase Map 等设计文档
- 为 E2E 治理闭环补上"落地"最后一环

**风险：** Markdown 解析复杂度（需处理多级 heading / 嵌套 list）、merge 冲突  
**复杂度：** ⭐⭐⭐ 中  
**优先级：** ⭐⭐⭐⭐⭐ 极高 — 目前 write-back 名存实亡，需补全

---

### D. 治理全流程 E2E 测试 + Reviewer 外部入口

**描述：** 两部分合一：(1) 编写覆盖所有 gate level + intent 组合的 E2E 治理流程测试（自然语言 → intent → gate → delegation/escalation → review → feedback → revision → writeback 完整路径）。(2) 创建最小 Reviewer 入口 — 一个 CLI 命令或简单模块，供主 agent/用户向 waiting_review 的 envelope 提交 approve/reject/revision feedback。

**权威来源：** 所有 `docs/` 文档综合校验

**新增文件预估：**
- `tests/test_governance_e2e.py` — 全路径 E2E 测试
- `src/review/feedback_api.py` — 外部反馈提交入口
- `tests/test_feedback_api.py`

**收益：**
- 验证所有路径端到端可用
- 为 reviewer（人或 agent）提供可调用入口
- 文档信心来源——用测试证明 docs/ 与 src/ 一致

**风险：** 无技术风险  
**复杂度：** ⭐⭐ 低中  
**优先级：** ⭐⭐⭐ 高

---

### E. 官方实例（doc-loop-vibe-coding）E2E 采用验证

**描述：** 对齐 `doc-loop-vibe-coding/` 原型与平台权威文档。审计实例 manifest、更新 bootstrap/validate 脚本适配平台 v1 运行时、在测试项目上跑完整采用流程。验证 `docs/project-adoption.md` 中描述的"三层叠加"是否可用。

**权威来源：** `docs/official-instance-doc-loop.md`、`docs/project-adoption.md`

**收益：** 验证平台从权威到实例到项目的完整链路  
**风险：** 可能发现平台文档缺口，需要回写  
**复杂度：** ⭐⭐ 低中  
**优先级：** ⭐⭐⭐ 中高 — 但依赖 A（Pack 运行时）才能真正端到端

---

## 优先级矩阵

| 序号 | 方向 | 价值 | 复杂度 | 前置依赖 |
|------|------|------|--------|----------|
| **A** | Pack 运行时（规则配置化） | ⭐⭐⭐⭐ | 高 | 需先确定 pack 配置源格式 |
| **B** | Real Worker Adapter | ⭐⭐⭐⭐ | 中 | 独立，无前置 |
| **C** | Write-Back 语义文档更新 | ⭐⭐⭐⭐⭐ | 中 | 独立，无前置 |
| **D** | E2E 测试 + Reviewer 入口 | ⭐⭐⭐ | 低中 | 独立 |
| **E** | 官方实例采用验证 | ⭐⭐⭐ | 低中 | 依赖 A（Pack 运行时） |

## 建议

**可组合方案：**
- **方案 1 (C→D)：** 先 Write-Back 增强（最高价值/复杂度比），再 E2E 测试 + Reviewer 入口。打通"决策→落地→验证→反馈"完整内环。
- **方案 2 (B→D)：** 先 Real Worker（让平台真正能执行任务），再 E2E 验证完整链路。
- **方案 3 (A→E)：** 先 Pack 运行时（配置化），再官方实例验证（三层叠加端到端）。这是"平台可扩展性"方向。
- **选单项：** 任何一个方向均可独立启动（E 除外，它完整验证依赖 A）。

请选择 Phase 14 方向。
