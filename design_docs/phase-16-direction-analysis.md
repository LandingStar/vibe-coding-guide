# Phase 16 方向分析

- Date: 2026-04-10
- Baseline: 253 passed, 1 skipped (Phase 15 complete)

## 当前平台能力总览

Phase 0–15 已完成：
- 9 个 JSON Schema + PDP 完整决策链（5 个 resolver）
- PEP 完整执行管线：委派 → worker → report → 校验 → review 状态机 → 写回
- Review 状态机（6 状态 / 7 事件 / 8 条迁移规则）+ ReviewOrchestrator
- Markdown 语义更新 + Directive Engine
- FeedbackAPI 外部 reviewer 入口
- 3 种通知适配器（Console / File / Webhook）
- 真实 Worker 后端（LLMWorker + HTTPWorker）+ WorkerRegistry

## 候选方向

### A. Pack 运行时加载器 ⭐⭐⭐⭐ 最高优先级

**问题**：当前所有规则（intent 映射、gate 阈值、delegation 条件、escalation 策略）均硬编码在代码中。`docs/pack-manifest.md` 和 `docs/plugin-model.md` 描述的 3 层配置覆盖机制（platform → instance → project-local）完全未实现。

**范围**：
- 创建 `src/pack/` 包：
  - `manifest_loader.py`：解析 pack-manifest.json
  - `context_builder.py`：加载 `always_on` 内容 + 构建上下文 dict
  - `override_resolver.py`：3 层规则优先级覆盖
- 重构各 resolver 从 pack 上下文读取规则（保持向后兼容）
- 测试多层 override 场景

**价值**：解锁平台可扩展性、真正的插件化架构。是官方实例验证（E）的前提。
**复杂度**：高
**依赖**：无

---

### B. 审计与追溯系统 ⭐⭐⭐ 高优先级

**问题**：当前只有 `ActionLog`（方法级别记录）和 Review 状态机的审计历史。缺乏跨决策链的完整追溯——从输入到 PDP 决策到 gate 触发到委派到写回的全链路 trace。`docs/core-model.md` 和 `docs/governance-flow.md` 均要求 "必须支持最小 tracing / audit 能力"。

**范围**：
- 创建 `src/audit/` 包：
  - `audit_logger.py`：中心审计记录器
  - `trace_builder.py`：correlation ID、trace span
- 在 PDP 各 resolver、PEP executor、review_orchestrator、writeback_engine 中插入审计点
- 持久化审计日志（JSON 文件 / 可插拔后端）
- Envelope 扩展 `trace_id` 字段

**价值**：治理问责、调试可见性、合规需求。
**复杂度**：中高
**依赖**：无

---

### C. 输入层抽象 ⭐⭐⭐ 中高优先级

**问题**：当前 PDP 只接受自然语言字符串输入。`docs/governance-flow.md` 定义输入层应支持"自然语言聊天、issue、PR、CI failure、webhook、schedule"等多种来源。

**范围**：
- 定义 `InputSource` Protocol
- 实现输入处理器：NaturalLanguageInput / IssueInput / PRInput / WebhookInput
- 实现 `InputDispatcher` 路由
- 重构 intent_classifier 接受结构化输入

**价值**：DevOps / CI 管线集成。
**复杂度**：中高
**依赖**：无

---

### D. 校验器 / 检查 / 触发器框架 ⭐⭐ 中优先级

**问题**：Pack manifest 中定义的 `validators` / `checks` / `scripts` / `triggers` 字段完全未对接执行。当前仅 `report_validator.py` 做 JSON Schema 校验。

**范围**：
- 定义 Validator / Check / Script / Trigger Protocol
- 实现注册表和执行器
- 在 report 提交、写回前、状态迁移处调用校验器

**价值**：Pack 可强制执行自定义规则/智能防护。
**复杂度**：中
**依赖**：最佳与 A（Pack Runtime）配合

---

### E. 官方实例端到端验证 ⭐⭐ 中优先级

**问题**：`doc-loop-vibe-coding/` 作为官方实例存在 pack-manifest.json 和模板，但从未与平台 v1 进行过端到端集成测试。bootstrap 脚本尚未对接 pack loader。

**范围**：
- 创建测试项目 `example/test-project/`
- 使用 bootstrap 脚本搭建完整 doc-loop 结构
- 创建 E2E 测试："采纳官方实例 pack → 加载上下文 → 执行 5 条治理路径"

**价值**：验证 platform ↔ instance ↔ project 采纳链。
**复杂度**：中低
**依赖**：强依赖 A（Pack Runtime）

---

### F. Email & Slack 通知 ⭐ 低优先级

**范围**：增加 EmailNotifier（SMTP）和 SlackNotifier 适配器。
**价值**：更丰富的升级通知渠道。
**复杂度**：低

## 建议路径

- **A → E**：先实现 Pack Runtime 解锁配置化，再验证官方实例端到端
- **A → B**：先 Pack Runtime 再审计系统（两者相对独立，但审计点需覆盖 pack 加载）
- **B 独立**：如果优先合规/可观测性，可先做审计
