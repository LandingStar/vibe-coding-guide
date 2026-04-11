# Dual-Package Distribution Standard

## 文档定位

本文件定义 `doc-based-coding-platform` 在“可供其他项目安装使用”这一目标下的第一版长期分发标准。

当前只固定一件事：

- 平台 runtime 与官方实例资产应拆成两个发行包
- 两个发行包各自负责什么
- 两者之间的依赖方向和最小兼容关系是什么

本文件当前不定义最终 distribution/import 命名、发布渠道和自动化流水线；但会固定最小兼容原则与最小验证门。

## 适用范围

本标准适用于：

- 平台 runtime 的对外安装与分发
- 官方实例 `doc-loop-vibe-coding` 的对外安装与分发
- 目标仓库通过安装包而不是源码 checkout 来采用平台与官方实例的场景

本标准当前不适用于：

- project-local pack 的最终安装器协议
- 远程 registry / marketplace
- 多官方实例同时挂载同一仓库时的冲突消解
- 发布自动化流水线

## 为什么采用双发行包

当前仓库现实状态表明“平台 runtime”和“官方实例资产”虽然协作紧密，但职责并不相同：

1. `src/` 提供的是 runtime、CLI、MCP server、Pipeline 等执行面。
2. `doc-loop-vibe-coding/` 提供的是官方实例 pack manifest、bootstrap scaffold、prompts、templates、validators、examples 等实例资产。
3. `docs/project-adoption.md` 已经把“平台 / 官方实例 / project-local pack”定义成三层 adoption 模型，因此若把 runtime 与官方实例继续捆成单一发行包，会削弱这种分层。

因此首版对外安装标准采用双发行包：

- 一个发行包承载平台 runtime
- 一个发行包承载官方实例资产

## 发行包 A：平台 Runtime 包

平台 runtime 包负责提供与实例无关的执行能力。

### 必须负责

- 平台核心 Python 模块与 API
- CLI 入口
- MCP server 入口
- Pipeline / governance runtime
- pack 加载、上下文合并、规则消解、审计、约束检查等通用运行时

### 当前对应面

- `src/__main__.py`
- `src/mcp/`
- `src/workflow/`
- `src/pack/`
- `src/pdp/`
- `src/pep/`

### 不应负责

- 内嵌 doc-loop 官方实例私有模板
- 内嵌 project-local 仓库状态文档
- 假定目标仓库一定采用 doc-loop 实例
- 使用当前开发仓库的本地路径作为安装后标准入口

## 发行包 B：官方实例包

官方实例包负责提供某个 workflow pack 的可安装资产，而不是平台 runtime 本身。

### 必须负责

- 实例级 pack manifest
- bootstrap scaffold
- prompts
- templates
- validators / scripts
- examples / references

### 当前对应面

- `doc-loop-vibe-coding/pack-manifest.json`
- `doc-loop-vibe-coding/scripts/`
- `doc-loop-vibe-coding/assets/`
- `doc-loop-vibe-coding/examples/`
- `doc-loop-vibe-coding/references/`

### 不应负责

- 重新实现平台 runtime
- 修改平台核心 precedence / gate 语义
- 携带 project-local 临时状态
- 假定自己拥有唯一的运行时入口解释权

## 依赖方向

双发行包的依赖方向固定如下：

1. 平台 runtime 包不依赖任何特定官方实例包。
2. 官方实例包可以依赖一个最小兼容范围内的平台 runtime 包。
3. 目标项目若采用 doc-loop 官方实例，应安装官方实例包；该实例包可以通过依赖关系拉起所需 runtime。
4. project-local pack 继续在语义层 `depends_on` 官方实例 pack，而不是直接依赖某个源码仓库路径。

该依赖方向的目的，是保持：

- runtime 对实例保持中立
- 实例对 runtime 明确绑定
- adoption 层继续遵守“平台 -> 官方实例 -> 项目本地”的三层结构

## 最小兼容关系

当前先固定最小原则，不展开完整版本矩阵：

1. 官方实例包必须声明其兼容的平台 runtime 版本范围。
2. 若官方实例包未声明兼容范围，不应视为可稳定安装。
3. 平台 runtime 的稳定升级不应默认要求所有实例同步改名或改入口。
4. 官方实例若依赖 runtime 的新能力，应通过版本范围而不是隐式文档约定来表达。

