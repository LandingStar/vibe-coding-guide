# Research Compass

## 文档定位

本文件是 `review/` 目录的牵头文档，用于快速检索当前研究资产。

它不是单个产品的详细研究，也不直接给出平台定稿；它负责：

- 提供全览
- 提供按问题检索入口
- 指出每份研究最值得参考的层
- 标记对子 agent 管理的相关性

若要看细节，请跳转到对应产品研究文档。

## 一页结论

当前研究可以先粗分成 5 组：

| 组别 | 代表产品 | 最强贡献 |
|---|---|---|
| 规则与决策 | OPA, Continue | precedence、rules、decision/enforcement 分层 |
| pack / skill / context | OpenHands, Continue, Semantic Kernel, **Claude Managed Agents** | pack 形态、always-on/on-demand、来源分层、**三级渐进加载** |
| 多 agent / 子 agent | LangGraph, AutoGen, CrewAI, OpenAI Agents SDK, Semantic Kernel, **Claude Managed Agents** | supervisor-worker、handoff、team 模式、review 节点、**单层委派+上下文隔离** |
| validator / quality control | Guardrails AI, Continue | validator registry、checks 分层、input/output guard |
| 文档 / 模板 / 平台形态 | Backstage, OpenHands, Continue | docs-like-code、templates、plugin architecture |
| 全托管 agent 运行时 | **Claude Managed Agents** | **事件驱动 session、permission policy 分层、Skills 渐进加载、structured outputs** |
| agent-as-teammate / 团队协作 | **Multica** | **Skills hash 锁定 + 远程来源、agent 任务分配生命周期、runtime 调度、知识持久化缺口与克制设计态度** |

## 全量研究地图

| 产品 | 主要关注层 | 最值得借鉴的点 | 子 agent 相关性 | 先读场景 |
|---|---|---|---|---|
| [Continue](./continue.md) | repo rules / checks / triggers | repo 内规则文件、checks vs agents、优先级链 | 低 | 想定义本地规则文件与检查体系时 |
| [OpenHands](./openhands.md) | skills / context / registry | always-on vs on-demand、项目/用户/组织/全局来源 | 中 | 想设计 pack 载入与上下文层次时 |
| [LangGraph / LangChain](./langgraph-langchain.md) | runtime / state / subgraph | interrupt、durable state、supervisor vs router、subgraph | 高 | 想设计 review 状态机和长流程 subagent 时 |
| [AutoGen](./autogen.md) | teams / handoff / lifecycle | handoff 原语、team 模式、human escalation | 高 | 想设计 handoff、team 与人类升级点时 |
| [CrewAI](./crewai.md) | manager-worker / flow / HITL | hierarchical manager、human feedback outcome、stateful flow | 高 | 想设计 manager 责任与 review 流转时 |
| [Open Policy Agent](./open-policy-agent.md) | policy engine | PDP/PEP、decision logs、structured decision | 中 | 想把规则系统与执行系统分开时 |
| [Guardrails AI](./guardrails-ai.md) | validator / guard | validator registry、input/output guard、template | 中 | 想设计 validator 生态时 |
| [Backstage](./backstage.md) | platform/plugin/docs/templates | docs-like-code、template review step、plugin architecture | 低 | 想设计平台本体与模板体系时 |
| [Dify](./dify.md) | triggers / event workflows | trigger plugin、webhook/subscription、多事件输入 | 低 | 想预留事件输入与触发器时 |
| [Semantic Kernel](./semantic-kernel.md) | plugin sources / orchestration patterns | OpenAPI/MCP plugin source、orchestration pattern 抽象 | 高 | 想扩展 pack 来源和协作模式时 |
| [OpenAI Agents SDK](./openai-agents-sdk.md) | handoff / tracing / guardrails | handoff 一等原语、guardrail 边界、tracing、tripwire | 高 | 想设计 handoff schema 与 tracing 时 |
| [Claude Managed Agents](./claude-managed-agents-platform.md) | skills / multi-agent / events / permissions | Skills 三级渐进加载、事件驱动 session、permission policy 分层覆盖、单层委派+上下文隔离 | 高 | 想设计 Pack 渐进加载、子 agent 上下文隔离、工具权限分层时 |
| [Multica](./multica/) | skills-lock / agent-as-teammate / runtime / knowledge-gap | Skills hash 锁定 + GitHub 来源、agent 任务生命周期、daemon runtime 调度、知识持久化缺口分析 | 中 | 想设计 pack 版本锁定、远程来源安装、子 agent 任务追踪、或知识管理策略对比时 |

