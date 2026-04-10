# 上下文持久化与压缩防护设计

## 文档定位

本文件定义平台在"会话内上下文压缩"场景下的防护设计。

它解决的核心问题是：当 AI model 的 conversation history 被压缩（token budget 耗尽后的自动 summarization），关键行为约束和工作状态可能丢失。

## 问题分析

### 已有防护层

平台目前已有 3 层上下文恢复机制：

| 层 | 机制 | 覆盖场景 |
|---|---|---|
| 会话初始 | copilot-instructions.md + AGENTS.md | 新会话启动时自动注入 |
| 会话间 | .codex/handoffs/CURRENT.md + Session Handoff Standard | 跨会话交接 |
| 实施层 | Document-Driven Workflow Standard | 工作闭环 |

### 缺失防护层

**会话内压缩**——当一次长会话中 conversation history 被 model 自动压缩时：

- copilot-instructions.md 中的约束仍存活（不在 conversation history 中）
- 但 **AGENTS.md 尾部的约束** 可能被截断
- **planning gate 的具体内容**、**当前 todo 状态**、**候选方向的来源依据** 等在 conversation history 中的信息会被压缩成 summary
- summary 质量不受平台控制

### 根因

1. 行为约束分散在 conversation history 和 always-on 文件中，压缩只作用于前者
2. 工作状态（当前做到哪一步、候选方向、设计分析）全部存在 conversation history 中
3. 没有"关键节点自动快照"机制

## 设计方案：B+C 组合

### B 层：行为约束持久化（快速止血）

**已实施**：将关键行为约束从 conversation history 提升到 always-on 加载层。

具体措施：
- `copilot-instructions.md` 中新增"对话行为约束"section，明确标注"上下文压缩后仍必须遵守"
- `AGENTS.md` 中同步添加精简版约束
- 约束条目：禁止单方面终止 → 方向文档化 → Phase 完成后自动推进 → 上下文恢复优先读文档 → 候选方向的来源

**效果**：这些约束不在 conversation history 中，不受压缩影响。

**局限**：always-on 文件有 token 预算限制，不能无限扩展。应只写入"无条件必须遵守的约束"，不写入工作状态。

### C 层：Checkpoint + Progressive Disclosure（长期治本）

#### C.1 Checkpoint 机制

**定义**：在工作关键节点，将当前工作状态写入 workspace 文件。压缩后 model 可通过读文件恢复，而不是依赖 conversation summary。

**Checkpoint 触发时机**：
- Phase 的 planning gate 被 APPROVED 时
- Phase 的一个 Slice 完成时
- Phase write-back 完成时
- 提出候选方向、等待用户选择时

**Checkpoint 存储位置**：`.codex/checkpoints/` 目录

**Checkpoint 文件格式**：
```
# Checkpoint — <timestamp>
## Current Phase
Phase N: <name>, Slice <X>, status: <in-progress|completed|waiting-user>
## Active Planning Gate
<path to planning gate file>
## Current Todo
- [x] done item
- [ ] in-progress item  
- [ ] not-started item
## Pending User Decision
<if awaiting user input, describe what was asked>
## Direction Candidates (if applicable)
- Candidate A: <one-line> — source: <doc ref>
- Candidate B: <one-line> — source: <doc ref>
## Key Context Files (re-read if memory incomplete)
- <file1>
- <file2>
```

**恢复流程**：当 model 检测到自身对项目状态记忆不完整时：
1. 读 `.codex/checkpoints/` 最新文件
2. 按 "Key Context Files" 重读必要文档
3. 恢复 todo list
4. 继续工作

#### C.2 Progressive Disclosure

**来源**：OpenHands 的 always-on / on-demand 二分法。

**应用**：
- always-on 文件（copilot-instructions.md、AGENTS.md）只放无条件约束，保持精简
- 工作状态放在 checkpoint 文件中，按需读取
- 候选方向的完整分析放在专题文档中，checkpoint 中只放一行摘要 + 路径引用

**效果**：减少 always-on token 占用，同时保证工作状态可恢复。

#### C.3 候选方向文档化

**来源**：用户反馈 + 对话行为约束。

**应用**：
- Phase 完成后的候选方向不再只用口头描述
- 应生成 `design_docs/direction-candidates-phase-<N>.md` 文档
- 每个候选项必须包含：
  - 一句话描述
  - 支撑文档引用（Checklist 待办 / docs/ 未实现能力 / research-compass 借鉴点）
  - 预估影响范围
- 压缩后 model 可通过读文件恢复候选列表，不丢失依据

## 实现路径

| 步骤 | 内容 | 状态 |
|---|---|---|
| 1 | copilot-instructions.md 行为约束持久化 | ✅ 已完成 |
| 2 | AGENTS.md 同步更新 | ✅ 已完成 |
| 3 | 本设计文档 | ✅ 当前文档 |
| 4 | `.codex/checkpoints/` 目录创建 + 首个 checkpoint | ✅ 已完成 |
| 5 | checkpoint 读写集成到 Document-Driven Workflow Standard | ✅ 已完成 |
| 6 | 候选方向文档化模板 | ✅ 已完成 |

