# Direction Candidates — After Phase 35

## 背景

Phase 35 已完成，`v1.0.0` 已发布。

在此之后，本仓库又完成了一项 post-v1.0 的窄 scope 标准化工作：

- 形成了 [design_docs/tooling/Dual-Package Distribution Standard.md](design_docs/tooling/Dual-Package Distribution Standard.md)
- 固定了平台 runtime 包与官方实例包的职责边界
- 固定了安装态 MCP 接入原则、最小兼容原则与最小验证门

这意味着下一步不应重新发散讨论“大方向”，而应从权威文档与当前实现缺口中选择一个可执行的窄切片。

## 来源

- [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md) 中的 post-v1.0 待办与当前活跃风险
- [design_docs/tooling/Dual-Package Distribution Standard.md](design_docs/tooling/Dual-Package Distribution Standard.md) 中已固定、但尚未落地的安装分发标准
- [docs/project-adoption.md](docs/project-adoption.md) 与 [docs/pack-manifest.md](docs/pack-manifest.md) 中尚未固定的安装/分发/兼容空白
- [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md) 中仍保留为后续方向的 N5 / checks 贯通议题
- [review/research-compass.md](review/research-compass.md) 中关于版本化 pack manifest 与 distribution 路径的研究空白
- 当前实现现实：官方实例脚本已可作为 adoption 工具存在，但还没有安装态入口、打包元数据与统一 validator/check 消费协议

## 候选方向

### A. 双发行包实现切片

- 做什么：把“双发行包标准”落成最小可安装实现，至少补齐 runtime 包与官方实例包的打包元数据、入口归属、package data 装载和最小 smoke 验证。
- 依据：
  - [design_docs/tooling/Dual-Package Distribution Standard.md](design_docs/tooling/Dual-Package Distribution Standard.md)
  - [docs/project-adoption.md](docs/project-adoption.md) 当前仍未固定安装器协议
  - [docs/pack-manifest.md](docs/pack-manifest.md) 当前仍未固定安装与发布流程
- 前置：双发行包标准已完成，可直接进入窄 scope planning-gate。
- 风险：中。会同时触及 Python packaging、入口暴露、package data 与安装后 smoke 验证。
- 当前状态：已完成。双包 wheel 构建通过、干净 venv 安装验证通过（runtime CLI + 实例 CLI + 资产可发现性全部正常）、AI 安装指南已打入 `release/doc-based-coding-v1.0.0.zip`。残留 CI/CD 自动化属于运维层，暂缓至发布目标确定后。

### B. 官方实例 validator/check 契约收口切片

- 做什么：把官方实例包中的 `validators` / `checks` / `scripts` 三类能力收口成稳定可消费契约，明确哪些脚本要暴露 `validate(data) -> dict` 一类的 registry 调用面，哪些保留为独立命令。
- 依据：
  - [docs/first-stable-release-boundary.md](docs/first-stable-release-boundary.md) 中 N5（Script-style validator 语义升级）与 checks 字段直连的遗留议题
  - [docs/pack-manifest.md](docs/pack-manifest.md) 中 `validators` / `checks` / `scripts` 的能力声明边界
  - 当前运行时现实：`get_pack_info` 仍将两个官方实例校验脚本列为 skipped validator
- 前置：不依赖完整打包实现，可先做协议与消费面收口。
- 风险：中。若定义过重，会把本应独立的 adoption 命令错误塞进 runtime validator 语义。
- 当前状态：已完成。官方实例 self-check 脚本已从 `validators` 边界中收回到 `scripts`。

### C. 兼容元数据与版本声明切片

- 做什么：把 runtime 包与官方实例包之间的兼容关系变成机器可读的声明面，明确“包管理层约束”和“pack 语义层约束”分别放在哪里。
- 依据：
  - [design_docs/tooling/Dual-Package Distribution Standard.md](design_docs/tooling/Dual-Package Distribution Standard.md) 已固定兼容声明层级
  - [docs/pack-manifest.md](docs/pack-manifest.md) 仍未固定版本兼容策略
  - [review/research-compass.md](review/research-compass.md) 仍将“版本化 pack manifest 规范”列为研究空白
- 前置：不必等完整打包实现，但最好与安装元数据设计一起推进。
- 风险：中高。若先做过深设计，容易在实际包布局与入口成形前重复修订。
- 当前状态：已完成。官方实例 pack manifest 已使用 `runtime_compatibility` 补齐语义层兼容声明，并与 Python 包依赖范围对齐。

