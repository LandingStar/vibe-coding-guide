# 多实例共存冲突解决策略方向分析

## 来源

- `review/research-compass.md` — 当前研究空白 #4："多实例共存时的冲突解决策略"
- `docs/pack-manifest.md` — pack manifest 权威文档
- `docs/precedence-resolution.md` — 优先级解析权威文档
- `design_docs/hierarchical-pack-topology-direction-analysis.md` — 拓扑设计推导

## 现状

当前 pack 系统已具备：

- **PackTree** — 单继承树，支持 forest（多根）；重名拒绝、循环拒绝、兄弟 scope 重叠拒绝
- **ContextBuilder** — 按 kind 优先级（platform→instance→project-local）排序后顺序合并
- **PrecedenceResolver** — layer-priority 排序，高层级优先；显式 `explicit_override` 标记
- **OverrideResolver** — 从 PackContext 合成 RuleConfig，字段级合并策略

但 **同层级多实例并存时存在 4 个未解决的冲突场景**。

## 已识别的冲突场景

### 场景 1 — 同层规则静默覆盖

两个 project-local pack 都定义 `rules.impact_table.question`，`_deep_merge()` 后者覆盖前者，无审计痕迹。

**影响**：用户无法发现某个 pack 的规则配置被另一个 pack 静默覆盖。

### 场景 2 — 同层优先级平局

`PrecedenceResolver` 中两个同层规则竞争时，按列表顺序取第一个，结果确定但不透明。

**影响**：`precedence_resolution` 结果中没有标记"这是平局裁决"，用户无法区分"明确胜出" vs "碰巧排在前面"。

### 场景 3 — 多 pack 覆盖同一目标

两个 pack 都声明 `overrides: ["target-pack"]`，`merged_overrides` 收集了两组声明，但 `PrecedenceResolver` 的 `explicit_override` 只检查 winner 是否声明了 override，不区分多个 pack 同时声明 override 的语义。

**影响**：override 竞争缺乏明确的仲裁规则。

### 场景 4 — 替换型字段争夺

`delegatable_intents` 等"替换型"字段，OverrideResolver 取"第一个非空值"。当两个同层 pack 都提供非空值时，后者被忽略，无警告。

**影响**：用户添加新 pack 时可能不知道自己的 `delegatable_intents` 配置未生效。

## 候选方案

### 方案 A — 冲突检测 + 审计报告（推荐）

**范围**：不改变现有合并策略，但在合并过程中检测冲突并报告。

**改动**：

1. **ContextBuilder 冲突检测**（`src/pack/context_builder.py`）：
   - `_deep_merge()` 新增 `conflicts` 收集器，当 key 已存在且被覆盖时记录 `{key, old_source, new_source, old_value, new_value}`
   - `PackContext` 新增 `merge_conflicts: list[dict]` 字段

2. **PrecedenceResolver 平局标记**（`src/pdp/precedence_resolver.py`）：
   - 当 winner 和 runner-up 具有相同 layer priority 时，result 新增 `tie_broken_by: "insertion_order"` 字段

3. **Pipeline.info() 暴露**（`src/workflow/pipeline.py`）：
   - `info()` 新增 `merge_conflicts` 和 `tie_resolutions` 字段
   - MCP `check_constraints()` 新增同层冲突的 advisory warning

**不做**：不改变合并行为（last-writer-wins 保持），只增加透明度。

**优势**：零破坏性改动；用户和 AI 能看到冲突报告并决定是否需要显式 override。

**劣势**：不解决冲突本身，只报告。

### 方案 B — 冲突检测 + 强制声明

在方案 A 基础上，新增约束：当检测到同层规则冲突时，要求至少一方声明 `overrides` 以明确覆盖意图。

**额外改动**：

4. **强制覆盖声明**：
   - 同层冲突且双方均未声明 `overrides` 时，`check_constraints()` 产生 warning
   - 可通过 `temporary_override` 临时豁免

**优势**：推动用户显式管理覆盖关系。

**劣势**：对现有 pack 配置有侵入性，可能导致首次加载时大量 warning。

### 方案 C — 完整仲裁引擎

完整的冲突仲裁系统，包括字段级合并策略配置、自定义仲裁规则、冲突报告面板。

**优势**：完整解决所有冲突场景。

**劣势**：过度工程化，当前只有 2 个 pack（instance + project-local），无同层冲突的实际案例。

## 推荐

**推荐方案 A**。理由：

1. 当前实际使用中只有 2 个不同层级的 pack，同层冲突尚未发生，方案 A 的"检测 + 报告"策略已足够
2. `merge_conflicts` 和 `tie_broken_by` 为后续方案 B/C 提供了基础数据
3. 改动集中在 3 个文件，不改变现有行为，风险极低
4. 与 decision logs 协同——冲突信息可反映在 `DecisionLogEntry` 中

预计交付：

- 修改 3-4 个源文件
- `PackContext.merge_conflicts` 新字段
- `PrecedenceResolver` 平局标记
- `Pipeline.info()` 暴露冲突信息
- 5-6 个 targeted tests
