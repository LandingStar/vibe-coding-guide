# Project Adoption

## 文档定位

本文件定义一个真实项目如何采用平台，并在官方实例之上叠加项目级 overlay pack。

它回答的是：

- 一个仓库如何接入平台
- 官方实例与项目本地规则如何叠加
- 项目级 pack 负责什么，不负责什么
- 采用后应如何校验

它不重复平台核心对象定义，也不替代某个官方实例内部规则。

## 为什么需要这一层

如果只有平台 schema 和官方实例原型，而没有项目接入协议，就会出现几个问题：

- 不清楚一个真实仓库从哪里进入这套系统
- 不清楚项目定制应该写在实例里还是写在项目本地
- 不清楚 overlay pack 的最小职责是什么
- 不清楚 adoption 完成后如何校验

因此，平台需要一份专门描述“仓库如何挂上来”的权威文档。

## 采用模型

当前平台建议按三层理解 adoption：

1. 平台权威文档
   - 定义核心对象、优先级、gate、review、subagent 语义
2. 官方实例 pack
   - 定义某类 workflow 的通用组织方式
3. 项目级本地 pack
   - 把官方实例绑定到某个真实仓库的文档路径、长期规则和局部约束

这意味着：

- 平台层回答“系统是什么”
- 官方实例回答“某种工作流如何落在系统上”
- 项目级 pack 回答“这个仓库如何采用这个工作流”

在大型项目中，项目级 pack 还可以进一步形成树状层级：根 pack 负责仓库级通用规则，子 pack 负责具体分区或子模块规则。

## Project-Local Pack 的角色

项目级 pack 应被理解为：

- 真实仓库的治理 overlay
- 官方实例在当前仓库内的落地点
- 项目特有规则、文档入口、prompt、模板和校验的声明面

它至少可以负责：

- 声明仓库级 `always_on` 上下文
- 声明仓库级 `on_demand` 内容
- 绑定当前仓库的文档路径
- 添加项目专有 prompt、template、validator、check、script
- 对官方实例默认行为做显式 overlay

它当前不应负责：

- 重定义平台 actor model
- 绕过平台 precedence
- 偷偷改写 gate 的核心语义
- 把项目临时状态写进 manifest

## 优先级与叠加

当前推荐的理解顺序为：

1. 用户当前回合的明确决定
2. workspace 现实状态
3. 项目级本地 pack
4. 官方实例 pack
5. 平台核心默认规则

其中：

- 项目级 pack 可以覆盖官方实例的项目化细节
- 官方实例 pack 可以提供领域化 workflow
- 平台核心语义仍应由权威文档定义

如果发生无法自动消解的冲突，应回退到 review，而不是让 AI 自行硬判。

## 最小采用路径

一个项目采用某个官方实例时，建议至少经过以下步骤：

1. 选择一个官方实例 pack
   - 例如当前仓库中的 `doc-driven vibe coding`
2. 将实例 scaffold 引入目标仓库
   - 例如通过 bootstrap 脚本复制文档骨架、prompt、contract 模板
3. 在目标仓库创建项目级 pack manifest
   - 作为当前仓库的 overlay 入口
4. 识别哪些内容应成为 `always_on`
   - 例如项目总状态板、阶段图、长期工作流规则
5. 识别哪些内容应成为 `on_demand`
   - 例如阶段模板、局部合同、辅助说明
6. 补齐项目级长期文档
   - 使主 AI 可以通过文档恢复上下文并执行 write-back
7. 运行校验
   - 确认 scaffold、project-local pack 和最小合同资产存在且语义合理

## Doc Loop 官方实例的采用方式

当前官方实例 `doc-driven vibe coding` 采用的项目接入形状是：

- 官方实例自身提供 `pack-manifest.json`
- bootstrap 后的目标仓库提供 `.codex/packs/project-local.pack.json`
- 项目级 pack 通过 `depends_on = ["doc-loop-vibe-coding"]` 显式依赖官方实例

在这个实例里，项目级 pack 默认应至少把以下内容纳入仓库治理入口：

- `AGENTS.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`

这些内容之所以默认进入 `always_on`，是因为它们直接影响当前仓库中的高层判断、上下文恢复与 write-back 收口。

## 大型项目 / Monorepo 采用形状

当一个仓库内部存在多个相对独立的分区（如 `frontend/`、`backend/`、`infra/`），项目级 adoption 不必再退回“一个 project-local pack 包打天下”。当前推荐形状是：

```text
.codex/packs/
   root.pack.json
   frontend.pack.json
   backend.pack.json
   backend-api.pack.json
```

其中：

- `root` 负责整个仓库共享的治理 overlay
- `frontend` / `backend` 通过 `parent = "root"` 继承公共规则并覆盖各自分区差异
- 更深的模块（如 `backend-api`）可以继续挂在局部父节点之下

典型字段分工是：

- `scope`
   - 写给人看的适用范围描述
- `scope_paths`
   - 写给 runtime 的路径前缀，如 `frontend/`、`backend/api/`

## Scoped Adoption

当前 runtime 的作用域化 adoption 采用显式模式：

- 宿主调用方在需要局部治理时，应显式传入 `scope_path`
- runtime 根据 `scope_path` 解析 pack tree，并只装载命中的 root → leaf 链
- 若没有传入 `scope_path`，则仍保持原有全局合并行为，保证旧项目 adoption 不被破坏

这意味着：

- 新项目可以逐步引入层级 pack，而不必一次性重构所有现有 pack
- 旧项目即使完全不知道 `parent` / `scope_paths`，也不会因为升级 runtime 而失效

## 项目级定制应该落在哪里

当前推荐分工如下：

- 平台级变化
  - 回写 `docs/`
- 官方实例级变化
  - 回写实例 pack 的规则、模板、脚本或示例
- 项目特有变化
  - 回写目标仓库中的 project-local pack 与项目长期文档

一个简单判断方法是：

- 如果多个项目都应该共享，优先考虑实例层或平台层
- 如果只对某个仓库成立，优先放在 project-local pack

## Validation

项目 adoption 完成后，至少应验证两件事：

1. 官方实例本身是自洽的
   - 实例 manifest、示例 schema、bootstrap 资产互相对齐
2. 目标仓库的接入面是自洽的
   - 项目级 pack 能正确指向文档、prompt、contract 模板与长期规则

对于当前 `doc-loop-vibe-coding` 原型，建议至少运行：

- 安装态入口：`doc-loop-validate-instance`
- 安装态入口：`doc-loop-validate-doc --target <repo>`
- 源码 checkout 备用入口：`python doc-loop-vibe-coding/scripts/validate_instance_pack.py --target doc-loop-vibe-coding`
- 源码 checkout 备用入口：`python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target <repo>`

完整安装步骤见：

- `installation-guide.md`

## Human Review In Adoption

项目 adoption 不是一次性复制模板，而是一次治理绑定。

因此在 adoption 阶段，人应重点审阅：

- 项目级 `always_on` 是否过宽或过窄
- 项目级长期文档是否足以恢复上下文
- 是否把本应属于平台或实例的规则误写到了项目本地
- 项目级 overlay 是否显式，而不是靠隐含约定

## 当前边界

本文件当前固定的是：

- adoption 的三层模型
- project-local pack 的职责边界
- 最小采用路径
- 当前官方实例的项目接入形状

本文件当前不固定：

- 安装器协议
- 远程 registry
- manifest 最终序列化格式
- 多实例同时挂载同一仓库时的冲突求解算法
