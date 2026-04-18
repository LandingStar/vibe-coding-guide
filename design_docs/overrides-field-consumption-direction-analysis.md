# Overrides 字段消费方向分析

## 文档定位

本文件是关于 `PackManifest.overrides` 字段消费（gap analysis #12）的方向分析文档。

它的目的是：

- 描述 `overrides` 字段的当前状态与缺口
- 分析候选语义定义并比较
- 推荐实施方案与切片策略
- 明确前置条件与风险

本文件不直接进入实现。实施前必须先提取窄 scope planning-gate。

## 当前状态

### 字段声明

`PackManifest.overrides: list[str]` 已在以下位置声明并加载：

- [src/pack/manifest_loader.py](../src/pack/manifest_loader.py) 第 44 行：`overrides: list[str] = field(default_factory=list)`
- [src/pack/manifest_loader.py](../src/pack/manifest_loader.py) 第 110 行：`overrides=_as_str_list(data.get("overrides", []))`
- [docs/pack-manifest.md](../docs/pack-manifest.md) §overrides：用于声明"该 pack 准备覆盖谁 / 覆盖是否显式"

### 已有引用

| 位置 | 状态 |
|------|------|
| `PackManifest` dataclass | ✅ 已声明 |
| `load_dict()` / `load()` | ✅ 已加载 |
| `validate_instance_pack.py` | ✅ 结构校验 |
| 所有现有 manifest 文件 | ✅ 存在，值为 `[]` |
| `ContextBuilder` | ❌ 未提取或消费 |
| `OverrideResolver` | ❌ 未消费 |
| `PrecedenceResolver` | ❌ 未消费 |
| `Pipeline.info()` | ❌ 未暴露 |

### 开放问题（来自 docs/pack-manifest.md）

> `overrides` 是否需要携带覆盖理由或条件

### 与 Hierarchical Pack Topology 的关系

[design_docs/hierarchical-pack-topology-direction-analysis.md](hierarchical-pack-topology-direction-analysis.md) 第 309 行：

> 当前 `overrides` 字段尚未消费（gap analysis #12），层级化 pack 拓扑与 overrides 有天然关联——子 pack override 父 pack 是最自然的消费场景。

树拓扑已经落地（`parent` / `scope_paths` / `PackTree` / `build_scoped()` / `process_scoped()`），这意味着 `overrides` 的消费场景已从"理论上可能有用"变为"子 pack 显式声明覆盖父 pack 规则是自然的审计需求"。

## 候选语义

### 方案 A：Pack 名称级覆盖声明（推荐）

**定义**：`overrides: ["parent-pack-name"]` 表示"本 pack 显式声明它将覆盖指定 pack 的规则"。

**语义边界**：

- `overrides` 是**声明**，不是**执行机制**——实际的规则覆盖仍由 `_deep_merge` 在排序后的 pack 链中完成
- `overrides` 补充的是**可审计性**——当 precedence 仲裁选出某 pack 的规则胜出时，`overrides` 字段确认这是有意为之而非意外合并
- `overrides` 补充的是**验证性**——若声明了 `overrides: ["foo"]` 但 `foo` 不存在于已加载的 pack 集合中，应产生警告

**Runtime 行为**：

| 场景 | 行为 |
|------|------|
| Pack X 声明 `overrides: ["Y"]`，Y 存在于加载集 | 正常，标记为 explicit override |
| Pack X 声明 `overrides: ["Y"]`，Y 不存在 | 警告：override target not found |
| Pack X 的规则覆盖了 Y 的规则，但 X 未声明 `overrides: ["Y"]` | 合并照常进行，但 info/审计中标记为 implicit override |
| Pack X 声明 `overrides: ["Y"]`，但实际没有任何同 key 规则 | 可选警告：declared override has no effect |

**Precedence 侧效果**：

当 precedence resolver 构建结果时：

- 若 winning pack 的 `overrides` 包含 losing pack → `resolution_strategy` 可标注 `"explicit-override"`
- 否则保持当前策略名

**优点**：

- 类型不变（`list[str]` 原样）
- 无 `manifest_version` bump（纯消费面扩展）
- 与现有 `depends_on` 的"pack 名引用"模式一致
- 对已有 `"overrides": []` 的 manifest 完全后向兼容
- 自然契合树拓扑中子→父的显式覆盖声明

**缺点**：

- 粒度停留在 pack 级，无法声明"只覆盖某个具体 rule key"
- 无覆盖理由字段（不回答 pack-manifest.md 的开放问题）

### 方案 B：Rule Key 级覆盖声明

**定义**：`overrides: ["impact_table.question", "gate_for_impact.low"]` 表示"本 pack 显式声明它将覆盖指定的规则路径"。

**语义边界**：

- 覆盖粒度到 rule key（以 dot-path 表示 JSON 路径）
- 验证：若声明的 key 在 merged_rules 中实际不存在，产生警告
- 审计：精确到 key 级别的覆盖审计

**优点**：

- 审计粒度最细

**缺点**：

