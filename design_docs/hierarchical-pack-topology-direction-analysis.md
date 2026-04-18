# 层级化 Pack 拓扑方向分析

## 文档定位

本文件是关于"Pack 层级化 / 树状拓扑"需求的方向分析文档。

它的目的是：

- 描述需求场景与动机
- 分析对现有架构的影响面
- 提出候选实现方案并比较
- 定义实施策略（分切片、风险、前置条件）

本文件不直接进入实现。实施前必须先提取窄 scope planning-gate。

## 需求场景

### 问题描述

当前平台的 Pack 系统采用扁平三层模型：

```
platform-default → official-instance → project-local
```

每层内部的多个 pack 之间没有定义层级关系。当一个大型项目需要按分区（如 frontend / backend / infra）或层级（如 monorepo 中的子项目）使用不同但相关的规则时，当前模型的局限：

1. **无作用域路由**：所有已加载的 pack 规则被全局合并，无法按工作目录/模块选择性应用
2. **同层无优先级**：两个 `project-local` pack 之间没有继承或优先级关系，冲突只能回退 review
3. **无增量继承**：子分区无法"继承父分区规则 + 覆盖少量差异"
4. **`depends_on` 仅为声明性**：只做存在性警告，不影响加载顺序或合并语义

### 目标场景

```
project/
├── .codex/packs/
│   ├── root.pack.json              # 项目全局规则
│   ├── frontend.pack.json          # 前端分区 (parent: root)
│   ├── backend.pack.json           # 后端分区 (parent: root)
│   └── backend-api.pack.json       # API 子模块 (parent: backend)
```

当 AI 在 `backend/api/` 目录下工作时，生效的规则链应是：

```
platform-default → official-instance → root → backend → backend-api
```

而在 `frontend/` 下工作时：

```
platform-default → official-instance → root → frontend
```

## 当前架构影响面分析

### 核心影响区（必须修改）

| 组件 | 文件 | 影响描述 | 风险 |
|------|------|---------|------|
| **PackManifest** | `src/pack/manifest_loader.py` | 新增 `parent` 字段、可能新增 `scope_paths` 字段 | 低——加字段 |
| **ContextBuilder** | `src/pack/context_builder.py` | 从扁平合并改为支持拓扑排序 + 作用域路由的合并策略 | **高**——核心变更 |
| **PackContext** | `src/pack/context_builder.py` | 可能需要区分"全局合并视图"与"当前作用域链视图" | 中 |
| **override_resolver** | `src/pack/override_resolver.py` | 需要感知 pack 在树中的位置计算优先级 | **高**——合并逻辑重写 |
| **precedence_resolver** | `src/pdp/precedence_resolver.py` | 需从单一 layer 比较升级为 (layer, depth) 二元组比较 | 中 |
| **Pipeline._discover_packs** | `src/workflow/pipeline.py` | 需解析 parent 引用、构建 pack 树 | 中 |
| **Pipeline._load_packs** | `src/workflow/pipeline.py` | 需拓扑排序、依赖链校验、作用域感知初始化 | **高** |
| **check_dependencies** | `src/pack/manifest_loader.py` | `parent` 隐式建立依赖，需统一处理 | 低 |
| **PackRegistrar** | `src/pack/registrar.py` | 考虑是否需要按分支隔离 validator 注册 | 中 |

### 安全区（不受直接影响）

这些组件均消费已合并好的 `RuleConfig`，只要上游合并正确，它们无需修改：

- `src/pdp/intent_classifier.py`
- `src/pdp/gate_resolver.py`
- `src/pdp/delegation_resolver.py`
- `src/pdp/escalation_resolver.py`
- `src/pep/executor.py`
- `src/pep/writeback_engine.py`
- `src/review/`
- `src/mcp/`（CLI / MCP 入口）
- `src/audit/`

### 权威文档影响

| 文档 | 变更类型 |
|------|---------|
| `docs/pack-manifest.md` | **必须更新**——新增 `parent` / `scope_paths` 字段规范 |
| `docs/precedence-resolution.md` | **必须更新**——新增层级内优先级语义 |
| `docs/plugin-model.md` | 更新——补充层级化 pack 能力 |
| `docs/project-adoption.md` | 更新——补充分区级 adoption 模式 |
| `docs/core-model.md` | 可能需要小幅补充"Rule 来源现在包含 pack 谱系" |
| `pack-manifest.md` schema versioning | `manifest_version` 需要 minor bump 到 `"1.1"` |

## 候选方案

### 方案 A：基于 `parent` 字段的树状继承

#### 概念

每个 pack manifest 可声明一个 `parent` 字段指向另一个 pack 名称，形成单继承树。

```json
{
  "name": "backend",
  "kind": "project-local",
  "parent": "root",
  "scope_paths": ["backend/", "services/backend-*"],
  ...
}
```

#### 规则合并