> **Multica 深度研究**: [架构深潜](./multica/01-architecture-deep-dive.md) · [方向与不足](./multica/02-direction-and-weaknesses.md) · [借鉴洞察](../review/multica-borrowing/borrowing-insights.md)

## 按问题检索

### 如果你想看“规则核心 / 决策与执行分离”

优先读：

1. [Open Policy Agent](./open-policy-agent.md)
2. [Continue](./continue.md)

补充读：

3. [OpenAI Agents SDK](./openai-agents-sdk.md)

### 如果你想看“pack / skill / plugin 应该长什么样”

优先读：

1. [Claude Managed Agents](./claude-managed-agents-platform.md)（Skills 三级渐进加载）
2. [OpenHands](./openhands.md)
3. [Continue](./continue.md)
4. [Semantic Kernel](./semantic-kernel.md)

补充读：

5. [Backstage](./backstage.md)

### 如果你想看“always-on context 与按需加载”

优先读：

1. [Claude Managed Agents](./claude-managed-agents-platform.md)（Skills L1/L2/L3 三级加载）
2. [OpenHands](./openhands.md)

补充读：

3. [Continue](./continue.md)

### 如果你想看“子 agent 默认协作模式”

优先读：

1. [LangGraph / LangChain](./langgraph-langchain.md)
2. [CrewAI](./crewai.md)
3. [AutoGen](./autogen.md)
4. [Claude Managed Agents](./claude-managed-agents-platform.md)（单层委派 + 上下文隔离）

### 如果你想看“handoff 应否是显式原语”

优先读：

1. [OpenAI Agents SDK](./openai-agents-sdk.md)
2. [AutoGen](./autogen.md)

补充读：

3. [Semantic Kernel](./semantic-kernel.md)

### 如果你想看“review / approve / human feedback”

优先读：

1. [LangGraph / LangChain](./langgraph-langchain.md)
2. [CrewAI](./crewai.md)
3. [AutoGen](./autogen.md)

### 如果你想看“validator / checks / quality guard”

优先读：

1. [Guardrails AI](./guardrails-ai.md)
2. [Continue](./continue.md)

补充读：

3. [OpenAI Agents SDK](./openai-agents-sdk.md)

### 如果你想看“模板、脚手架与 docs-like-code”

优先读：

1. [Backstage](./backstage.md)
2. [OpenHands](./openhands.md)

### 如果你想看“事件输入 / trigger / webhook”

优先读：

1. [Dify](./dify.md)
2. [Continue](./continue.md)

### 如果你想看“tracing / 审计 / 可回放”

优先读：

1. [OpenAI Agents SDK](./openai-agents-sdk.md)
2. [Open Policy Agent](./open-policy-agent.md)
3. [LangGraph / LangChain](./langgraph-langchain.md)

## 按平台层检索

