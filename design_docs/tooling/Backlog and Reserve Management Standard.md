# Backlog 与储备方案管理标准

## 文档定位

本文件定义"未来需求、条件触发待办、储备方案"的结构化管理规则。

它补充 [Document-Driven Workflow Standard](Document-Driven%20Workflow%20Standard.md) 的以下空白：

- 当前常规工作流只管理"活跃待办 → planning-gate → 实施 → 回写"。
- 但方向分析中产出的**备选方案**、dogfood 中发现的**条件触发 gap**、以及跨版本的**长期研究空白**缺乏统一的登记、分类和生命周期规则。

## 三层分类模型

### 第 1 层：Active Backlog（活跃待办）

- **定义**：已确认需要实施，且已有或正在准备 planning-gate 的待办。
- **登记位置**：`design_docs/Project Master Checklist.md` §活跃待办与风险
- **格式**：`- [ ] 任务描述 — 相关文档链接`
- **生命周期**：`登记 → 起 planning-gate → 实施 → 完成 → 标 [x]`
- **退出条件**：planning-gate 标记 COMPLETED + 回写完成

### 第 2 层：Conditional Backlog（条件触发待办）

- **定义**：已记录但需要等待特定信号或条件才应激活的待办。
- **登记位置**：对应的 `direction-candidates-after-phase-*.md` 或本文件附录
- **格式**：

```markdown
| ID | 描述 | 触发条件 | 类型 | 优先级 | 状态 |
|----|------|----------|------|--------|------|
| BL-1 | Driver 职责定义 | dogfood 出现多 skill 消费场景 | 文档 | 低 | 待触发 |
```

- **生命周期**：`登记 → 待触发 → 条件命中 → 升级到第 1 层 → 起 planning-gate → 完成`
- **触发规则**：
  - 每次 dogfood 反馈审查时，扫描第 2 层条目的触发条件
  - 若条件匹配，将该条目从第 2 层升级到第 1 层（Checklist 活跃待办）
  - 升级时必须在 Checklist 中记录来源 BL-ID
- **退出条件**：完成后标记为"已完成"并记录对应 planning-gate 路径

### 第 3 层：Reserve / Future Backlog（储备方案与长期研究）

- **定义**：方向分析中被标记为"当前不选、未来可激活"的备选方案，或跨版本的研究空白。
- **登记位置**：本文件附录 §储备方案注册表，或对应方向分析文档中显式标注
- **格式**：

```markdown
| ID | 原始方向分析 | 储备方案描述 | 激活条件 | 兼容升级路径 |
|----|-------------|-------------|----------|-------------|
| R-1 | overrides-field-consumption | 方案 C 结构化覆盖 | 真实场景需要覆盖理由或条件约束 | list[str] → list[str \| object]，minor bump |
```

- **生命周期**：`登记 → 长期保持 → 激活条件命中 → 升级到第 2 层或直接第 1 层 → planning-gate → 完成`
- **清理规则**：
  - 每次起新的方向分析时，检查相关的第 3 层条目是否仍然有效
  - 若对应的技术决策已变化导致储备方案失效，标记为 `已失效` 并记录原因
- **退出条件**：激活并完成、或因技术演进失效

## 写回规则

### 何时登记

| 场景 | 登记层 |
|------|--------|
| 方向分析中选定了 A 但 C 也有价值 | 第 3 层（储备） |
| dogfood 发现了新 gap 但不在当前切片 scope | 第 2 层（条件触发） |
| 用户明确要求下一步做某事 | 第 1 层（活跃） |
| 子 agent 在委派切片中发现超出 scope 的新需求 | 先写回主 agent → 主 agent 决定登记到第 2 或第 3 层 |
| research-compass 中识别的研究空白 | 第 3 层 |
| planning-gate 实施中发现的关联改进 | 先完成当前切片 → 再登记到第 2 层 |

### 何时审查

- **每次 safe-stop writeback**：扫描第 2 层条件触发条目，检查当前 dogfood 结果是否命中触发条件
- **每次起新的方向分析**：检查第 3 层储备方案中是否有可复用的设计资产
- **每次 direction-candidates 文档刷新**：同步第 2 / 3 层条目的状态

## 与现有机制的关系