### D. MCP pack info 刷新一致性切片

- 做什么：修正或显式文档化 MCP 长生命周期进程对 pack metadata 的刷新时机，避免 manifest 已更新而 `get_pack_info` 仍返回旧缓存。
- 依据：
  - 当前切片实现中，fresh `Pipeline.info()` 已反映新 manifest 边界，但当前 MCP `get_pack_info` 仍返回旧的 `validators`/`skipped_details` 缓存
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md) 当前要求上下文恢复与状态读取应以 workspace 现实为准
- 前置：无。
- 风险：低到中。问题更偏向状态一致性，而不是核心语义错误。
- 当前状态：已完成。长生命周期 `GovernanceTools` 现已按调用刷新 Pipeline，pack state 视图会跟随磁盘变化更新。

### E. Strict Doc-Loop Runtime Enforcement Slice

- 做什么：把当前仍停留在规则/提示词层的 doc-loop 对话约束进一步落到运行时可检查面，至少明确哪些约束可以被机器检查、哪些只能由上层 agent 指令承担，并补齐对应的状态审计或能力边界。
- 依据：
  - 当前 enforcement audit 结果表明，runtime 级 `check_constraints()` 主要仍只检查 C4/C5
  - [design_docs/tooling/Document-Driven Workflow Standard.md](design_docs/tooling/Document-Driven Workflow Standard.md) 与 [AGENTS.md](AGENTS.md) 已明确更严格的对话推进规则
  - 当前用户明确质疑“没有遵循严格的 doc-loop 规则”，且该质疑部分成立
- 前置：无。
- 风险：中。若把对话层约束和项目状态层约束混成一套，会导致职责边界再次模糊。
- 当前状态：已完成。runtime contract 已显式区分 machine-checked 与 instruction-layer 约束边界。

### F. Handoff Model-Initiated Invocation Slice

- 做什么：把 handoff workflow 的调用语义收口到“安全停点下允许 model 主动进入 handoff 分支，且 `generate / accept / refresh current / rebuild` 在未返回 `blocked` 时允许继续执行下一步”。
- 依据：
  - 当前用户最新明确要求：handoff 的构建应可由 model 主动调用，其他指令在不抛 `blocked` 的前提下也应可由 model 执行
  - `design_docs/tooling/Session Handoff Standard.md` 当前仍缺少 model 主动调用与 blocked stop 语义
  - `.codex/handoff-system/docs/Skill Workflow.md` 此前仍保留“若用户明确要求继续轮转”一类旧约束，需要在本切片中统一收口
- 前置：当前仓库已经回到安全停点，且 handoff proto-skill 已具备 `generate / accept / refresh current / rebuild` 四条分支。
- 风险：低到中。若收口不严，可能会放宽到越过安全停点或越过 blocked 停止条件。
- 当前状态：已完成。权威协议、workflow、skill contract 与 bootstrap / example 副本已统一到 model 主动调用 + blocked-only stop 语义；显式 slash 入口仍保留为示例而非唯一触发条件。

### G. 持续 Pre-Release Dogfood / Gap Tracking Slice

- 做什么：继续在真实开发中受控使用 CLI / MCP / Instructions，收集新的 dogfood 反馈，并只把命中的 regression / gap 拉成新的窄 planning-gate。
- 依据：
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md) 当前活跃待办中的“持续 pre-release dogfood：在实际开发中受控使用 CLI / MCP / Instructions，并收集反馈”
  - [docs/official-instance-doc-loop.md](docs/official-instance-doc-loop.md) 当前官方实例使用入口
  - [review/research-compass.md](review/research-compass.md) 中仍保留的研究与借鉴空白
- 前置：当前 safe-stop handoff 已生成，`.codex/handoffs/CURRENT.md` 已指向最新 canonical handoff。
- 风险：低到中。若缺少新信号就硬推实现，容易从“收集反馈”扩成无依据的大改。

### H. 通用外部 Skill 交互接口能力 Slice

