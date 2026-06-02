# Semantic Versioning and Packaging Standard

## 文档定位

本文定义本仓库打包与发布时的版本号标准。版本号规则依据 Semantic Versioning 2.0.0（https://semver.org/），并结合当前 Python wheel、官方实例包、VS Code VSIX 与 release zip 的真实打包路径收窄第一版可执行边界。

本文是长期 tooling 标准；具体某次 release 的版本号仍由 release gate 或用户发布决策确定。

## SemVer 基线

发布版本号必须遵守 SemVer 2.0.0：

1. 正式版本号格式为 `MAJOR.MINOR.PATCH`。
2. `MAJOR` 表示不兼容变更。
3. `MINOR` 表示向后兼容的新能力。
4. `PATCH` 表示向后兼容的问题修复。
5. 预发布版本可表达为 `MAJOR.MINOR.PATCH-prerelease`。
6. 构建元数据可表达为 `MAJOR.MINOR.PATCH+build`。
7. 版本一旦发布，对应内容不可修改；任何变更必须发布新版本。
8. 对外 artifact 文件名可以带 `v` 前缀作为人类可读标签，但包元数据中的版本号不得带 `v`。

## 当前可打包版本号边界

当前打包入口只接受 SemVer 正式版本核心：`MAJOR.MINOR.PATCH`。

理由：

1. Python package metadata、wheel 文件名、VS Code extension package 与 release zip 当前共用同一发布流程，但对 pre-release / build metadata 的兼容细节不完全一致。
2. 当前 release 脚本已有 `--version` 覆盖 zip 名能力；如果允许任意字符串，会造成 zip 批次号与 wheel / VSIX 元数据语义漂移。
3. 第一版标准先固定可执行、安全的发布面；后续若需要 `-alpha`、`-rc.1` 或 `+build`，必须先扩展脚本、文档和验证矩阵。

因此：

- 合法包元数据版本示例：`0.9.7`、`1.0.0`、`2.3.4`
- 当前不允许用于实际打包的版本示例：`v1.0.0`、`1.0`、`1.0.0-rc.1`、`1.0.0+build.7`
- release zip 文件名继续使用 `doc-based-coding-vX.Y.Z.zip`，其中 `v` 只属于文件名标签，不属于包版本号。

## 版本线

当前仓库至少存在四条版本线：

1. Runtime wheel：`pyproject.toml` 中 `doc-based-coding-runtime` 的版本。
2. Official instance wheel：`doc-loop-vibe-coding/pyproject.toml` 与 `doc-loop-vibe-coding/pack-manifest.json` 的版本。
3. VS Code extension VSIX：`vscode-extension/package.json` 的版本。
4. 外部前端组件：例如 `@note-web/knowledge-graph-engine`，由组件仓库独立声明 SemVer。

当前双 wheel 发布批次要求 runtime 与 official instance 使用同一个 `MAJOR.MINOR.PATCH`。官方实例的 `runtime_compatibility` 必须同步表达可兼容 runtime 范围。

VS Code extension 可以保持独立版本线，但每次 release zip 若携带 VSIX，release note 必须显式列出 VSIX 版本，避免误认为它与 Python wheel 版本完全同线。

外部前端组件不并入宿主源码长期维护。发布态应固定为以下模型：

1. 组件仓库独立打包并声明自身版本。
2. 宿主 `vscode-extension` 依赖固定组件版本、registry 版本或 release-local tarball。
3. VSIX 运行时必须自包含已构建的 webview JS / worker，用户安装 VSIX 后不需要单独安装组件 npm 包。
4. release zip 可携带组件 tarball 作为可复现构建材料，但 VSIX 内不应再携带 `node_modules/` 或 `vendor/` 原始包。
5. `file:` 依赖只允许指向当前 extension 目录内的 release-local `vendor/` tarball；不得依赖发布者机器上的外部源码工作区路径。

## Bump 判定

### Runtime wheel

Runtime wheel 的 bump 依据稳定公开面判断，公开面包括 CLI、MCP server、Pipeline API、pack runtime、PDP/PEP 语义和已声明稳定的文档控制面。