## Checkpoint 实现深度对比

下面三种深度各解决不同层次的问题，成本递增。

### 选项 A：纯约定

**做什么**：只在本设计文档和 Document-Driven Workflow Standard 中定义 checkpoint 格式和触发时机约定。不写任何代码。AI 在合适时机手动创建 checkpoint 文件。

**优点**：
- 零代码成本
- 立即可用——AI 下次 phase 完成时手动写一个 `.codex/checkpoints/latest.md`

**缺陷**：
- 完全依赖 AI 自觉遵守——如果 AI 忘了写 checkpoint（例如上下文已被压缩时恰好不记得有这个约定），防护失效
- 格式不一致风险——每次手写可能字段遗漏
- 无法验证——没有脚本检测 checkpoint 是否过时或缺失

**适用场景**：当前 Phase 少、团队小、上下文压缩不频繁。

### 选项 B：约定 + 工具函数（推荐）

**做什么**：
1. 定义 checkpoint 格式约定（同选项 A）
2. 在 `src/` 中创建 checkpoint 读写工具函数：
   - `write_checkpoint(phase, slice, status, todos, pending_decision, direction_candidates, key_files)` → 写入 `.codex/checkpoints/latest.md`
   - `read_checkpoint()` → 解析 `.codex/checkpoints/latest.md` 返回结构化数据
   - `validate_checkpoint()` → 检查 checkpoint 是否存在且非过时
3. 在 Document-Driven Workflow Standard 中定义触发时机

**但不做**：不把这些函数自动集成到 executor/PEP workflow 中。触发仍由 AI 手动调用。

**优点**：
- 格式一致——函数保证输出格式始终符合约定
- 可验证——`validate_checkpoint()` 可作为 check 使用
- AI 调用门槛低——`write_checkpoint(...)` 一行调用比手写 markdown 方便
- 测试覆盖——可为读写逻辑写 pytest

**缺陷**：
- 仍依赖 AI 记得调用——但 always-on 约束 + 函数存在降低了遗忘概率
- 额外代码维护成本（约 100-150 行 Python）

**适用场景**：当前阶段最平衡的选择。

### 选项 C：Runtime 自动触发

**做什么**：
1. 选项 B 的全部内容
2. 在 PEP executor 或 workflow 层的关键节点自动调用 `write_checkpoint()`：
   - `executor.execute()` 完成后自动写 checkpoint
   - Write-back 完成后自动写 checkpoint
   - RSM 状态变更时自动写 checkpoint
3. 可选：定义 CheckpointTrigger 作为 Trigger 协议的实现

**优点**：
- 不依赖 AI 记忆——runtime 层保障 checkpoint 自动生成
- 最可靠的防护

**缺陷**：
- executor 与 checkpoint 耦合——每次 execute 都会写磁盘
- 粒度问题——自动触发可能产生过多 checkpoint 文件
- 当前 executor 的 dry-run 模式需要适配
- 实现成本最高（约 200-300 行 + executor 修改 + 测试）
- **过度工程风险**：当前 checkpoint 的消费者是 AI 自身在 conversation-level 恢复，而 executor 是 governance-level 的组件，层级不匹配

**适用场景**：平台成熟后、多用户场景、或 checkpoint 需要被外部系统消费时。

### 对比矩阵

| 维度 | 纯约定 | 约定+工具函数 | Runtime 自动触发 |
|---|---|---|---|
| 代码量 | 0 | ~150 行 | ~300 行 |
| 格式一致性 | 低 | 高 | 高 |
| AI 遗忘风险 | 高 | 中 | 低 |
| 过度工程风险 | 无 | 无 | 高 |
| 可测试性 | 无 | 有 pytest | 有 pytest |
| 维护成本 | 无 | 低 | 中 |
| 适合阶段 | 实验期 | **当前阶段** | 成熟期 |

## 参考来源

- OpenHands: Progressive Disclosure + always-on vs on-demand（[review/openhands.md](../../review/openhands.md)）
- LangGraph: Checkpoint Persistence + interrupt/resume（[review/langgraph-langchain.md](../../review/langgraph-langchain.md)）
- OpenAI Agents SDK: Sessions + Tracing（[review/openai-agents-sdk.md](../../review/openai-agents-sdk.md)）
- Continue: 单一职责规则文件（[review/continue.md](../../review/continue.md)）

## 与现有标准的关系

- 本设计**不替代** Session Handoff Standard（跨会话交接场景仍沿用 handoff）
- 本设计**补充** Document-Driven Workflow Standard（新增 checkpoint 触发点定义）
- 本设计**延伸** copilot-instructions.md / AGENTS.md（已实施约束持久化）
