# Claude Managed Agents Platform — 研究分析

> 来源：https://platform.claude.com/docs/  
> 分析日期：2026-04-16  
> 分析目标：从 doc-based-coding-platform 视角，提取可借鉴的架构模式与设计决策

## 一句话定位

Anthropic 的 Managed Agents 是一套**全托管、有状态、事件驱动**的 agent 运行时，提供 Agent → Environment → Session → Events 四层抽象，原生支持 custom tools、MCP servers、Skills（渐进式领域知识加载）和多 agent 编排。

---

## 关键架构概念

### 1. Agent / Environment / Session 三层分离

| 概念 | 职责 | 生命周期 |
|---|---|---|
| **Agent** | 可复用配置：model + system prompt + tools + MCP servers + skills + callable_agents | 版本化，可 archive |
| **Environment** | 文件系统 / 沙箱 / 运行时环境 | 独立于 session |
| **Session** | Agent 在 Environment 内的一次运行实例，保持跨 turn 会话历史 | idle → running → idle → terminated |

**对我们的启发**：我们当前的 subagent 设计只有"dispatch a worker → get report"的一次性调用模式。Claude 的三层分离说明 agent 配置（相当于我们的 Pack）、执行环境（相当于我们的 worker process context）与会话状态（相当于我们的 subagent report 链）应当是独立可组合的关注点。

### 2. 事件驱动会话模型

Session 是一个**状态机**，由事件驱动：

- **User events**: `user.message`, `user.interrupt`, `user.custom_tool_result`, `user.tool_confirmation`, `user.define_outcome`
- **Agent events**: `agent.custom_tool_use`, `agent.tool_use`, `agent.mcp_tool_use`
- **Session events**: `session.status_idle` (with `stop_reason: end_turn | requires_action`)

关键模式：
- Session **暂停等待** custom tool 结果 → 外部系统执行 → 把结果回传 → session 恢复
- `requires_action` + `event_ids` 机制支持**多个并行 tool call** 同时等待确认
- `user.interrupt` 可以中断正在执行的 agent 并重定向

**对我们的启发**：
- 我们的 `governance_decide` / `check_constraints` 本质上就是 session 暂停等待治理决策的模式。Claude 的显式 `requires_action` + event ID 匹配比我们当前的同步调用更灵活。
- `user.interrupt` 对应我们在 planning-gate 中"发现超出 scope 的问题时回退"的需求 — 可以考虑在 workflow 引擎层显式化这个中断原语。
- `user.define_outcome` 是一个我们没有的概念：在运行时定义期望结果，让 agent 朝目标工作。这比我们当前的 system prompt + pack 配置更动态。

### 3. Permission Policies — 工具执行权控制

两种策略：
- `always_allow`：工具自动执行
- `always_ask`：session 暂停，等待 `user.tool_confirmation` (allow/deny + deny_message)

可在 toolset 级别设置默认，也可在单个工具级别 override。

**对我们的启发**：这与我们的 PDP/PEP 治理模型高度对齐。Claude 的 permission policy 是我们 `governance_decide` 的工具粒度版本。我们可以借鉴：
- **分层覆盖**：pack 级默认 + 单 tool 级 override
- **deny_message**：拒绝时附带理由，让 agent 可以理解并调整策略

### 4. Custom Tools — 外部能力扩展

定义：agent 配置中声明 tool name + description + input_schema → agent 调用时 session 暂停 → 你的代码执行 → 把结果发回。

最佳实践（直接引用）：
1. **极其详尽的 description**（3-4 句，越详细越好）
2. **合并相关操作**到少数 capable tools（而非大量小 tools）
3. **有意义的命名空间前缀**（`db_query`, `storage_read`）
4. **高信号返回值**（semantic identifiers, 只返回 agent 下一步推理所需的字段）

**对我们的启发**：
- 我们的 MCP tools（`governance_decide`, `check_constraints` 等）已经遵循了类似模式
- "合并相关操作" 的建议值得我们回头审视当前 MCP tool surface — 是否有过度拆分的情况
- "高信号返回值" 直接适用于 `SubagentReport` 的设计：report 应只包含下一步决策所需信息

### 5. Agent Skills — 渐进式领域知识系统

**这是对我们的 Pack 系统最有价值的参考。**

#### 核心架构

