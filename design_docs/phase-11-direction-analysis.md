# Phase 11 方向分析

## 现状总结

Phase 0-10 完成后的平台资产：

| 层 | 组件 | 状态 |
|----|------|------|
| 规格层 | 9 个 JSON Schema (draft-2020-12) | ✅ 完成 |
| PDP | 5 resolver (intent → gate → delegation → escalation → precedence) | ✅ 完成 |
| PEP | 委派管线 + Handoff 落地 + 升级路径 | ✅ 完成 |
| 接口层 | 4 个 Protocol (WorkerBackend, ContractFactory, ReportValidator, EscalationNotifier) | ✅ 完成 |
| 测试 | 93 项 pytest 通过 | ✅ 完成 |

**但仍缺失的核心能力：**

1. Worker 只有 Stub 实现——子 agent 无法做实际工作
2. Notifier 只有 Stub 实现——升级通知不能真正送达
3. Review 状态机只有 `waiting_review` → `applied`——缺少 `revised`, `rejected`, `approved` 等完整流转
4. Pack 运行时未实现——多 pack 覆盖关系无法执行

---

## 候选方向

### A. Real Worker Adapter

**是什么**：实现真正的 `WorkerBackend`，让子 agent 能做实际工作（LLM 调用 / subprocess / HTTP 委派）。

**新增文件**：`src/workers/` — `llm_worker.py`, `subprocess_worker.py` 等

**交付价值**：
- 平台从"决策引擎"升级为"可工作引擎"
- 验证 contract → report 管线在真实场景下的完整性
- 为未来对接各种 LLM/agent 平台奠定基础

**复杂度**：中——LLM/subprocess 集成直接，但需处理超时、重试、错误格式化

**前置条件**：WorkerBackend Protocol 已定义（Phase 8）；需要 LLM API key 或 subprocess 环境

**依赖**：独立，不依赖其他候选

---

### B. Review 状态机引擎

**是什么**：实现 `review-state-machine.md` 定义的 6 状态流转引擎（proposed → waiting_review → approved → rejected → revised → applied）。

**新增文件**：`src/review/` — `state_machine.py`, `state_store.py`

**交付价值**：
- 高影响决策有完整审批流（建议 → 审核 → 修改 → 重审 → 批准 → 执行）
- 每次状态迁移可审计
- Write-back 可挂在 `approved` 状态之后
- 支撑 governance-flow 预设的治理循环

**复杂度**：中——状态机逻辑简洁，但需处理持久化和并发

**前置条件**：review-state-machine.md 规范已定义

**依赖**：独立；但与 Notifier 组合可在状态变化时触发通知

---

### C. Real Notifier Adapter

**是什么**：实现真正的 `EscalationNotifier`，支持 email、webhook、console log 等通知通道。

**新增文件**：`src/notifiers/` — `email_notifier.py`, `webhook_notifier.py`, `console_notifier.py`

**交付价值**：
- 升级通知真正送达 human_reviewer
- 平台可进入生产使用
- 验证通知规范和传递链路

**复杂度**：中——各通道 API 不同但模式相同

**前置条件**：EscalationNotifier Protocol 已定义（Phase 10）；需要外部通知服务

**依赖**：独立；但与 Review 状态机组合价值更高

---

### D. Pack 运行时

**是什么**：实现 pack 装载引擎——解析 `pack-manifest.json`，加载 always-on 内容，按需加载 on-demand 内容，处理多 pack 的 override 仲裁。

**新增文件**：`src/pack/` — `manifest_loader.py`, `pack_resolver.py`, `context_builder.py`

**交付价值**：
- "文档即代码"的扩展机制真正可用
- 官方实例与项目 pack 即插即用
- 多 pack 覆盖关系自动仲裁
- 为未来云端分发铺路

**复杂度**：**高**——需处理 pack 依赖求解、循环引用检测、override 冲突仲裁

**前置条件**：Pack Manifest 规范已定义（Phase 5）；需先决定文件格式/存储模式

**依赖**：前置决策较多；建议在 A/B/C 之后

---

### E. Governance 端到端集成测试

**是什么**：编写完整 E2E 测试：input → PDP → PEP → 文档改写 → write-back → 通知 → 状态变化 → 验证。

**新增文件**：`tests/test_governance_e2e.py`

**交付价值**：
- 验证平台整体可闭环
- 早期发现架构缺陷
- 为后续开发提供目标基准

**复杂度**：中——组织已有组件联动

**前置条件**：PDP + PEP 已完成

**依赖**：可并行执行

---

### F. 阶段性总结文档

**是什么**：编写 Phase 0-10 回顾总结，记录设计决策、实现轨迹、教训学习。

**新增文件**：`docs/phase-retrospective.md`

**交付价值**：降低上手门槛，记录 "为什么这样做" 的决策上下文

**复杂度**：**低**——纯写作

**依赖**：完全独立

---

## 优先级矩阵

| 序号 | 选项 | 价值 | 复杂度 | 建议阶段 |
|------|------|------|--------|----------|
| B | Review 状态机引擎 | ★★★★ | 中 | Phase 11 |
| A | Real Worker Adapter | ★★★★ | 中 | Phase 12 |
| E | Governance E2E 测试 | ★★★ | 中 | Phase 11 并行 |
| C | Real Notifier Adapter | ★★★ | 中 | Phase 13 |
| D | Pack 运行时 | ★★★★★ | 高 | Phase 14 |
| F | 阶段性总结 | ★★ | 低 | 任何时候 |

**推荐依据**：Review 状态机是 governance 流程的核心缺失——当前"高影响决策"只能 queue for review，没有真正的审核流。实现它可以让 PEP 的 approve gate、delegation 的 requires_review、escalation 的 human_reviewer 路径全部正式闭环。
