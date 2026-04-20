# Pack Manifest

## 文档定位

本文件定义平台中 `Pack Manifest` 的最小规范。

它的作用是让一个 pack 能够声明：

- 自己是谁
- 属于哪一层
- 提供哪些能力
- 哪些内容是 always-on
- 哪些内容是 on-demand
- 它依赖谁、覆盖谁

本文件当前只定义对象、字段和不变量，不绑定最终文件格式。

## 解决什么问题

如果没有统一的 manifest：

- pack 提供了什么很难快速判断
- precedence 与 override 关系容易只停留在口头说明
- 平台无法稳定知道该装载哪些上下文与扩展件

因此，manifest 是 pack 的**能力声明面**，不是运行时状态记录。

## 不解决什么问题

本文件当前不解决：

- 远端分发协议
- 安装与发布流程
- 签名、校验和安全模型
- 最终使用 YAML、JSON 还是其他格式

## 核心定位

`Pack Manifest` 应被理解为：

- pack 的身份证
- pack 的能力目录
- pack 的装载与覆盖声明

它不应被理解为：

- pack 内部规则正文
- 运行时状态快照
- 市场元数据中心

## 最小字段

### 身份字段

- `manifest_version`
  - manifest JSON 结构的格式版本
  - 当前版本：`"1.0"`
  - 格式：`"<major>.<minor>"`
  - 若缺失，loader 默认按 `"1.0"` 处理（后向兼容）
  - 参见下方 §Schema Versioning
- `name`
  - pack 的稳定名称
- `version`
  - pack 的版本标识（pack 内容版本，与 manifest_version 分离）
- `kind`
  - pack 类型
  - 当前支持：
    - `platform-default` — 平台内置默认 pack（优先级 0）
    - `official-instance` — 官方实例 pack（优先级 1）
    - `user-global` — 用户全局 pack，存放在 `~/.doc-based-coding/packs/`（优先级 2）。可通过环境变量 `DOC_BASED_CODING_USER_DIR` 覆盖 home 目录
    - `project-local` — 项目级 pack（优先级 3，最高）
- `scope`
  - 适用范围说明

### 拓扑与路由字段

- `parent`
  - 当前 pack 在单继承树中的父 pack 名称
- `scope_paths`
  - runtime 作用域路由使用的路径前缀列表

### 能力声明字段

- `provides`
  - 声明该 pack 提供了哪些能力槽位
- `document_types`
  - 该 pack 引入或定义的文档类型
- `intents`
  - 该 pack 扩展或细化的 interaction intent
- `gates`
  - 该 pack 额外使用或约束的 gate 语义

### 上下文装载字段

- `always_on`
  - 默认常驻上下文
- `on_demand`
  - 按需加载内容

### 依赖与覆盖字段

- `depends_on`
  - 依赖哪些 pack 或能力
- `runtime_compatibility`
  - 声明该 pack 兼容的平台 runtime 版本范围
- `overrides`
  - 显式声明覆盖哪些 pack 或规则来源

### 扩展件字段

- `prompts`
  - 该 pack 暴露的提示词面
- `templates`
  - 模板与 scaffold
- `validators`
  - runtime 可调用的 validator 列表
- `checks`
  - runtime 可调用的 writeback gate 检查
- `scripts`
  - 独立执行脚本
- `triggers`
  - 事件输入入口

## 字段设计原则

### `provides`

`provides` 用于回答“这个 pack 具备哪些能力面”，而不是直接塞入完整内容。

例如它可以声明：

- `rules`
- `document_types`
- `prompts`
- `validators`
- `triggers`

Runtime 当前会将所有已加载 pack 的 `provides` 合并为 `PackContext.merged_provides`，并注入 `RuleConfig.available_capabilities`。

在 v1.0 之后的 delegation 路径中，这些能力会被用作 advisory capability check：

- 若某个可委派 intent 通常需要的能力未出现在 merged provides 中，delegation 结果会附带 `capability_warnings`
- 该 warning 不会阻塞委派，但会将 `requires_review` 升级为 `true`
- 能力需求映射当前保持简单、可由 pack rules 覆盖，不做版本级或细粒度匹配

### `always_on` 与 `on_demand`

这两个字段不是简单的文件列表，而是上下文装载声明。