- 做什么：把“model 可主动触发外部 skill、skill 在非 `blocked` 结果下可继续流转、slash 入口只是显式路由而非唯一调用面”等规则，收口为与当前项目和单一 handoff skill 解耦的通用接口能力；首个实现可以围绕当前 handoff skill，但最终产物必须能被 driver 侧复用。
- 依据：
  - 用户最新裁决：第 1 点与第 4 点应合并为通用接口能力，先可围绕当前外部 skill 特化固化，但最终要与当前项目和具体 skill 解耦
  - [docs/plugin-model.md](docs/plugin-model.md) 对“平台能力与具体实例/插件分离”的定位
  - [docs/subagent-management.md](docs/subagent-management.md) 当前已定义委派/协作边界，但尚未把“driver 与外部 skill 的交互 contract”标准化为独立能力
- 前置：当前 handoff workflow 已证明 model-initiated / blocked-only stop 语义可行，且 safe-stop handoff 已生成。
- 风险：中。若直接把 handoff 特例硬编码成平台 contract，容易把 project-local 经验错误上升为通用规范。
- 备注：用户要求先详细解释“authority -> shipped copies 单源编译 / 漂移检查”这一子问题，再决定它是并入本切片还是作为辅助机制单列。
- 当前状态：已完成。`docs/external-skill-interaction.md`、`src/workflow/external_skill_interaction.py`、pack rules、instructions / MCP surface、official instance reference 与 handoff skill texts 已统一到同一套 external skill interaction contract；`authority -> shipped copies` 也已作为 companion drift-check / distribution rule 落地。

### I. Safe-Stop Writeback Bundle Slice

- 做什么：把 safe-stop 收尾时必做的 handoff generation、`CURRENT.md` refresh、Checklist / Phase Map / direction / checkpoint 同步收口成一个 first-class writeback bundle，而不是依赖本轮这种逐项补写。
- 依据：
  - 用户最新裁决：第 3 点接受并标为 crucial
  - [design_docs/tooling/Document-Driven Workflow Standard.md](design_docs/tooling/Document-Driven Workflow Standard.md) 当前要求验证后回写状态板/阶段文档/协议文档与 handoff，但尚未把 safe-stop close 固化成 bundle 化 contract
  - [design_docs/tooling/Session Handoff Standard.md](design_docs/tooling/Session Handoff Standard.md) 已定义 handoff 分支，却尚未把 safe-stop 的外围状态面同步固定成原子写回能力
- 前置：当前 safe-stop handoff 已能生成并刷新 `CURRENT.md`，说明主流程存在；缺的是 bundled writeback contract。
- 风险：低到中。若 bundle 边界定义不准，可能把本应条件执行的写回强行绑定。
- 优先级：crucial（用户已明确确认）。
- 当前状态：已完成。`src/workflow/safe_stop_writeback.py` 已提供 bundle contract，`writeback_notify()` 现在会返回 required/conditional bundle items 与完整 `files_to_update`，workflow / handoff 协议也已同步到同一口径。

### J. Conversation Progression Contract Stability Slice

- 做什么：把“未经用户显式许可不得主动终止对话”与“遇到选择、审批、方向确认时必须先给分析/倾向判断，再以提问继续交流，必要时使用 `askQuestions`”收口为稳定行为支架，而不只停留在规则文案层。
- 依据：
  - 用户最新明确裁决：该约束“仍不能稳定生效，应当先处理这个”，且处理完之后再按既定 I → H 顺序继续
  - [design_docs/tooling/Document-Driven Workflow Standard.md](design_docs/tooling/Document-Driven Workflow Standard.md) 已定义对话推进规则，但当前 prompt / generator / tool 输出仍缺少可复用的操作支架
  - [design_docs/stages/planning-gate/2026-04-11-strict-doc-loop-runtime-enforcement.md](design_docs/stages/planning-gate/2026-04-11-strict-doc-loop-runtime-enforcement.md) 已明确 runtime 不会自动审查每一轮回复是否满足推进式提问，因此需要另一层稳定机制
- 前置：当前仓库无 active gate，可直接为这一新窄需求起 planning-gate。
- 风险：中。若切片膨胀成完整 conversational rule engine，会偏离本轮“稳定行为支架”目标。
- 优先级：当前最高。用户已明确要求先做，再回到 I / H。
- 当前状态：已完成。正式规则、project-local pack、prompt surfaces、instructions generator、MCP next-step outputs 与 official-instance always_on reference 已统一到 conversation progression contract；针对 `jsonschema` 依赖链受限的 official-instance 全文件回归，当前仍保留环境级验证缺口。

