# Planning Gate — Post-v1.0 Dual-Package Install Standard

- Status: **COMPLETED**
- Date: 2026-04-11

## 问题陈述

当前仓库已经完成 v1.0 稳定版确认，但“可在其他项目中安装使用”仍停留在源码仓库形态：

1. 运行时当前通过 `python -m src` 暴露 CLI，而不是正式分发包入口。
2. VS Code MCP 配置当前直接指向本仓库本地虚拟环境与 `src.mcp.server`，属于 workspace-local 开发形态，不是对外安装标准。
3. 官方实例 `doc-loop-vibe-coding/` 已经具备 manifest、bootstrap、validator、模板等可分发资产，但尚未定义它应如何与平台 runtime 一起发布。

用户已明确：下一步先形成标准，不直接做实现；并将发布形态收敛为“双发行包”，而不是单一发行包。

## 审核后边界

用户已确认：

- 当前先只定义安装/发布标准，不进入 pyproject、构建脚本、发布流水线实现。
- 发布形态采用双发行包：平台 runtime 与 doc-loop 官方实例资产分开发布。
- 当前阶段先由主 agent 起草标准，不把权威标准文档维护委派给子 agent。

## 权威输入

- `design_docs/Project Master Checklist.md`
- `docs/project-adoption.md`
- `docs/official-instance-doc-loop.md`
- `docs/first-stable-release-boundary.md`
- `doc-loop-vibe-coding/pack-manifest.json`
- `src/__main__.py`
- `.vscode/mcp.json`

## 本轮只做什么

### Slice A: 双发行包边界标准

- 明确平台 runtime 包负责什么：CLI、MCP server、Pipeline/runtime API、安装后入口面。
- 明确官方实例包负责什么：pack manifest、bootstrap scaffold、prompts、templates、validators、examples。
- 明确两个发行包之间的依赖方向、版本兼容关系与最小耦合边界。

### Slice B: 安装与接入标准

- 定义目标项目应如何安装 runtime 包与官方实例包。
- 定义 bootstrap、validate-instance、validate-repo、generate-instructions 等入口应由哪个发行包暴露。
- 定义 MCP 配置标准必须引用“已安装入口”而非当前仓库源码路径。

### Slice C: 验证门标准

- 定义 clean environment 安装验证。
- 定义 bootstrap 到目标仓库后的最小校验链。
- 定义 CLI/MCP/pack assets 的 smoke test 范围。

## 本轮明确不做什么

- 不直接重命名 `src` import root
- 不直接编写 `pyproject.toml`、`setup.cfg` 或发布脚本
- 不直接实现 wheel/sdist 构建
- 不直接做 PyPI / 私有源发布自动化
- 不直接实现 registry、远程拉取实例资产或多实例冲突求解

## 验收与验证门

- 双发行包的职责边界清晰且互不重叠
- 安装路径、调用入口、MCP 接入方式都有明确标准
- 版本兼容关系与最小验证矩阵被文档化
- 子 agent 使用边界被明确：当前标准起草阶段不用；仅在后续窄 scope 调研或实现合同下考虑引入

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `.codex/checkpoints/latest.md`
- 后续若该 planning-gate 被采纳，再同步正式 tooling standard / adoption 文档

## 子 agent 切分草案

- 当前不使用子 agent 起草该标准。
- 若后续进入实现前调研，可将“PEP 517 backend 对比”“包数据打包策略对比”“安装后 MCP 入口形态对比”拆成只读子合同交给子 agent。
- 共享状态文档、权威标准文档与最终边界结论继续由主 agent 维护。

## 收口判断

- 该切片是一个纯标准定义 planning-gate，不进入实现。
- 做到双发行包边界、安装入口、验证门、子 agent 使用策略都清晰，就应收口。
- 完成后再决定下一步进入“正式标准文档写作”还是“最小实现切片”。