它们的区别是：

- `always_on`
  - 会直接参与高层行为塑形
- `on_demand`
  - 只在需要时展开

### `parent` 与 `scope_paths`

这两个字段共同定义 pack 的层级拓扑与作用域路由：

- `parent`
  - 把当前 pack 挂到另一个 pack 之下，形成单继承树
  - 空串表示该 pack 是根节点，或作为独立 pack 存在
- `scope_paths`
  - 用于声明该 pack 作用于哪些文件/目录路径
  - 当前 runtime 采用简单前缀匹配，而不是 glob 或正则

需要区分：

- `scope`
  - 面向人类阅读的适用范围描述
- `scope_paths`
  - 面向 runtime 的机器可消费路由前缀

当前 runtime 语义是：

- 所有已加载 pack 都可以参与树（`platform-default`、`official-instance`、`user-global`、`project-local`）
- 当调用方显式传入 `scope_path` 时，runtime 会先解析匹配的 pack 链，再只合并这条链上的 pack
- 若未传入 `scope_path`，或没有任何 pack 命中该路径，则退回全局合并行为
- 同一个 parent 下多个子 pack 的 `scope_paths` 若发生重叠，属于配置错误，应在加载时拒绝，而不是留给运行时决定

### `depends_on`

用于声明：

- 此 pack 依赖哪些基础能力
- 若缺少这些能力，pack 是否仍可部分工作

当前阶段先只要求表达依赖关系，不要求定义复杂求解算法。

**Runtime 校验行为（v1.0）**：Pipeline 初始化时会对所有已加载 pack 的 `depends_on` 条目做交叉校验——检查每个声明的依赖名称是否出现在已发现的 pack 名称集合中。未解析的依赖会以 `logging.warning` 输出，并记入 `Pipeline.info()["dependency_status"]` 的 `unresolved` 列表，但不阻塞 pack 加载或治理链。

特殊名称 `"platform-core-defaults"` 被视为虚拟依赖（始终 resolved），无需对应实际 manifest。

### `runtime_compatibility`

当 pack 需要对某个平台 runtime 版本范围作出明确承诺时，应使用 `runtime_compatibility` 表达语义层兼容范围。

当前首版固定为：

- 字段类型为字符串
- 值表达“此 pack 兼容哪些 runtime 版本范围”
- 它与发行包依赖中的版本范围应保持一致，但不替代发行包依赖本身

因此：

- `depends_on` 解决的是“逻辑上依赖谁”
- `runtime_compatibility` 解决的是“与哪个 runtime 版本范围可以稳定协作”

### `overrides`

用于声明：

- 该 pack 准备覆盖谁（以 pack 名称列表表示）
- 覆盖是否显式

它不应绕开平台的 precedence 规则。

Runtime 消费语义：

- `ContextBuilder` 在合并时提取所有 pack 的 `overrides` 声明到 `PackContext.merged_overrides`
- `check_overrides()` 验证所有覆盖目标是否存在于已加载 pack 集合中（warning-only，不阻塞）
- `PrecedenceResolver` 在仲裁结果中标注 `explicit_override: true` 当胜出 pack 显式声明了对失败 pack 的覆盖
- `Pipeline.info()` 暴露 `override_declarations` 与 `override_warnings`

当前 `overrides` 是 `list[str]`（pack 名称列表），不携带覆盖理由或条件。若未来出现需要覆盖理由的真实场景，可升级为 `list[str | object]`（manifest_version minor bump），已有消费代码天然兼容。

### `validators` / `checks` / `scripts`

这三个字段虽然都可能指向“某段扩展逻辑”，但它们在 runtime 中的消费语义不同，不能混用：

- `validators`
  - 用于声明会被 runtime 注册进 `ValidatorRegistry` 的 validator。
  - 这类扩展应能被平台直接调用，并消费 runtime 传入的数据对象。
  - 当前实现里，它们会在 delegation 后对 report 一类数据执行校验。
- `checks`
  - 用于声明会在 writeback 前执行的 gate check。
  - 这类扩展消费的是 writeback 前的执行上下文，而不是独立 CLI 输入。
  - 当前实现里，它们会由 `PackRegistrar` 自动注册进 `ValidatorRegistry`，并在 `Executor` writeback 前调用。