| 平台层 | 最相关研究 |
|---|---|
| 核心治理层 | [open-policy-agent.md](./open-policy-agent.md), [continue.md](./continue.md) |
| pack 扩展层 | [claude-managed-agents-platform.md](./claude-managed-agents-platform.md), [openhands.md](./openhands.md), [continue.md](./continue.md), [semantic-kernel.md](./semantic-kernel.md), [multica/](./multica/) |
| review / approval 层 | [langgraph-langchain.md](./langgraph-langchain.md), [crewai.md](./crewai.md), [autogen.md](./autogen.md) |
| subagent orchestration 层 | [langgraph-langchain.md](./langgraph-langchain.md), [autogen.md](./autogen.md), [crewai.md](./crewai.md), [openai-agents-sdk.md](./openai-agents-sdk.md), [semantic-kernel.md](./semantic-kernel.md), [claude-managed-agents-platform.md](./claude-managed-agents-platform.md), [multica/](./multica/) |
| validator / checks 层 | [guardrails-ai.md](./guardrails-ai.md), [continue.md](./continue.md) |
| docs / templates 层 | [backstage.md](./backstage.md), [openhands.md](./openhands.md) |
| triggers / event inputs 层 | [dify.md](./dify.md), [continue.md](./continue.md) |

## 子 agent 管理专门导航

如果后续只看子 agent 管理，建议阅读顺序：

1. [LangGraph / LangChain](./langgraph-langchain.md)
2. [OpenAI Agents SDK](./openai-agents-sdk.md)
3. [AutoGen](./autogen.md)
4. [CrewAI](./crewai.md)
5. [Semantic Kernel](./semantic-kernel.md)
6. [OpenHands](./openhands.md)

对应关注点：

- `LangGraph / LangChain`
  - supervisor vs router
  - subgraph / namespace / resume
- `OpenAI Agents SDK`
  - handoff 原语
  - tracing
  - guardrails 与 handoff 边界
- `AutoGen`
  - team 形态
  - handoff lifecycle
  - human escalation
- `CrewAI`
  - manager-worker
  - review 责任
  - structured human feedback
- `Semantic Kernel`
  - orchestration patterns
  - automation approval
- `OpenHands`
  - 子 agent 上下文装载策略

## 当前研究空白

当前仍明显不足的研究方向有：

- ~~版本化 pack manifest 规范~~ — 已落地：`manifest_version` 字段已加入 `PackManifest`，loader 支持版本感知加载（major 不匹配→拒绝，minor 不匹配→警告），详见 `docs/pack-manifest.md` §Schema Versioning
- ~~decision logs 的最小字段设计~~ — 已落地：`DecisionLogEntry` 19 字段 dataclass + `DecisionLogStore` JSON Lines 持久化 + Pipeline.process() 后处理聚合 + MCP `governance_decide()` 返回 `decision_log_entry` + `query_decision_logs()` 查询工具，详见 `design_docs/stages/planning-gate/2026-04-14-decision-logs-minimum-field-design.md`
- ~~子 agent tracing 如何与文档 write-back 对接~~ — 已落地：ExecutionResult 新增 trace_id/delegation_mode 字段 + WritebackEngine 发射 writeback_planned / artifact_changed audit event + Executor 发射 contract_generated / subagent_report_received / writeback_blocked_by_check + trace 链从 intent 到 artifact 全程可追踪，详见 `design_docs/stages/planning-gate/2026-04-14-subagent-tracing-writeback-linkage.md`
- ~~多实例共存时的冲突解决策略~~ — 已落地：`_deep_merge()` 冲突收集器（path/old_value/new_value/old_source/new_source）+ `PackContext.merge_conflicts` 字段 + `PrecedenceResolver` 同层 tie 标记 `tie_broken_by: insertion_order` + 同层冲突记录 + `Pipeline.info()` 条件暴露 merge_conflicts，详见 `design_docs/stages/planning-gate/2026-04-14-multi-instance-conflict-detection.md`
- ~~plugin distribution / marketplace 的演化路径~~ — 已分析：三阶段演化方案（A Pack Index Metadata / B 本地 Registry / C 远程 Marketplace），当前判断均不建议立即实现，等待 dogfood 分发需求信号，详见 `design_docs/plugin-distribution-marketplace-direction-analysis.md`

这些方向后续若继续研究，应在本文件补入口，而不是只把新报告追加到底部目录。