### 兼容声明层级

兼容关系至少应在两个层面被表达：

1. 发行包元数据层
	- 用于让安装器和依赖求解先做第一轮约束过滤。
2. pack / 实例语义层
	- 用于让人和 runtime 明确知道该实例针对哪个 runtime 语义面设计。

当前首版实现中，pack / 实例语义层的最小声明字段固定为：

- `runtime_compatibility`
	- 值为字符串版本范围
	- 用于表达官方实例兼容的平台 runtime 版本范围
	- 不替代发行包依赖，仅补齐语义层声明

当前应特别区分：

- `depends_on` 表达的是逻辑依赖关系
- 版本兼容表达的是“哪些版本组合可以稳定工作”

因此，`depends_on` 不能替代版本兼容声明。

### 默认兼容预期

在未引入更细粒度策略前，当前标准采用以下默认预期：

1. runtime 包的 patch 级修复不应无故打破已声明兼容的官方实例包。
2. runtime 包的 minor 级扩展可以增加新能力，但不应要求已兼容的官方实例立刻升级才能继续工作。
3. runtime 包若发生 major 级不兼容变更，官方实例包必须重新审阅并显式更新兼容声明。
4. 官方实例包若只更新 prompts、templates、examples、references 等静态资产，且不依赖 runtime 新行为，可维持原兼容范围。
5. 官方实例包若开始依赖 runtime 新入口、新协议或新装载语义，必须显式抬高最低兼容 runtime 版本。

## 安装入口归属

双发行包虽然都可以安装，但“谁暴露什么入口”必须分清。

### 平台 Runtime 包负责暴露的入口

凡是需要执行平台 runtime 语义的入口，都由平台 runtime 包负责暴露。

包括：

- governance / pipeline CLI 主入口
- MCP server 启动入口
- `generate-instructions` 这类基于 PackContext 的通用运行时入口
- 其他依赖 `src/workflow/`、`src/mcp/`、`src/pdp/`、`src/pep/` 的执行型命令

理由：

- 这些入口本质上消费的是平台 runtime，而不是某个特定实例的静态资产
- 同一个 runtime 未来应能承载多个官方实例，而不是把 CLI / MCP 入口绑死在 doc-loop 上

### 官方实例包负责暴露的入口

凡是直接面向 doc-loop 官方实例资产的入口，由官方实例包负责暴露。

包括：

- bootstrap scaffold
- 实例 pack 自检
- 目标仓库的 doc-loop scaffold 校验
- 其他只依赖 manifest、templates、prompts、validators、examples、references 的实例专属工具

按当前仓库现实状态，对应的就是：

- `bootstrap_doc_loop.py`
- `validate_doc_loop.py`
- `validate_instance_pack.py`

理由：

- 这些入口描述的是“如何采用 doc-loop 官方实例”，而不是“如何运行平台本体”
- 若未来存在第二个官方实例，这些入口不应被放进通用 runtime 包里共同命名和维护

### 不允许的混合方式

以下做法不应成为安装态标准：

- 由官方实例包直接充当 MCP server 进程
- 由平台 runtime 包内嵌 doc-loop bootstrap 模板并把它们当作默认必带资产
- 通过当前源码仓库中的相对路径来假定命令归属

## 安装态 MCP 接入标准

MCP 接入在安装态下必须遵守“消费已安装 runtime，而不是消费发布者源码工作区”的原则。

### 必须满足

1. MCP server 进程由平台 runtime 包提供并启动。
2. MCP 配置使用的是目标项目当前环境中的解释器或等价启动器，而不是发布者工作区里的固定 `.venv` / `.venv-mcp` 路径。
3. MCP 配置引用的是安装后的 runtime 入口，不再直接写 `src.mcp.server` 这种源码仓库模块路径。
4. MCP server 的工作目录应指向目标项目根目录，使其能基于目标仓库的 `design_docs/`、`.codex/` 与 pack 配置恢复上下文。
5. 官方实例包通过 pack/adoption 机制被 runtime 发现和消费，而不是在 MCP 配置层被单独当成 server 进程启动。

### 开发态与安装态的区分

当前仓库中的 [ .vscode/mcp.json ](.vscode/mcp.json) 属于开发态配置示例，而不是安装态标准。其作用是：