## AI 倾向判断

当前 A、B、C、D、E、F、H、I、J 与 safe-stop handoff generation 均已完成。当前仓库已经没有新的高优先级能力缺口需要立刻进入实现，剩余更像是“持续 dogfood”与“补记后续 backlog 边界”的轻量后续项。

原因是：

1. J、I、H 三条近期高优先级切片已经分别补齐了“对话推进稳定性”“safe-stop 收尾 contract”和“通用 external skill interaction contract”三块关键支架。
2. 当前 Checklist 里剩下的事项，要么是背景性的持续 dogfood，要么是低优先级或纯 backlog 记录，不再构成必须立刻实现的新主线。
3. 因此，更合理的下一步通常不是继续扩实现面，而是先保持 safe stop，并根据用户偏好决定是否要把 backlog 边界再单独文档化一次。

所以按当前信息，我当前倾向是：先回到无 active gate 的 safe stop，把 `G. 持续 Pre-Release Dogfood / Gap Tracking Slice` 作为默认背景主线；只有当用户希望先把 driver / adapter / 转接层 backlog 边界写清时，再开一条轻量文档切片。

## 用户决定

- 状态: `UPDATED`
- 当前已完成方向:
  - `H. 通用外部 Skill 交互接口能力 Slice`：已完成；对应 planning-gate 为 `design_docs/stages/planning-gate/2026-04-12-external-skill-interaction-interface.md`。
- 当前选定方向:
  - `G. 持续 Pre-Release Dogfood / Gap Tracking Slice`：用户已明确选择继续受控 dogfood；当前保持无 active gate，仅在出现真实 regression / gap signal 时再起新的窄 gate。
- 当前备选方向:
  - `driver / adapter / 转接层 backlog 记录切片`：若后续需要先把实现边界文档化，可单独起一条轻量文档切片，但不直接进入实现。
- 已完成方向:
  - `J. Conversation Progression Contract Stability Slice`：已完成，已把“非用户许可不终止对话 + 选择/审批时以提问推进”的行为支架稳定到多层载体。
  - `I. Safe-Stop Writeback Bundle Slice`：已完成，已把 safe-stop close 收口为 bundle contract 与 targeted validation。
- 已完成配套机制:
  - `authority -> shipped copies` 的单源编译 / 漂移检查：已作为 H 的 companion drift-check / distribution rule 落地。
- 已记录但本轮不实施:
  - driver 与外部 skill 交互的标准 / 接口 / 留空转接层 — 已结构化记录为下方 §Driver / Adapter / 转接层 Backlog（BL-1 / BL-2 / BL-3）。
  - 本轮讨论中另外两个仍特化于当前 skill 的后续需求，先记 backlog，不在当前切片实现。
- 当前结论: `当前已回到无 active gate 的 safe stop，且用户已选择继续受控 dogfood。后续只有在 dogfood 命中新回归/新缺口，或用户改为要求 backlog 边界文档化时，才再起新的 planning-gate。driver / adapter / 转接层 backlog 已结构化记录（BL-1 / BL-2 / BL-3），等待触发条件。`

## Driver / Adapter / 转接层 Backlog（结构化记录）

以下条目从 Checklist 待办、direction candidates、Phase 0-35 实现、外部 skill interaction contract 与权威文档中提取，不涉及新 planning-gate，仅为后续方向提供结构化入口。

### 已落地的 Adapter / Bridge 实现

| 组件 | Phase | 位置 | 状态 |
|------|-------|------|------|
| Worker Adapters (LLMWorker, HTTPWorker) | 15 | `src/workers/` | 实验性（依赖外部 API，不纳入默认稳定面） |
| Notification Adapters (Console/File/Webhook) | 13 | `src/pep/notifiers/` | 稳定 |
| Pack Registrar Bridging | 25 | `src/pack/registrar.py` | 稳定 |
| External Skill Interaction Contract | H | `docs/external-skill-interaction.md` | 稳定（含 companion drift-check） |

### 尚未落地的 Backlog 条目

#### BL-1: Driver 职责定义文档