| 现有机制 | 本标准的关系 |
|---------|------------|
| `Project Master Checklist.md` §活跃待办 | = 第 1 层的唯一权威位置 |
| `direction-candidates-after-phase-*.md` §Backlog | = 第 2 层条件触发条目的主要来源 |
| 方向分析文档（如 `overrides-field-consumption-direction-analysis.md`） | = 第 3 层储备方案的出处 |
| `checkpoint latest.md` §Direction Candidates | = 第 1/2 层在当前会话中的快照视图 |
| `design_docs/stages/planning-gate/` | = 第 1 层条目被激活后的执行载体 |

## 不变量

- 每个第 2 / 3 层条目必须有明确的触发条件或激活条件。
- 条目的生命周期流转必须记录在来源文档中（标注 `升级至第 X 层 → planning-gate Y`）。
- 储备方案的技术兼容路径必须在登记时说明（如"A→C 升级路径为 minor bump"）。
- 清理操作不得删除记录，只能标记为 `已完成` 或 `已失效` 并附注原因。

---

## 附录：当前条目快照

### 第 2 层：条件触发登记表

| ID | 描述 | 触发条件 | 类型 | 优先级 | 来源 | 状态 |
|----|------|----------|------|--------|------|------|
| BL-1 | Driver 职责定义文档 | dogfood 出现多 skill 消费场景或 driver 语义不清 | 文档 | 低 | `direction-candidates-after-phase-35.md` | 待触发 |
| BL-2 | Adapter 分类与统一注册框架 | dogfood 出现"根据 rule config 动态选择 adapter"场景 | 设计+骨架 | 低-中 | `direction-candidates-after-phase-35.md` | 待触发 |
| BL-3 | 多协议转接层 | 多协议/多格式需求从 dogfood 或外部用户浮现 | 设计→原型 | 低 | `direction-candidates-after-phase-35.md` | 待触发 |
| BL-5 | mixin / DAG 多继承 | dogfood 出现横切关注点（如公共 lint 配置跨多分区）信号 | 设计+实现 | 低 | `hierarchical-pack-topology-direction-analysis.md` | 待触发 |
| BL-6 | IDE 扩展层输出拦截 | 平台决定打包为独立 VS Code 扩展，且 R-2 Chat Participant output gate 进入实施 | 设计+实现 | 中 | conversation-progression-contract 方案 D 分析 | 待触发 |
| BL-7 | decision log 持久化独立于 dry_run | dogfood 中确认审计日志需要独立于 dry_run 持久化，或出现审计回溯需求 | 设计+实现 | 低-中 | MCP 0.9.1 dogfood 验证 | 已完成（decision log 现始终持久化，不受 dry_run 控制） |
| BL-8 | merge 层冲突解决结果对 decision log 可见 | dogfood 中出现审计回溯需求，需要知道"哪个 pack 赢了哪条规则" | 设计+实现 | 低 | MCP 0.9.1 dogfood 字段分析 | 待触发 |

### 第 3 层：储备方案注册表

| ID | 原始方向分析 | 储备方案描述 | 激活条件 | 兼容升级路径 | 状态 |
|----|-------------|-------------|----------|-------------|------|
| R-1 | `overrides-field-consumption-direction-analysis.md` 方案 C | 结构化覆盖：`overrides` 携带 reason/keys/condition | 真实场景需要覆盖理由或条件约束 | `list[str]` → `list[str \| object]`，manifest_version minor bump | 储备 |
| R-2 | conversation-progression-contract 方案 D | 自建 Chat Participant 作为 output gate（路径 1） | 平台决定打包为独立 VS Code 扩展 | 当前 MCP+pack 规则 → vscode.lm + Chat Participant output gate，`completion_boundary_protocol` 校验逻辑直接复用 | 储备 |
| R-3 | conversation-progression-contract 折衷 3 | `finalize_response()` MCP 校验工具 | B+A 实施后仍观察到完成边界违规 | 新增 MCP tool，不改架构；校验逻辑向 R-2 兼容 | 储备 |

### 已完成条目

| ID | 描述 | 完成日期 | 对应 planning-gate |
|----|------|---------|-------------------|
| BL-4 | 对话中临时规则突破能力 | 2026-04-12 | `2026-04-12-conversation-progression-contract-stability.md` 等 |
