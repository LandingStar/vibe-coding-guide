# Phase 15 — 方向分析文档

- Date: 2026-04-10
- 前序阶段: Phase 14 (Write-Back 语义文档更新 + E2E 治理测试) CLOSED
- 测试基线: 228 passed, 1 skipped

## Phase 0–14 实现总览

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
| 14 | Markdown 语义更新 + E2E 治理测试 + FeedbackAPI | 228 |

**已完成的核心闭环：** 自然语言 → 意图分类 → 门控 → 委派/升级 → 审阅（approve/reject/revision）→ 写回落地 → 外部反馈入口。5 条治理路径 E2E 验证通过。

---

## 剩余关键缺口

### 缺口 1：规则全部硬编码，无配置化运行时
- 12 种 intent + keyword 硬编码在 `intent_classifier.py`
- gate / delegation / escalation 规则硬编码在各个 resolver
- 无 pack manifest 加载器和三层 override 仲裁
- 平台无法被不同实例/项目定制

### 缺口 2：子 agent 只有 Stub，无真实执行
- StubWorkerBackend 仅返回合成 report
- 无 LLM / subprocess / HTTP worker

### 缺口 3：官方实例未经端到端验证
- `doc-loop-vibe-coding/` 原型的 bootstrap/validate 脚本未适配平台 v1

---

## 候选方向

### A. Pack 运行时 — 规则配置化与多层装载

**描述：** 实现 `docs/pack-manifest.md` 和 `docs/plugin-model.md` 定义的完整 pack 运行时。解析 manifest JSON → 装载 always_on 内容至 PDP context → 三层 override（平台 → 实例 → 项目本地）。classifier 和 resolver 改为从 pack 配置读取规则。

**权威来源：** `docs/pack-manifest.md`、`docs/plugin-model.md`、`docs/project-adoption.md`

**新增文件预估：**
- `src/pack/manifest_loader.py` — JSON manifest 解析与校验
- `src/pack/context_builder.py` — always_on / on_demand 上下文装载
- `src/pack/override_resolver.py` — 三层 override 冲突仲裁
- `src/pdp/configurable_classifier.py` — 从 pack 配置读取规则
- `tests/test_pack_runtime.py`

**收益：** 解锁实例级可扩展性，规则不再硬编码  
**风险：** 三层 override 组合复杂，需先确定外部规则格式  
**复杂度：** ⭐⭐⭐⭐ 高  
**优先级：** ⭐⭐⭐⭐ 极高

---

### B. 子 Agent 真实执行能力（Real Worker Adapter）

**描述：** 将 StubWorkerBackend 替换为真实执行后端。LLM Worker（调用 OpenAI/Claude API）：接收 contract → 生成 prompt → 调用 LLM → 构造 report。可选扩展 HTTP Worker（外部 API endpoint）。

**权威来源：** `docs/subagent-management.md`、`docs/subagent-schemas.md`

**新增文件预估：**
- `src/workers/llm_worker.py` — LLM API + contract→prompt
- `src/workers/http_worker.py` — 外部 API 委派
- `src/workers/worker_registry.py` — 按 type 分发
- `tests/test_workers.py`

**收益：** 平台从"决策引擎"升级为"执行引擎"  
**风险：** LLM API 成本、需 API key  
**复杂度：** ⭐⭐⭐ 中  
**优先级：** ⭐⭐⭐⭐ 极高

---

### C. 官方实例（doc-loop-vibe-coding）端到端验证

**描述：** 审计 `doc-loop-vibe-coding/` 原型与平台权威文档对齐度。更新 bootstrap/validate 脚本。在测试项目上运行完整采用流程。

**权威来源：** `docs/official-instance-doc-loop.md`、`docs/project-adoption.md`

**收益：** 验证平台从权威到实例到项目的完整链路  
**风险：** 可能发现平台文档缺口需要回写  
**复杂度：** ⭐⭐ 低中  
**优先级：** ⭐⭐⭐ 中高 — 完整验证依赖 A（Pack 运行时）

---

## 优先级矩阵

| 序号 | 方向 | 价值 | 复杂度 | 前置依赖 |
|------|------|------|--------|----------|
| **A** | Pack 运行时 | ⭐⭐⭐⭐ | 高 | 独立 |
| **B** | Real Worker | ⭐⭐⭐⭐ | 中 | 独立 |
| **C** | 官方实例验证 | ⭐⭐⭐ | 低中 | 依赖 A |

## 建议

- **A 是唯一不可跳过的方向** — 不做 Pack 运行时，平台永远只有一种硬编码配置，无法被任何实例/项目定制。
- **B 可独立或后续追加** — LLM Worker 让平台能真正执行任务，但不阻塞治理流程。
- **A→C** 是自然的验证链：配置化 → 实例对齐验证。
- **A→B** 是功能链：配置化 → 真实执行。

请选择 Phase 15 方向。