- **做什么**：把当前分散的 "driver" 概念（主 agent 对 external skill 结果的消费逻辑）统一到一份权威设计概述中，定义平台级 driver 的职责边界、输入来源与结果分发路径。
- **依据**：[docs/external-skill-interaction.md](../docs/external-skill-interaction.md) 已固定 skill 侧 contract，但 driver 侧（消费方）的职责仍分散在 pipeline / MCP tools / instructions generator 多处。
- **类型**：纯文档，不涉及代码实现。
- **触发条件**：当 dogfood 出现多 skill 消费场景或 driver 语义不清时触发。
- **优先级**：低。

#### BL-2: Adapter 分类与统一注册框架

- **做什么**：把现有三类 adapter（Worker / Notifier / Registry Bridge）的加载、发现、版本兼容逻辑抽取为统一描述模型，预留配置驱动的动态选择点。
- **依据**：[docs/plugin-model.md](../docs/plugin-model.md) 已定义插件模型抽象边界，但 adapter 级的统一注册/发现机制仍由各模块自行实现。当前 `PackRegistrar` 动态加载模式可作为模式参考。
- **类型**：设计文档 + 轻量骨架（如决定实施）。
- **触发条件**：当 dogfood 出现"根据 rule config 动态选择 adapter"的场景时触发。
- **优先级**：低到中。
- **依赖**：BL-1 的定义先行。

#### BL-3: 多协议转接层（远期）

- **做什么**：支持多协议 skill 调用（不仅 handoff，还包括远程 WebSocket / gRPC 等），定义内部协议→外部协议的转换、转移、恢复与重试中的协议中立边界。
- **依据**：[example/design_docs/stages/planning-gate/Post-MVP Scope Guardrails and Next-Step Plan.md](../example/design_docs/stages/planning-gate/Post-MVP%20Scope%20Guardrails%20and%20Next-Step%20Plan.md) 中已为 websocket / 远程适配器预留边界。[review/research-compass.md](../review/research-compass.md) 中仍将"版本化 pack manifest 规范"与"distribution 路径"列为研究空白。
- **类型**：设计文档→原型（视需求演进）。
- **触发条件**：当多协议/多格式需求从 dogfood 或外部用户需求中浮现时触发。
- **优先级**：低（超出当前版本规划）。
- **依赖**：BL-1 + BL-2。

### Backlog 与现有权威文档的关系

| 权威文档 | 与 Backlog 的关系 |
|----------|------------------|
| `docs/external-skill-interaction.md` | 已固定 skill 侧 contract；BL-1 补齐 driver 侧定义 |
| `docs/plugin-model.md` | 已固定插件抽象边界；BL-2 补齐 adapter 统一描述 |
| `docs/first-stable-release-boundary.md` | N5 (script-style validator) 与 BL-2 有交集，但互相独立 |
| `design_docs/tooling/Dual-Package Distribution Standard.md` | 打包/分发层面已固定；BL-3 的多协议层在其之上 |
| `design_docs/tooling/Document-Driven Workflow Standard.md` | 已定义对话推进与文档驱动规则；BL-4 补齐对话中临时规则突破的 contract |

#### BL-4: 对话中临时规则突破 / 修改能力

- **做什么**：把当前对话中由用户口头临时授权突破或修改默认行为规则的模式（例如"临时允许你使用 git，但仅限本地指令"），收口为可追溯、可审计、可撤销的 runtime contract，而不是依赖 model 记忆用户口头指令。
- **依据**：
  - 当前对话中用户临时授权修改了默认行为（"现在临时允许你使用 git，但仅限本地指令，禁止动远程"），该授权成功执行但仅靠 model 上下文维持，无持久化、无审计、无自动过期机制。
  - [design_docs/tooling/Document-Driven Workflow Standard.md](design_docs/tooling/Document-Driven%20Workflow%20Standard.md) 已定义 always-on 对话约束，但未区分"可被临时突破的约束"和"不可突破的硬约束"。
  - [docs/governance-flow.md](../docs/governance-flow.md) 已定义治理决策链，但决策链目前面向项目状态（gate / constraint），不面向对话行为层的动态 override。
- **类型**：设计文档 + 可能的轻量运行时支架（如需实施）。
- **触发条件**：当 dogfood 中再次出现用户临时修改行为规则的场景，或对话约束因上下文压缩而丢失临时 override 时触发。
- **优先级**：中。已证明该需求真实存在，但当前口头指令模式尚可工作。
- **依赖**：无硬依赖。与 conversation progression contract（J）有交集。