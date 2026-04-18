# Driver Responsibilities

> 权威来源：`docs/driver-responsibilities.md`

## 文档定位

本文件定义平台中 **driver** 角色的职责边界。

它与 [`external-skill-interaction.md`](external-skill-interaction.md) 形成消费方-提供方的对称 contract：
- `external-skill-interaction.md` 定义 skill 侧的 invocation / continuation / authority boundary
- 本文件定义 driver 侧的输入来源、决策分发、结果消费与 write-back 控制

## Driver 是什么

Driver 是平台中负责**编排治理流程**的主控角色。

在当前架构中，driver 不是一个独立的代码类，而是由以下组件协作实现的逻辑角色：

| 组件 | 在 driver 角色中的职责 |
|------|----------------------|
| `Pipeline` | 治理链编排：意图分类 → PDP 决策 → PEP 执行 → write-back |
| `GovernanceTools` (MCP) | 工具调用面：将 driver 能力暴露给 AI agent |
| `InstructionsGenerator` | 静态指令面：将 driver 规则注入到 agent 的系统指令中 |
| 主 agent (Supervisor) | 运行时载体：实际执行 driver 逻辑的 AI agent 实例 |

## Driver 与 Supervisor 的关系

[`subagent-management.md`](subagent-management.md) 定义了 `Supervisor-Worker` 协作模型，其中主 agent 扮演 Supervisor。

Driver 是 Supervisor 角色在治理编排维度的具体化：

- **Supervisor** 定义的是角色关系（谁管谁、谁 review 谁的输出）
- **Driver** 定义的是该角色在治理流程中做什么（怎么编排、怎么消费结果、怎么控制 write-back）

两者不矛盾，但关注面不同。

## Driver 的职责边界

### Driver 负责

| 职责 | 说明 | 体现位置 |
|------|------|----------|
| **意图分类** | 将用户输入分类为 intent + gate level | `Pipeline.process()` → `IntentClassifier` |
| **治理决策分发** | 将分类结果交由 PDP 做出 allow/block/review 决策 | `Pipeline.process()` → `PolicyDecisionPoint` |
| **执行编排** | 根据 PDP 决策编排 PEP 执行路径 | `Pipeline.process()` → `PolicyEnforcementPoint` |
| **约束检查** | 检查项目状态是否满足治理约束 | `Pipeline.check_constraints()` |
| **外部 skill 结果消费** | 消费 external skill 返回的 continuation signal | 遵循 `external-skill-interaction.md` §Continuation Boundary |
| **子 agent review** | 审查子 agent 产出并决定 integrate/reject/revise | `subagent-management.md` §Review Of Subagent Output |
| **Write-back 控制** | 控制对权威文档和状态板的写入 | `WritebackEngine` / `SafeStopWriteback` |
| **审计追踪** | 记录治理决策和执行过程 | `DecisionLogStore` / `AuditTracer` |
| **Pack 信息聚合** | 加载、合并多 pack 的规则/上下文/元数据 | `Pipeline.info()` / `PackContext` |
| **Session 状态管理** | 维护跨调用的 session 状态（仅 MCP 层） | `GovernanceTools._pipeline` / `_session_state` |
| **指令注入** | 将治理规则注入到 agent 的系统指令 | `InstructionsGenerator.generate()` |

### Driver 不负责

| 不做 | 原因 |
|------|------|
| 外部 skill 内部逻辑 | skill 自治，driver 只消费 continuation signal |
| 子 agent 的具体实现 | 子 agent 按合同自治，driver 只 review 结果 |
| Pack 内容的编写 | pack 由 pack 作者维护，driver 只加载消费 |
| 用户对话的直接生成 | driver 提供规则/约束，实际回复由 agent 生成 |
| 远端 registry / 分发 | 超出当前版本范围（BL-3 / 远期） |
| Adapter 动态选择 | 超出当前版本范围（BL-2） |

## Driver 的输入来源

```
Pack Rules & Context ──→ PackContext ──→ ┐
Project State ─────────→ Constraints ──→ │
User Input ──────────────────────────────┤──→ Pipeline.process()
MCP Tool Call ───────────────────────────┤──→ GovernanceTools.*()
Static Instructions ─────────────────────┘──→ InstructionsGenerator
```

| 输入 | 来源 | 消费方式 |
|------|------|----------|
| Pack 规则 | `pack-manifest.json` + pack 资产文件 | `PackContext` 聚合后注入 Pipeline |
| 项目状态 | `.codex/` 目录下的状态文件 | `check_constraints()` 读取并校验 |
| 用户输入 | MCP tool call / CLI 参数 | `process()` 进行意图分类 |
| External skill 结果 | skill 返回的 `blocked` / non-blocked signal | driver 决定 continue / escalate |
| 子 agent report | `SubagentReport` 结构化返回 | driver review → integrate / reject |

## Driver 的结果分发路径

```
Pipeline.process()
  ├──→ PipelineResult (intent + gate + decision + execution)
  ├──→ DecisionLogEntry (审计持久化)
  ├──→ WritebackPlan (文档更新计划)
  └──→ InteractionContract (对话推进约束)

GovernanceTools.*()
  ├──→ governance_decide() → PipelineResult
  ├──→ check_constraints() → ConstraintResult
  ├──→ get_next_action() → NextActionRecommendation
  ├──→ writeback_notify() → WritebackBundle
  └──→ get_pack_info() → PackInfoResult
```

## 当前 Runtime 中 Driver 的体现

| 入口 | 对应 driver 能力 | 文件 |
|------|-----------------|------|
| CLI `process` | 完整治理链（dry-run） | `src/__main__.py` |
| CLI `validate` | 约束检查 | `src/__main__.py` |
| CLI `check` | 约束/状态检查 | `src/__main__.py` |
| CLI `info` | Pack 信息聚合 | `src/__main__.py` |
| CLI `pack` | Pack 生命周期管理 | `src/__main__.py` + `src/pack/pack_manager.py` |
| MCP `governance_decide` | 完整 PDP→PEP 链 | `src/mcp/tools.py` |
| MCP `check_constraints` | 约束检查 | `src/mcp/tools.py` |
| MCP `get_next_action` | 下一步推荐 | `src/mcp/tools.py` |
| MCP `writeback_notify` | 写回通知 + bundle | `src/mcp/tools.py` |
| MCP `get_pack_info` | Pack 信息 | `src/mcp/tools.py` |
| MCP `governance_override` | 临时规则突破 | `src/mcp/tools.py` |
| Instructions | 静态规则注入 | `src/workflow/instructions_generator.py` |

## 与 BL-2 / BL-3 的关系

本文件不定义 adapter 注册或多协议转接。

当这些能力落地时，driver 的职责将扩展为：

- 根据规则配置动态选择 adapter（BL-2）
- 管理协议级别的 route / transform / retry（BL-3）

但 driver 的核心职责（意图分类 → 决策分发 → 结果消费 → write-back 控制）不变。

## 当前边界

本文件只固定 driver 的概念定义与当前职责映射。

它不定义：

- adapter 统一注册框架（BL-2）
- 多协议转接层（BL-3）
- driver 内部的可扩展 hook 接口
- 具体 skill 的 driver-side 消费协议