Skills 是**文件系统目录**，包含 SKILL.md + 可选的引用文件和脚本。三级加载：

| 级别 | 加载时机 | Token 开销 | 内容 |
|---|---|---|---|
| L1: Metadata | 启动时（始终加载） | ~100 tokens/skill | YAML frontmatter: name + description |
| L2: Instructions | Skill 被触发时 | <5k tokens | SKILL.md body |
| L3: Resources | 按需 | 无上限 | 引用文件、脚本（脚本执行只传输输出） |

#### 关键设计决策

- **SKILL.md 是目录** — 不是 API 调用、不是数据库记录，是文件系统上的 markdown 文件
- **渐进式披露 (Progressive Disclosure)** — 只在需要时加载具体内容
- **description 是发现机制** — Claude 用 description 决定是否激活 skill
- **引用深度不超过一层** — SKILL.md → 引用文件，不允许引用文件再引用文件
- **脚本执行不加载源码** — 只有输出进入 context，源码不占 token
- **反馈循环** — 推荐 "执行 → 验证 → 修复 → 重复" 的 workflow 模式

#### Best practices 摘要

- 保持 SKILL.md body < 500 行
- 按领域拆分引用文件（finance.md, sales.md, product.md）
- 使用清单 (checklist) 跟踪复杂 workflow 进度
- 不包含时间敏感信息
- 术语一致
- 先建评估再写文档（evaluation-driven development）
- 用 Claude A 写 skill、Claude B 测 skill 的迭代模式

**对我们的启发（高优先级）**：

| Claude Skills 概念 | 我们的 Pack 系统对应 | 借鉴价值 |
|---|---|---|
| SKILL.md 三级加载 | 我们的 Pack 目前是全量加载 | **非常高**：Pack 应支持 metadata-only 发现 + 按需加载 |
| YAML frontmatter (name + description) | 我们有 pack manifest | 中：验证我们的 manifest 结构是否包含足够的发现信息 |
| description 作为激活信号 | 我们的 pack 选择机制 | 高：pack 的 description 质量直接影响 agent 是否正确选择 |
| 引用深度 ≤ 1 | 无约束 | 中：值得设为 Pack 写作规范 |
| 脚本执行不加载源码 | 我们的 subagent worker 调用 | 高：Pack 附带的验证脚本应只返回输出 |
| evaluation-driven development | 我们的 dogfood pipeline | 高：我们的 evaluator 模型可以直接参考 |
| 按领域拆分 | Pack 内部组织 | 中：为 Pack 规范补充组织指南 |

### 6. Multi-Agent Orchestration

Claude 的多 agent 编排模型：

- **单层委派**：coordinator agent 可以调用 callable_agents，但被调用者不能再调用其他 agent
- **共享文件系统，隔离上下文**：所有 agent 共享同一个 container/文件系统，但各自有独立的 session thread（各自的对话历史）
- **线程持久化**：coordinator 可以向之前调用过的 agent 发后续消息，agent 保持之前的上下文
- **线程事件**：`session.thread_created`, `session.thread_idle`, `agent.thread_message_sent/received`

**对我们的启发**：
- "单层委派"与我们 AGENTS.md 中"子 agent 只处理窄切片"的约束完全对齐
- "共享文件系统 + 隔离上下文"是一个比我们当前模型更精细的分离 — 我们的子 agent 目前共享所有上下文（包括状态文档），这可能导致耦合
- "线程持久化"对应我们 handoff 系统的 session 连续性需求，但 Claude 的方案更轻量（不需要 rebuild/refresh）
- 路由机制（`session_thread_id`）值得参考：custom tool result 和 tool confirmation 需要路由回正确的 thread

### 7. Structured Outputs

- `output_config.format` with `json_schema` 类型 → 保证输出严格符合 JSON Schema
- Tools 的 `strict: true` → 参数输入也被 schema 验证
- 语法编译有 24h 缓存
- 限制：最多 20 个 strict tools，24 个 optional params，16 个 union-type params

**对我们的启发**：
- 我们的 `SubagentReport` 和 dogfood pipeline 的输出已经是 frozen dataclass
- 如果未来接入 Claude API 作为 worker backend，可以直接用 strict mode 保证 report 格式
- 当前 `LLMWorker` 的 report 解析逻辑可以简化

