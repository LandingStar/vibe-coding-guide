# Phase 12 — 方向分析文档

- Date: 2026-04-10
- 前序阶段: Phase 11 (Review 状态机引擎) CLOSED
- 测试基线: 129 passed, 1 skipped

## Phase 0–11 实现总览

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

**已完成的 5 项子 agent 机制需求** 全部关闭（Contract 生成、Worker 调用、Report 校验、Handoff 落地、升级路径）。

---

## 权威文档（docs/）中尚未实现的关键能力

1. **文档写回与工作流闭环**：PEP 能产生决策但无法落地到实际文档改写
2. **Review 流程的 rejected/revised 路径**：状态机支持但 PEP 无驱动逻辑
3. **升级通知真实传递**：仅 Stub 实现，无 email/webhook/Slack
4. **子 agent 实际执行**：仅 StubWorker，无 LLM/subprocess
5. **Pack 运行时与多层装载**：manifest schema 已定义但无加载/仲裁引擎
6. **规则库配置化**：规则仍硬编码在 resolver 代码中
7. **完整审计链**：ActionLog 有基本记录但缺完整 tracing

---

## 候选方向

### A. 文档写回 + 工作流闭环

**描述：** 实现从 PEP decision envelope 到真实文档改写的完整路径。扩展 PEP executor 支持 write-back 指令：解析改写目标、调用模板引擎生成内容（Markdown/JSON/YAML）、安全落地文件改写（含 validation + dry-run）、记录 write-back 历史。与 review state machine 的 `applied` 状态绑定——仅 `approved` 后触发写回。

**权威来源：** `docs/governance-flow.md`、`docs/core-model.md` (PEP 职责)

**新增文件预估：**
- `src/pep/writeback_engine.py` — 模板引擎与文件安全更新
- `tests/test_pep_writeback.py`

**依赖：** 独立，无前置依赖  
**风险：** 模板引擎复杂度（可从简单 string/Jinja2 开始）  
**优先级：** ⭐⭐⭐⭐⭐ 极高 — 打通"决策 → 执行 → 落地"最关键的一环

---

### B. Review 完整流程 + 真实通知系统

**描述：** 补完 Phase 11 状态机的 rejected/revised 驱动路径，并将 StubNotifier 替换为真实通知适配器。PEP 处理 rejection（降级/重提）和 revision（reviewer 反馈后的重新提交循环）。通知适配器支持 Email/Webhook/Console 多种通道，包含 decision context 与 reviewer action items。

**权威来源：** `docs/review-state-machine.md`、`docs/escalation-decision.md`

**新增文件预估：**
- `src/pep/notifiers/` — email_notifier.py, webhook_notifier.py
- `src/pep/review_orchestrator.py` — revision/rejection 流程驱动
- `tests/test_notifiers.py`

**依赖：** 主要独立；与 A 无硬依赖但可共享 executor 扩展  
**风险：** 外部服务配置（SMTP/webhook）、reviewer 反馈入口设计  
**优先级：** ⭐⭐⭐⭐⭐ 极高 — governance"打回修改"是核心能力

---

### C. 子 agent 实际执行能力（Real Worker Adapter）

**描述：** 将 StubWorkerBackend 替换为真实执行后端。支持三种 Worker 类型：LLM Worker（调用 OpenAI/Claude API，输入 contract task → 输出 report）、Subprocess Worker（执行本地脚本/二进制，沙箱隔离）、HTTP Worker（委派给外部 API endpoint）。含超时/重试/错误恢复策略和 report 自动生成。

**权威来源：** `docs/subagent-management.md`、`docs/subagent-schemas.md`

**新增文件预估：**
- `src/workers/` — llm_worker.py, subprocess_worker.py, worker_registry.py
- `tests/test_workers_*.py`

**依赖：** 依赖 A（write-back）才能完整闭环；LLM API 或本地模型配置  
**风险：** LLM 调用成本、subprocess 安全隔离  
**优先级：** ⭐⭐⭐⭐ 高

---

### D. Pack 运行时 — 多实例装载与冲突仲裁

**描述：** 实现 pack-manifest.md 和 plugin-model.md 定义的完整 pack 运行时。Parse manifest JSON、装载 `always_on` 内容到 PDP context、按需加载 `on_demand` 内容、处理三层 override（平台 → 实例 → 项目本地）、冲突检测与仲裁算法、capability 声明与依赖求解。

**权威来源：** `docs/pack-manifest.md`、`docs/plugin-model.md`、`docs/project-adoption.md`

**新增文件预估：**
- `src/pack/` — manifest_loader.py, pack_resolver.py, context_builder.py
- `tests/test_pack_runtime.py`

**依赖：** 前置决策多（override 算法、规则源格式）；可与其他方向独立测试  
**风险：** 复杂度最高；override 场景组合爆炸  
**优先级：** ⭐⭐⭐ 中高

---

### E. 官方实例与项目采用验证

**描述：** 对齐 `doc-loop-vibe-coding` 原型与平台权威文档，实现"一个真实项目如何采用此平台"的端到端流程。重新审视实例 SKILL.md/references、增强 bootstrap script（自动生成项目级 overlay pack + 初始化文档骨架）、完善 validate 脚本检查清单、创建样本采用案例。

**权威来源：** `docs/official-instance-doc-loop.md`、`docs/project-adoption.md`、`docs/current-prototype-status.md`

**依赖：** 文档对齐可独立；完整流程验证需要 A（write-back）+ D（pack runtime）  
**风险：** 可能发现平台文档遗漏需要回写  
**优先级：** ⭐⭐⭐ 中

---

### F. 治理全流程 E2E 测试 + 知识总结

**描述：** 编写完整 E2E 治理流程测试（自然语言 → intent → gate → delegation/escalation → state transition 完整路径）覆盖所有 gate level + intent 组合。同时编写阶段性回顾文档（Phase 0–11 设计决策、外部产品参考吸收点、权衡取舍、已知开放问题）。

**权威来源：** 所有 docs/ 文档的综合校验

**依赖：** 完全独立  
**风险：** 无技术风险，主要是工作量  
**优先级：** ⭐⭐ 低中

---

## 优先级矩阵

| 序号 | 方向 | 价值 | 复杂度 | 建议阶段 |
|------|------|------|--------|----------|
| **A** | 文档写回 + 工作流闭环 | ⭐⭐⭐⭐⭐ | 中 | Phase 12 首选 |
| **B** | Review 完整流程 + 真实通知 | ⭐⭐⭐⭐⭐ | 中 | Phase 12 或 13 |
| **C** | Real Worker Adapter | ⭐⭐⭐⭐ | 中 | Phase 13 |
| **D** | Pack 运行时 | ⭐⭐⭐ | 高 | Phase 13-14 |
| **E** | 官方实例对齐 | ⭐⭐⭐ | 中 | Phase 12-13 并行 |
| **F** | E2E 测试 + 知识总结 | ⭐⭐ | 低 | 任何时候 |

**推荐：** A（文档写回）为 Phase 12 首选——它解锁"决策落地"能力，是平台从"决策机"升级为"工作流完成机"的关键。B（Review 完整流程）和 C（Real Worker）为紧随其后的高优先级候选。
