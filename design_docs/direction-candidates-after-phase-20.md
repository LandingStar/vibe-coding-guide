# Phase 20 后候选方向

- 状态：**WAITING_USER_REVIEW**
- 日期：2026-04-10
- 前置：Phase 0–20 全部完成，414 项 pytest 通过

## 文档定位

本文件列出 Phase 20 完成后的**全部**候选方向，每个候选项附带权威来源引用与预估范围。

用户应选择下一个方向（或组合），AI 不得单方面决定。

---

## 第一梯队：紧急 / 平台治理基础缺口

### 1. Checkpoint 持久化机制落地
- **内容**：创建 `.codex/checkpoints/`，实现 checkpoint 读写逻辑，集成到 Document-Driven Workflow Standard
- **来源**：[design_docs/context-persistence-design.md](../context-persistence-design.md)（步骤 4/5/6 均标记"待实施"）
- **范围**：Small

### 2. 候选方向文档化模板
- **内容**：创建 `direction-candidates-phase-<N>.md` 模板，使方向选择可复用、压缩后可恢复
- **来源**：[design_docs/context-persistence-design.md](../context-persistence-design.md)（C.3 节）
- **范围**：Small

### 3. Human Classification Correction Runtime
- **内容**：intent classification 纠偏 API——人可纠正分类，高影响分类不能无保护生效
- **来源**：[docs/core-model.md](../../docs/core-model.md)（分类可纠正要求），[docs/governance-flow.md](../../docs/governance-flow.md)（Intent Classification 最低要求）
- **范围**：Small

---

## 第二梯队：Pack 能力补全

### 4. Pack `prompts` 字段消费
- **内容**：manifest `prompts` 已定义但 runtime 未消费，需 ContextBuilder/PEP 加载 pack 声明的 prompt
- **来源**：[docs/pack-manifest.md](../../docs/pack-manifest.md)，[docs/plugin-model.md](../../docs/plugin-model.md)
- **范围**：Small

### 5. Pack `scripts` 字段消费
- **内容**：manifest `scripts` 已定义未消费，需实现脚本注册与执行
- **来源**：[docs/pack-manifest.md](../../docs/pack-manifest.md)
- **范围**：Small

### 6. Pack `templates` 字段消费 + 模板系统
- **内容**：模板加载、scaffold 生成
- **来源**：[docs/pack-manifest.md](../../docs/pack-manifest.md)，[review/backstage.md](../../review/backstage.md)（docs-like-code 借鉴）
- **范围**：Medium

### 7. Pack `depends_on` 依赖解析
- **内容**：依赖检查、缺失报告、partial-work 策略
- **来源**：[docs/pack-manifest.md](../../docs/pack-manifest.md)（depends_on 设计原则）
- **范围**：Small–Medium

### 8. Pack `overrides` 冲突检测
- **内容**：多 pack 同时命中时的冲突检测与回退到人工 review
- **来源**：[docs/plugin-model.md](../../docs/plugin-model.md)（覆盖与优先级），[docs/pack-manifest.md](../../docs/pack-manifest.md)
- **范围**：Medium

---

## 第三梯队：协作模式与子 Agent 进化

### 9. Team 协作模式
- **内容**：多 agent 并行/竞争方案
- **来源**：[docs/subagent-management.md](../../docs/subagent-management.md)（非默认模式），[review/autogen.md](../../review/autogen.md)（team 形态），[review/crewai.md](../../review/crewai.md)
- **范围**：Medium

### 10. Swarm 协作模式
- **内容**：去中心化自组织任务分配
- **来源**：[docs/subagent-management.md](../../docs/subagent-management.md)，[review/openai-agents-sdk.md](../../review/openai-agents-sdk.md)
- **范围**：Medium

### 11. Supervisor 一等对象
- **内容**：core-model 定义但 src/ 中无数据结构
- **来源**：[docs/core-model.md](../../docs/core-model.md)（Subagent Core Objects）
- **范围**：Small

### 12. Artifact Ownership 运行时强制
- **内容**：子 agent 不应维护平台权威文档的运行时校验
- **来源**：[docs/subagent-management.md](../../docs/subagent-management.md)（Artifact Ownership）
- **范围**：Small

### 13. 子 Agent 上下文装载差异化
- **内容**：主 agent 装 always-on context，子 agent 只装合同 refs
- **来源**：[docs/subagent-management.md](../../docs/subagent-management.md)（Context Loading），[review/openhands.md](../../review/openhands.md)
- **范围**：Medium

---

## 第四梯队：输入层与外部接口

### 14. 多输入类型支持（Input Layer）
- **内容**：issue / PR / CI failure / webhook / schedule 输入适配器
- **来源**：[docs/governance-flow.md](../../docs/governance-flow.md)（输入层），[docs/plugin-model.md](../../docs/plugin-model.md)（Pack And Triggers），[review/dify.md](../../review/dify.md)
- **范围**：Large