- 便于本仓库 dogfood 当前实现
- 便于在 workspace 内直接启动 `doc-based-coding-governance`

但它不应被复制为对外文档中的最终接入方式，因为它仍然依赖：

- 当前仓库自己的 `.venv-mcp`
- 当前仓库源码树里的 `src.mcp.server`

### 标准化后的角色分工

- 运行时如何启动 MCP：由平台 runtime 包定义
- doc-loop 项目要准备哪些文档与 pack：由官方实例包和 adoption 文档定义
- 某个目标仓库如何把二者绑定到自己的 workspace：由 project-local pack 与目标仓库配置负责

因此，安装态 MCP 接入不应把“server 可执行入口”和“doc-loop 实例资产入口”混为一层。

## 最小验证门

双发行包标准在进入实现前，至少要有一套能证明“安装形态成立”的最小验证门。

### A. clean environment 安装验证

必须能在干净环境中分别证明：

1. 只安装平台 runtime 包时：
	- runtime CLI 主入口可发现
	- MCP server 入口可启动
	- 不依赖 doc-loop 实例资产也能完成基础 runtime 初始化
2. 安装平台 runtime 包 + 官方实例包时：
	- 官方实例专属入口可发现
	- 实例资产可被稳定读取
	- runtime 能识别并消费已安装的官方实例资产

### B. adoption 验证

针对采用 doc-loop 官方实例的目标仓库，至少应验证：

1. 能用官方实例包提供的 bootstrap 入口生成最小 scaffold。
2. 能用官方实例包提供的校验入口验证 scaffold 与 project-local pack。
3. project-local pack 对官方实例 pack 的逻辑依赖仍然成立。
4. 平台 runtime 入口在目标仓库内仍能读取 `design_docs/`、`.codex/` 与 pack 配置恢复上下文。

### C. runtime smoke 验证

安装态下至少应覆盖以下 smoke 范围：

1. runtime CLI 必须覆盖当前稳定面等价能力：
	- process
	- check
	- validate
	- info
	- generate-instructions
2. MCP 工具至少应覆盖当前稳定面等价能力：
	- `check_constraints`
	- `governance_decide`
3. 任一入口都不应依赖发布者源码工作区里的硬编码路径。

### D. 失败判定

以下任一情况出现时，不应宣称双发行包安装标准已达成：

- runtime 入口只能从源码仓库模块路径启动
- 官方实例资产必须靠源码 checkout 才能读取
- MCP 配置仍要求引用发布者工作区的固定虚拟环境路径
- bootstrap / validate / generate-instructions 的归属仍然混乱
- 兼容关系只能靠口头说明，无法从安装与文档层共同恢复

## 当前仓库对该标准的直接影响

根据当前仓库现实状态，这个标准意味着：

- 当前 `.vscode/mcp.json` 中直接引用 workspace 本地 `.venv-mcp` 与 `src.mcp.server` 的做法，只能视为开发态配置，不是安装态标准。
- 当前 `python -m src` 与 `python -m src.mcp.server` 只说明 runtime 已具备模块入口，不等于已经满足可分发标准。
- `doc-loop-vibe-coding/` 需要被视为未来可安装实例包的资产源，而不是仅仅保存在仓库里的原型目录。
- `generate-instructions` 应继续归平台 runtime 侧，而 bootstrap / validate-doc-loop / validate-instance-pack 应归官方实例包侧。

## 子 agent 边界

当前这份标准属于权威边界定义，不交给子 agent 维护。

后续若进入窄 scope 调研，可将以下工作委派给子 agent：

- Python 打包 backend 对比
- package data 打包方式对比
- 安装后入口形态对比

但最终标准结论、文档写回与共享状态同步继续由主 agent 负责。

## 当前边界

本文件当前只固定：

- 双发行包模型
- runtime 包职责
- 官方实例包职责
- 依赖方向
- 最小兼容原则
- 安装入口归属
- 安装态 MCP 接入原则
- 最小验证门

本文件当前不固定：

- distribution name / import name 最终命名
- CLI / bootstrap / validator / MCP 的安装后命令名
- wheel / sdist 构建方案
- 发布渠道与自动化流程
- 更完整的兼容矩阵
- 自动化发布回归流程