1. 构建 pack 树：根据 `parent` 字段建立父子关系
2. 拓扑排序：确保父 pack 先于子 pack 合并
3. 作用域路由：根据当前工作路径选取适用的 pack 链
4. 链式合并：沿 `platform → instance → [root → parent → ... → leaf]` 依次合并
5. 分支隔离：不在当前作用域链上的 pack 不参与合并

#### 优点

- 概念简单，单继承树容易理解和调试
- 与当前扁平模型向后兼容（无 parent = 根节点）
- 作用域路由自然——每条路径最多匹配一条链
- 冲突解析明确——树中越深的节点优先级越高

#### 缺点

- 不支持多继承（一个 pack 不能同时继承两个父 pack）
- 如果项目需要 cross-cutting concern（如"安全规则"跨所有分区），需要另外的合并机制

### 方案 B：基于 DAG 的拓扑合并

#### 概念

允许 `depends_on` 建立多父继承关系，pack 之间形成 DAG（有向无环图）。

```json
{
  "name": "backend-api",
  "kind": "project-local",
  "depends_on": ["backend", "api-security-policies"],
  "scope_paths": ["backend/api/"],
  ...
}
```

#### 优点

- 更灵活——支持 cross-cutting concern 和共享规则模块
- 更接近真实大型项目的需求

#### 缺点

- **合并冲突显著增加**——当两条路径提供相同规则时，需要定义复杂的冲突解决策略
- 实现复杂度高——需要完整的 DAG 拓扑排序 + MRO（方法解析顺序）风格的合并
- 调试困难——规则来源追溯变成多路径问题
- 对当前只有 advisory `depends_on` 的模型冲击过大

### 方案 C：树状继承 + 附加 mixin 层

#### 概念

结合方案 A 和 B 的优点：主结构为 `parent` 单继承树，额外支持 `mixins` 列表引入横切关注点。

```json
{
  "name": "backend-api",
  "kind": "project-local",
  "parent": "backend",
  "mixins": ["api-security-policies"],
  "scope_paths": ["backend/api/"],
  ...
}
```

合并顺序：先沿树链合并，再叠加 mixin（mixin 之间按声明顺序合并，但优先级低于直接继承链）。

#### 优点

- 主路径清晰（树），横切补充灵活（mixin）
- 冲突解析策略简单——树链 > mixin，mixin 之间按声明顺序

#### 缺点

- 需要额外定义 mixin 的合并语义
- 首版实现可以不做 mixin，只做树（退化为方案 A）

## 确认方案与分阶段策略

### 确认：方案 A（树状继承）为首版，方案 C（+mixin）为近期演化，方案 B 仅作理论保留

#### 理由

1. **用户需求直指"至少树状"**——方案 A 精确匹配这个要求
2. **与当前模型自然兼容**——无 `parent` 的 pack 仍按当前逻辑工作
3. **影响面可控**——不需要 MRO 算法，不需要重新定义 `depends_on` 语义
4. **mixin 作为近期演化**——C（树 + mixin）覆盖 cross-cutting concern；完整 DAG（B）可能永远不需要

#### 已确认设计决策

- **D4 = 选项 B（所有 pack 都参与树）**：platform-default / official-instance / project-local 都允许声明 `parent`。优先级模型从固定的 `kind` 三档升级为 `(kind, depth)` 二元组，树中同 kind 越深优先级越高。
- **scope 路由 = 显式传入（首版）**：MCP `governance_decide` 新增可选 `scope_path` 参数，不做自动推断。
- **实施节奏 = 逐 Slice 推进**：每个 Slice 完成验证后再进入下一个。
- **演化路径 = A→C**：B（完整 DAG）仅作理论保留，不作为规划目标。

### 分切片实施策略

考虑到对核心代码的影响面，建议按以下顺序拆分为 4 个窄切片：

#### Slice 1：Manifest 字段 + 树构建（低风险）

- PackManifest 新增 `parent`、`scope_paths` 字段
- 新增 `PackTree` 类：从 manifest 列表构建树结构
  - 循环检测、孤儿节点处理、根节点识别
- `manifest_version` 从 `"1.0"` bump 到 `"1.1"`
- 新增单元测试覆盖树构建与异常情况
- **不改变任何现有合并逻辑**——只建树、不消费

#### Slice 2：作用域路由 + 链式合并（**高风险核心**）

- ContextBuilder 新增 `build_scoped(scope_path: str)` 方法
  - 根据 `scope_paths` 匹配计算当前适用的 pack 链
  - 沿链合并（替代当前全局合并）
  - 原 `build()` 在无 scope 或无层级 pack 时保持原行为（向后兼容）
- override_resolver 的 `resolve()` 支持接收树深度信息参与优先级计算
- 新增测试：多链分支、默认回退、路径匹配边界

#### Slice 3：Pipeline 集成 + 作用域感知（中风险）

- Pipeline 新增 `scope_path` 可选参数（允许调用方指定当前工作上下文路径）
- `_load_packs` 构建 PackTree 并保存
- `process()` 可按 scope_path 路由到对应的 RuleConfig
- MCP / CLI 入口适配——透传 scope_path
- `info()` 输出增加 pack 树结构信息