### 15. CLI / 外部入口层
- **内容**：命令行或 API server 作为真实使用入口
- **来源**：[docs/platform-positioning.md](../../docs/platform-positioning.md)，[docs/project-adoption.md](../../docs/project-adoption.md)
- **范围**：Medium

### 16. Trigger Plugin 系统
- **内容**：真实 trigger 插件（webhook listener、schedule cron、CI event adapter）
- **来源**：[docs/plugin-model.md](../../docs/plugin-model.md)（Pack And Triggers），[review/dify.md](../../review/dify.md)
- **范围**：Medium–Large

---

## 第五梯队：审计 / Review 进化

### 17. Decision Logs 最小字段设计
- **内容**：专用 decision log 数据结构（区别于通用 AuditEvent）
- **来源**：[review/research-compass.md](../../review/research-compass.md)（研究空白），[review/open-policy-agent.md](../../review/open-policy-agent.md)
- **范围**：Small–Medium

### 18. FileAuditBackend 查询与回放
- **内容**：文件级查询、按 trace_id 过滤、审计回放
- **来源**：[review/openai-agents-sdk.md](../../review/openai-agents-sdk.md)（tracing 回放），[docs/governance-flow.md](../../docs/governance-flow.md)
- **范围**：Small–Medium

### 19. 子 Agent Tracing 与 Write-Back 对接
- **内容**：audit 与 writeback 关联追溯
- **来源**：[review/research-compass.md](../../review/research-compass.md)（研究空白）
- **范围**：Medium

### 20. Review 状态机扩展（cancelled / superseded）
- **内容**：review-state-machine.md 列出的开放扩展点
- **来源**：[docs/review-state-machine.md](../../docs/review-state-machine.md)
- **范围**：Small

### 21. Revised 历史版本链
- **内容**：revised 是否保留历史版本链
- **来源**：[docs/review-state-machine.md](../../docs/review-state-machine.md)（开放问题）
- **范围**：Small–Medium

---

## 第六梯队：平台扩展与长期演进

### 22. Rule 一等对象实现
- **内容**：独立 Rule 对象、注册表、运行时评估引擎
- **来源**：[docs/core-model.md](../../docs/core-model.md)（Rule 定义），[review/open-policy-agent.md](../../review/open-policy-agent.md)
- **范围**：Medium–Large

### 23. Document Type 运行时强制
- **内容**：校验 artifact 是否属于已声明文档类型
- **来源**：[docs/plugin-model.md](../../docs/plugin-model.md)，[docs/core-model.md](../../docs/core-model.md)
- **范围**：Small–Medium

### 24. Pack Origins 多层级
- **内容**：user-level、organization-level、remote registry
- **来源**：[docs/plugin-model.md](../../docs/plugin-model.md)（Pack Origins），[review/openhands.md](../../review/openhands.md)
- **范围**：Medium–Large

### 25. Pack 来源扩展（OpenAPI / MCP）
- **内容**：预留 OpenAPI specification、MCP server 等 pack 来源
- **来源**：[docs/plugin-model.md](../../docs/plugin-model.md)（Pack Sources），[review/semantic-kernel.md](../../review/semantic-kernel.md)
- **范围**：Large

### 26. LangGraph 式 Durable State / Interrupt-Resume
- **内容**：PEP executor 长流程中断恢复
- **来源**：[review/langgraph-langchain.md](../../review/langgraph-langchain.md)，[design_docs/context-persistence-design.md](../context-persistence-design.md)
- **范围**：Large

### 27. 多实例共存冲突解决
- **内容**：多实例共存时的冲突解决策略
- **来源**：[review/research-compass.md](../../review/research-compass.md)（研究空白）
- **范围**：Medium

### 28. 版本化 Pack Manifest 规范
- **内容**：版本兼容性检查、变更迁移
- **来源**：[review/research-compass.md](../../review/research-compass.md)（研究空白）
- **范围**：Small–Medium

### 29. 官方实例 Prototype 复审收口
- **内容**：原型规则上升平台 vs 属于实例的分界
- **来源**：[docs/current-prototype-status.md](../../docs/current-prototype-status.md)，[docs/official-instance-doc-loop.md](../../docs/official-instance-doc-loop.md)
- **范围**：Medium

### 30. Project Adoption 自动化 Bootstrap
- **内容**：bootstrap 集成到 runtime（CLI 或 PEP 动作）
- **来源**：[docs/project-adoption.md](../../docs/project-adoption.md)（最小采用路径）
- **范围**：Medium

### 31. Plugin Distribution / Marketplace
- **内容**：远端分发协议、安装发布流程、签名校验
- **来源**：[review/research-compass.md](../../review/research-compass.md)，[docs/pack-manifest.md](../../docs/pack-manifest.md)
- **范围**：Large

### 32. Inform 快速路径最小 Reviewer 可见性
- **内容**：inform 快速路径是否需最小可见性
- **来源**：[docs/review-state-machine.md](../../docs/review-state-machine.md)
- **范围**：Small