- `PATCH`：向后兼容 bugfix、性能修复、文档修正、内部重构，且不要求实例包改变使用方式。
- `MINOR`：向后兼容新增能力、新命令、新 MCP tool、新可选字段、新配置项，或官方实例可选择使用的新 runtime 能力。
- `MAJOR`：删除或改变稳定入口、改变稳定字段语义、改变默认 gate/decision 行为导致既有项目需要迁移、或打破已声明兼容范围。

### Official instance wheel

- `PATCH`：prompts、templates、examples、references 或 validator 诊断文本的向后兼容修复。
- `MINOR`：新增模板、prompt、validator、document type、on_demand asset，或开始使用 runtime 的新可选能力。
- `MAJOR`：改变官方实例采用方式、删除已发布入口、改变 project-local scaffold 的不兼容结构，或要求 runtime major 升级。

### VS Code extension

VSIX 按自身 `package.json` 版本线独立 bump：

- `PATCH`：UI bugfix、webview 修复、无新命令的兼容行为修正。
- `MINOR`：新增用户可见功能、命令、配置项、面板或可选集成。
- `MAJOR`：不兼容配置迁移、命令移除、最低 VS Code engine 大幅改变，或现有用户工作流需要迁移。

若 VSIX 的用户可见能力来自外部前端组件，VSIX bump 依据宿主用户可见行为判断；外部组件版本只作为依赖记录，不强制与 VSIX 版本同线。

## 打包前强制检查

打包前必须满足：

1. `pyproject.toml` version 是当前可打包的 SemVer core：`MAJOR.MINOR.PATCH`。
2. `doc-loop-vibe-coding/pyproject.toml` version 与 runtime version 一致。
3. `doc-loop-vibe-coding/pack-manifest.json` version 与 runtime version 一致。
4. release 文档中的 wheel / zip 版本引用不含旧版本。
5. `scripts/release.py --version` 的覆盖值必须同样是 `MAJOR.MINOR.PATCH`，且不得带 `v`。
6. `scripts/release.py --version` 不是 bump 工具；覆盖值必须等于 `pyproject.toml` 中的 canonical runtime version，否则 release zip 批次号会与 wheel 元数据漂移，必须拒绝打包。
7. 若生成 VSIX，`vscode-extension/package.json` version 必须是合法 SemVer；它可以不同于 runtime version，但 release note 必须显式记录。
8. 若 VSIX 使用外部前端组件，本地 `file:` 依赖不得指向当前仓库外部工作区；发布态必须指向 `vscode-extension/vendor/*.tgz` 或使用 registry 版本。
9. release zip 若携带 VSIX，应同时携带外部前端组件 tarball或在 release note 中记录 registry 版本与 lockfile integrity，确保可复现构建线索可恢复。

## 脚本约束

当前代码层约束：

1. `scripts/release_versioning.py` 提供 SemVer 校验 helper。
2. `scripts/build.py` 读取 runtime / instance version 时拒绝非 `MAJOR.MINOR.PATCH`。
3. `scripts/release.py --version` 拒绝非 `MAJOR.MINOR.PATCH`，也拒绝与 runtime package metadata 不一致的版本。
4. `release/verify_version_consistency.py` 校验 runtime、instance、pack manifest 与 release 文档的一致性时，也拒绝非 `MAJOR.MINOR.PATCH`。
5. `release/verify_version_consistency.py` 独立校验 VSIX 文档引用与 `vscode-extension/package.json` 版本一致，并拒绝 graph engine 等外部组件继续使用开发态外部 `file:` 路径。

## 未来扩展

若后续需要 preview / rc 发布，应先新增独立 planning gate，明确：

1. Python wheel 对预发布版本的 metadata 与文件名兼容规则。
2. VS Code Marketplace / VSIX 对预发布版本的兼容规则。
3. release zip 文件名中 `-rc.1` / `+build` 的转义与排序规则。
4. 版本一致性 checker 对 pre-release、build metadata 的解析和 stale reference 策略。
5. 用户安装文档如何区分稳定版、候选版和内部构建版。