#### Slice 4：文档 + 回归验证（低风险）

- 权威文档全面更新：`pack-manifest.md`、`precedence-resolution.md`、`plugin-model.md`、`project-adoption.md`
- 全套回归测试确认向后兼容
- 状态板 / Phase Map / 方向候选同步

### 预计影响范围

| 文件 | Slice | 变更类型 | 行数估计 |
|------|-------|---------|---------|
| `src/pack/manifest_loader.py` | 1 | 新增字段 | +10 |
| 新增 `src/pack/pack_tree.py` | 1 | 新文件 | ~120 |
| `src/pack/context_builder.py` | 2 | 新增方法 + 修改 build 逻辑 | +80, ~30 修改 |
| `src/pack/override_resolver.py` | 2 | 添加深度感知 | +20, ~10 修改 |
| `src/pdp/precedence_resolver.py` | 2 | 支持 (layer, depth) | +15 |
| `src/workflow/pipeline.py` | 3 | scope_path 路由 | +40, ~20 修改 |
| `src/mcp/tools.py` | 3 | 透传 scope_path | ~5 修改 |
| `src/pack/registrar.py` | 3 | 可选的分支感知 | +15 |
| 权威文档 ×4 | 4 | 更新 | +200 |
| 测试文件 ×3+ | 1-3 | 新增 | +300 |
| **合计** | | | ~800+ 行新增/修改 |

## 关键设计决策点

以下决策需在 planning-gate 阶段由用户确认：

### D1：scope_paths 匹配语义

- **选项 A**：简单前缀匹配（`backend/` 匹配所有 `backend/**` 路径）
- **选项 B**：glob 模式（`backend/**/*.py`）
- **选项 C**：前缀 + 排除模式

推荐：选项 A（简单前缀匹配），因为绝大多数分区场景是路径前缀划分。

### D2：无 scope 时的行为

- **选项 A**：退化为当前全局合并（向后兼容）
- **选项 B**：只应用所有树根 + 无 scope_paths 的 pack

推荐：选项 A，保证现有行为零变更。

### D3：同深度同 scope 冲突

当同一个 parent 下有两个子 pack 的 scope_paths 重叠时：

- **选项 A**：拒绝加载并报错
- **选项 B**：按声明顺序合并 + 警告
- **选项 C**：回退到 review

推荐：选项 A（拒绝 + 报错），因为 scope 重叠是配置错误而非运行时决策。

### D4：Platform / Instance 层是否参与树

- **选项 A**：仅 `project-local` pack 参与树，platform / instance 始终在链头
- **选项 B**：所有 pack 都可以参与树

**已确认：选项 B**——所有 pack 都参与树。这允许 official-instance 也有继承关系（如 `doc-loop-base` → `doc-loop-enterprise`），优先级模型从 `kind` 三档升级为 `(kind, depth)` 二元组。

### D5：RuleConfig 缓存策略

每次 `process()` 若按不同 scope_path 计算不同 RuleConfig：

- **选项 A**：每次按需计算，不缓存
- **选项 B**：预计算所有叶节点的 RuleConfig 并缓存

推荐：选项 B（预计算 + 缓存），因为 pack 数量有限（通常 <20），初始化时一次性计算所有链的成本可忽略。

## 前置条件

- 当前 `overrides` 字段尚未消费（gap analysis #12），层级化 pack 拓扑与 overrides 有天然关联——子 pack override 父 pack 是最自然的消费场景。建议在 Slice 2 中同步考虑 overrides 的语义。
- 当前 `manifest_version` 为 `"1.0"`，新增 `parent` / `scope_paths` 为可选字段，属于 minor bump（`"1.1"`），loader 兼容性不受影响。

## 风险与缓解

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| Slice 2 核心合并逻辑变更可能引入回归 | 高 | 保持原 `build()` 无参调用完全不变；scoped 路径只在新方法中生效 |
| 作用域路由歧义（多条路径同时匹配） | 中 | D3 决策中要求拒绝重叠 scope |
| 与 overrides 字段语义交叉 | 中 | Slice 2 设计时统一考虑 |
| 测试组合爆炸（多层级 × 多分区 × 多 pack） | 中 | 以典型 2-3 层深的树 + 3 分支覆盖即可 |
| 性能——大量 pack 时树构建开销 | 低 | 实际场景 pack 数 <20，不构成瓶颈 |

## 开放问题

1. 当前 `scope` 字段（manifest 已有）与新的 `scope_paths` 是什么关系？是否应将 `scope` 改为 `scope_paths`？
2. `PackRegistrar` 是否需要按 scope chain 隔离 validator 注册？还是保持全局注册但在执行时过滤？
3. MCP `governance_decide` tool 如何获取 scope_path？是从用户输入推断、从 MCP 上下文获取、还是要求显式传入？