- 使 overrides 声明严重依赖 rules 的内部结构——rule key 重命名会导致 overrides 声明失效
- 维护成本高：每次调整规则结构都需同步更新 overrides 声明
- 实际场景中，pack 级粒度已够用——"backend pack 覆盖 root pack"比"backend 覆盖 root.impact_table.question"更自然
- 与 `depends_on`（pack 名引用）的模式不一致

### 方案 C：带条件/理由的结构化覆盖

**定义**：

```json
{
  "overrides": [
    {"target": "parent-pack", "reason": "stricter review for backend", "keys": ["gate_for_impact"]}
  ]
}
```

**优点**：

- 回答了 pack-manifest.md 的开放问题（覆盖理由）
- 同时支持 pack 级和 key 级粒度

**缺点**：

- **类型变更**：`list[str]` → `list[object]`，这是对已有字段的语义变更，需要 `manifest_version` major bump
- 过度工程化：当前没有任何 manifest 使用非空 overrides，在无真实场景验证前就引入复杂结构，风险高
- 违反"在没有窄 scope 文档前不进入大规模实现"原则

## 推荐

**当前实施：方案 A（Pack 名称级覆盖声明）**。

理由：

1. **类型零变更**：`list[str]` 原样消费，无 manifest_version bump
2. **与现有模式一致**：`depends_on` 已经是 `list[str]` 的 pack 名引用模式
3. **与树拓扑自然契合**：`overrides: ["my-parent"]` 是子 pack 最常见的声明
4. **最小实现面**：只需在 ContextBuilder/Pipeline 侧增加验证和审计注入
5. **可验证**：overrides 目标存在性检查与 `depends_on` 的 `check_dependencies()` 模式一致
6. **后向兼容**：对所有现有 `"overrides": []` 的 manifest 完全无影响

**未来储备：方案 C（结构化覆盖）标记为可用升级路径**。

当未来出现以下信号时，方案 C 值得从储备中激活：

- 真实场景需要覆盖理由（如合规审计要求 override 附带 reason）
- 多团队协作中需要 key 级别的精确覆盖声明（如"只允许覆盖 gate_for_impact，不允许覆盖 delegatable_intents"）
- 覆盖条件需要机器可读（如"仅在 CI 环境下生效"）

升级路径为 `list[str]` → `list[str | object]`（manifest_version minor bump），方案 A 的消费代码天然兼容——当 item 是 `str` 时按当前逻辑处理，当 item 是 `dict` 时提取 `target` / `reason` / `keys` 等结构化字段。

关于 pack-manifest.md 的开放问题"overrides 是否需要携带覆盖理由或条件"——当前答案是**当前不需要，但设计上预留了升级到方案 C 的路径**。

## 实施影响面

### 需要变更的文件

| 文件 | 变更 |
|------|------|
| `src/pack/context_builder.py` | `_build_from_entries()` 提取 overrides → `PackContext.merged_overrides` |
| `src/pack/context_builder.py` | 新增 overrides 验证（目标存在性检查） |
| `src/pack/override_resolver.py` | `RuleConfig` 或 resolve 结果中暴露 override declarations |
| `src/pdp/precedence_resolver.py` | resolve 结果注入 `explicit_override: bool` |
| `src/workflow/pipeline.py` | `info()` 暴露 override declarations 与验证状态 |
| `docs/pack-manifest.md` | 回答开放问题、补充消费语义 |
| `docs/precedence-resolution.md` | 补充 explicit-override 注释 |
| tests | 新增 override declaration 验证与 precedence 注入测试 |

### 不需要变更的文件

| 文件 | 原因 |
|------|------|
| `src/pack/manifest_loader.py` | `overrides` 已加载，无需变更 |
| `src/pack/pack_tree.py` | 树结构不受 overrides 影响 |
| `src/mcp/tools.py` / `server.py` | 无新 MCP 参数 |
| `.codex/packs/*.json` / `doc-loop-vibe-coding/pack-manifest.json` | 当前为 `[]`，不变 |

### 预估切片

单一窄切片即可覆盖全部实施面：

1. `PackContext` 新增 `merged_overrides: dict[str, list[str]]`（pack_name → overrides targets）
2. ContextBuilder 在 `_build_from_entries()` 中提取并做目标存在性验证（warning-only）
3. PrecedenceResolver 在结果中标注 explicit-override
4. Pipeline.info() 暴露 override_declarations 与 override_warnings
5. 权威文档同步
6. Targeted tests

## 风险与缓解

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| 过度设计：当前无人使用非空 overrides | 中 | 方案 A 只做声明消费，不改变合并行为，零运行时影响 |
| 与 depends_on 校验重复 | 低 | depends_on 解决"依赖存在性"，overrides 解决"覆盖意图声明"，语义不同 |
| 未来需扩展到结构化覆盖 | 低 | list[str] 的 minor 升级到 list[str \| object] 不影响现有消费 |

## 前置条件

- hierarchical pack topology 已完成（✅）
- 当前测试基线 755 passed, 2 skipped（✅）
- 无 active planning-gate（✅）