---

## 与现有研究的关系

| 已有研究 | Claude Managed Agents 的补充/互证 |
|---|---|
| [OpenAI Agents SDK](./openai-agents-sdk.md) | Claude 的 multi-agent 模型更重量级（server-side session），但 custom tool 暂停-恢复模式更成熟 |
| [AutoGen](./autogen.md) | Claude 的 thread 持久化类似 AutoGen 的 team conversation，但更原生 |
| [OpenHands](./openhands.md) | Claude Skills 的三级加载与 OpenHands 的 always-on/on-demand 高度对应 |
| [OPA](./open-policy-agent.md) | Claude 的 permission policy 是 PDP/PEP 的工具粒度简化版 |
| [LangGraph](./langgraph-langchain.md) | Claude 的 session 状态机 (idle/running/rescheduling/terminated) 比 LangGraph 更简单但覆盖了核心 case |
| [Semantic Kernel](./semantic-kernel.md) | Claude 的 MCP server 集成验证了 MCP 作为 tool source 的可行性 |
| [Guardrails AI](./guardrails-ai.md) | Claude 的 permission policy 是 guard 的运行时版本 |

---

## 对平台的具体待办建议

### B-REF-1: Pack 渐进式加载设计

**优先级：高**  
**来源**：Claude Skills 三级加载架构  
**内容**：为 Pack 系统设计 metadata-only / manifest / full-load 三级加载，减少 context 占用。当前 Pack 全量加载会在 Pack 数量增长后成为瓶颈。

### B-REF-2: Pack description 质量标准

**优先级：中**  
**来源**：Claude Skills best practices — description 是发现机制  
**内容**：为 Pack manifest 的 description 字段建立质量标准：必须包含"做什么"和"何时使用"，3-4 句，避免模糊描述。这直接影响 agent 是否正确选择 Pack。

### B-REF-3: Pack 内部组织规范 — 引用深度与按域拆分

**优先级：中**  
**来源**：Claude Skills best practices — progressive disclosure patterns  
**内容**：Pack 内部引用文件不超过一层深度；大型 Pack 按领域拆分引用文件；引用文件超过 100 行时提供目录。

### B-REF-4: Permission policy 分层覆盖模型

**优先级：中**  
**来源**：Claude permission policies — toolset default + per-tool override  
**内容**：在 governance_decide 之外补充工具粒度的权限策略：pack 级默认 + 单 tool 级 override + deny_message 机制。

### B-REF-5: 工作流中断原语 (interrupt primitive)

**优先级：低**  
**来源**：Claude `user.interrupt` event  
**内容**：在 workflow 引擎层显式化中断与重定向操作，对应我们"发现超出 scope 时回退到 planning-gate"的模式。

### B-REF-6: 子 agent 上下文隔离评估

**优先级：中**  
**来源**：Claude multi-agent — 共享文件系统 + 隔离 context  
**内容**：评估当前子 agent 共享全部上下文是否合理，是否应改为"共享工作区文件 + 隔离对话/状态上下文"。

### B-REF-7: Custom tool surface 合并审计

**优先级：低**  
**来源**：Claude best practices — consolidate related operations  
**内容**：审计当前 MCP tool surface（governance_decide, check_constraints, get_next_action 等），评估是否有过度拆分，是否应合并相关操作。

---

## 总结判断

Claude Managed Agents 是继 OpenAI Agents SDK 之后，第二个提供**一等公民多 agent 编排**的主流 LLM 平台 API。其架构比 OpenAI 更重量级（服务端有状态 session），但在以下方面对我们有**直接参考价值**：

1. **Skills = 我们的 Pack 的工业级实现**：三级渐进加载、文件系统目录结构、description 作为发现机制 — 这些都可以直接指导 Pack 系统的演进。
2. **Permission policy 分层覆盖**：验证了我们 PDP/PEP 模型的方向，同时给出了工具粒度覆盖的具体方案。
3. **事件驱动 session 状态机**：`requires_action` 暂停-恢复模式是我们治理决策流的工业级参考。
4. **单层委派 + 上下文隔离**：与我们 AGENTS.md 的约束高度一致，但提供了更精细的隔离机制。

这份参考资料库应当作为 **Pack 系统演进**和**子 agent 管理优化**的持续参考入口。