- `scripts`
  - 用于声明独立的操作型脚本，例如 bootstrap、adoption 自检、实例自检等。
  - 这类脚本可以只有 CLI `main()` 入口，不应因为名称像 `validate_*` 就自动放进 `validators`。

因此，repo scaffold 校验、官方实例自检、bootstrap 一类命令，默认应归入 `scripts`，而不是归入 runtime `validators`。

## Schema Versioning

### 为什么需要 manifest_version

`version` 描述的是 pack 内容的语义版本（如 `"1.0.0"`）。但 pack manifest 的 JSON 结构本身也需要一个版本号来指示格式变化，以便：

- loader 判断是否能正确解析该 manifest
- 新增字段时，旧版 loader 能安全降级或报告不兼容
- 避免因字段重命名或语义变更导致静默加载错误

`manifest_version` 使用 `"<major>.<minor>"` 格式（不含 patch），因为 manifest 格式变更的粒度不需要三段版本号。

### 兼容策略

| 变更类型 | 版本影响 | 示例 |
|---------|---------|------|
| 新增可选字段 | 可保持不变，或在需要显式宣告新 schema surface 时 minor bump | 加 `parent` / `scope_paths`；或加 `shipped_copies` 到 rules |
| 修改字段语义 | major bump | `always_on` 从路径列表改为对象数组 |
| 移除字段 | major bump | 删除 `triggers` |
| 新增必需字段 | major bump | 要求某字段必须存在 |

### Loader 行为

| 场景 | 行为 |
|------|------|
| `manifest_version` 缺失 | 视为 `"1.0"`（后向兼容） |
| `manifest_version` == 当前版本 | 正常加载 |
| `manifest_version` major > 当前支持 | 抛出 ValueError |
| `manifest_version` minor > 当前支持 | 正常加载 + 日志警告 |

### manifest_version 与 version 的关系

```
manifest_version  →  manifest JSON 结构的格式版本
version           →  pack 内容的语义版本
```

这两个版本独立演进。一个 pack 可以在不改变 manifest 格式的情况下多次发布内容更新（只 bump `version`），也可以在一次格式变更中不改变 pack 内容（只 bump `manifest_version`）。

当前已落地的 `parent` / `scope_paths` 仍属于 `manifest_version = "1.0"` 范围内的后向兼容可选字段，因为旧 loader 即使忽略它们，也不会误解已有字段的含义。

## 不变量

`Pack Manifest` 至少应满足以下不变量：

- 一个 manifest 只能描述一个 pack。
- manifest 声明的是能力与关系，不是运行时状态。
- manifest 不应内联大段规则正文。
- `always_on` 与 `on_demand` 应只引用该 pack 可装载的内容。
- `overrides` 不得假定自己能绕过平台核心 precedence。
- 未声明的能力不应被默认视为该 pack 提供。

## 与平台核心的关系

`Pack Manifest` 服务于：

- `Policy Decision Point`
  - 用于知道当前有哪些可用能力与覆盖关系
- `Policy Enforcement Point`
  - 用于知道有哪些 prompts、templates、validators、scripts 可被调用

它同时也是：

- `Always-On Context`
- `On-Demand Pack Content`

这两个抽象的入口声明面。

## 与实例的关系

官方实例和项目级实例都应能通过 manifest 暴露自己的能力。

例如 `doc-driven vibe coding` 未来应能通过 manifest 声明：

- 文档类型
- write-back 规则
- handoff 规则
- 子 agent 合同模板
- 相关 prompts / validators / scripts

## 当前边界

本文件已经固定了：

- `Pack Manifest` 的职责
- 最小字段集合
- 基本不变量
- 官方实例可用 `runtime_compatibility` 声明最小 runtime 兼容范围

本文件尚未固定：

- 目录布局
- 字段最终类型系统
- 最终序列化格式
- 更完整的版本兼容矩阵与求解策略

## 开放问题

- `scope` 是否需要进一步拆成 `audience` 与 `workspace_scope`
- `provides` 是否需要固定枚举
- `depends_on` 是否需要区分强依赖与软依赖
- ~~`overrides` 是否需要携带覆盖理由或条件~~ — 已回答：当前不需要，保持 `list[str]`；若未来需要，可升级为 `list[str | object]`（方案 C 储备路径）
