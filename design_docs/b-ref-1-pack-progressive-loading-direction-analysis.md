# Direction Analysis — B-REF-1: Pack 渐进式加载

> 日期：2026-04-16  
> 前置：`review/claude-managed-agents-platform.md` → B-REF-1  
> 触发：当前 Pack 系统在 Pipeline 初始化时全量加载所有 pack 内容，Pack 数量增长后 context 占用将线性增长

## 背景与当前状态

### 当前加载流程

```
Pipeline.from_project() → _discover_packs()
                              ↓
                         manifest_loader.load() [全量 JSON]
                              ↓
                         ContextBuilder.add_pack()
                              ↓
                         ContextBuilder.build() → always_on 全量读文件
                              ↓
                         PackContext（已全量）
```

### 当前瓶颈

| 阶段 | 当前行为 | 问题 |
|------|---------|------|
| Manifest 解析 | `load()` 一次性读完整个 JSON | 无法只获取 name/kind/provides |
| ContextBuilder.build() | 对每个 pack 的 `always_on` 逐个读文件内容 | 文件多时 I/O + context 占用 |
| PackContext | `always_on_content` 存储所有文件全文 | 内存 + token 占用无上限 |
| on_demand | 声明存在但极少使用 | L3 概念已有但未整合到加载策略 |

### 已有的懒加载基础

- `PackContext.on_demand_entries`: `dict[str, Path]` — 路径已收集但不读内容
- `PackContext._on_demand_cache`: `dict[str, str]` — 按需读取并缓存
- `ContextBuilder.load_on_demand(key)` / `list_on_demand()` — API 已存在

## 三级加载模型设计

### L1: Metadata-only（启动阶段）

**目标**：以最小开销发现可用 pack，提供 Pack 选择所需的最少信息。

**加载内容**：
- `name`, `version`, `kind`, `manifest_version`
- `provides` (能力列表)
- `description` (**新字段** — 当前 manifest 缺少)
- `scope`, `scope_paths`, `parent`

**token 成本**：~100-150 / pack

**使用场景**：MCP `get_pack_info` 工具返回 pack 列表时、AI 根据 description 选择 pack 时。

### L2: Manifest（配置阶段）

**目标**：完整 manifest 数据用于决策和配置，但不读取任何文件内容。

**加载内容**：L1 全部 + `intents`, `gates`, `document_types`, `depends_on`, `overrides`, `always_on` 路径列表, `on_demand` 路径列表, `rules`, `validators`, `checks`, `scripts`, `triggers`, `prompts`, `templates`

**token 成本**：~500-2000 / pack（取决于声明复杂度）

**使用场景**：Pipeline 初始化、ContextBuilder.build() 合并能力集时。当前 `build()` 的合并逻辑（intents/gates/rules merge）只需 manifest 数据，不需要文件内容。

### L3: Full-load（执行阶段）

**目标**：读取 always_on 文件内容、注册扩展件。

**加载内容**：L2 全部 + `always_on_content`（实际文件文本）+ 扩展件注册

**token 成本**：无上限（取决于文件大小）

**使用场景**：Pipeline.process() 需要 instructions 注入时、validator/check 执行时。

## 候选切片

### Slice 1: LoadLevel enum + ContextBuilder 分阶段 build（最窄）

**做什么**：

1. 在 `PackManifest` 中添加可选 `description: str = ""` 字段
2. 新增 `LoadLevel` enum: `METADATA`, `MANIFEST`, `FULL`
3. 修改 `ContextBuilder.build()` 接受 `level: LoadLevel = LoadLevel.FULL` 参数
   - `METADATA`: 只合并 name/kind/provides/description，不读文件，不合并 rules
   - `MANIFEST`: 合并 intents/gates/rules/overrides，不读文件内容
   - `FULL`: 现有行为（向后兼容）
4. `PackContext` 新增 `load_level: LoadLevel` 字段
5. `PackContext` 增加 `upgrade(target_level)` 方法：从低级别升级到高级别（读取缺失的内容）

**不做**：
- 不修改 Pipeline 初始化流程（仍然 FULL load）
- 不修改 MCP 工具
- 不修改 on_demand 机制

**优势**：最窄 scope，引入分级概念，不改变任何现有行为。后续切片可逐步将 Pipeline 从 FULL 降级到 MANIFEST + 按需升级。

**文件变更预估**：

| 文件 | 变更 |
|------|------|
| `src/pack/manifest_loader.py` | `description` 字段 + `LoadLevel` enum |
| `src/pack/context_builder.py` | `build(level=)` + `PackContext.load_level` + `upgrade()` |
| `tests/test_pack_progressive_load.py`（新建） | 三级加载测试 |

### Slice 2: Pipeline 默认降级 + on_demand 整合（中等）

Slice 1 基础上：
- Pipeline 初始化改为 `MANIFEST` 级别
- `Pipeline.process()` 在需要 instructions 内容时自动升级到 `FULL`
- 整合现有 on_demand 作为 L3 内容

### Slice 3: MCP Pack 选择 + description 驱动（完整）

Slice 2 基础上：
- MCP `get_pack_info` 返回 L1 信息
- 新增 MCP 工具或参数允许按 pack name 请求 L2/L3 内容
- description 质量标准（B-REF-2）

## AI 倾向判断

**推荐 Slice 1**，理由：
1. 引入 `LoadLevel` + `description` 是最小但关键的概念变更
2. 不改变任何现有行为（FULL 是默认值）
3. `upgrade()` 方法为后续 Pipeline 降级铺路
4. 可独立测试

## 验证门

- [x] `LoadLevel.METADATA` build 只包含 name/kind/provides/description
- [x] `LoadLevel.MANIFEST` build 不读取文件内容（always_on_content 为空）
- [x] `LoadLevel.FULL` build 行为与当前完全一致
- [ ] `PackContext.upgrade(FULL)` 从 MANIFEST 升级后内容与直接 FULL build 一致
- [ ] `description` 字段在 manifest JSON 中正确解析
- [ ] 全量回归 ≥ 992 passed

## 权威引用

- [review/claude-managed-agents-platform.md](../review/claude-managed-agents-platform.md) — Claude Skills 三级渐进加载
- [src/pack/manifest_loader.py](../src/pack/manifest_loader.py) — 当前全量加载
- [src/pack/context_builder.py](../src/pack/context_builder.py) — ContextBuilder + PackContext
- [src/workflow/pipeline.py](../src/workflow/pipeline.py) — Pipeline._load_packs()
