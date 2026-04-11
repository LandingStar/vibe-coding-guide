# Planning Gate — Post-v1.0 Installation Flow Documentation

- Status: **COMPLETED**
- Date: 2026-04-11

## 当前问题

当前仓库已经具备 runtime 包与官方实例包的最小安装骨架，但用户侧仍缺一份可以直接照着执行的安装流程说明：

1. 目前已经能通过本地路径或 wheel 安装 `doc-based-coding-runtime` 与 `doc-loop-vibe-coding`。
2. 但仓库里的权威文档尚未给出统一、可执行的安装与验证步骤。
3. 当前 workspace 的 `.vscode/mcp.json` 仍是开发态配置，用户若想按安装态接入 MCP，需要一个明确的配置示例。

此外，用户还要求先检查当前 MCP 运行情况，并据此决定安装文档是否需要单独强调“开发态 MCP”和“安装态 MCP”的区别。

## 权威输入

- `design_docs/Project Master Checklist.md`
- `docs/project-adoption.md`
- `docs/official-instance-doc-loop.md`
- `design_docs/tooling/Dual-Package Distribution Standard.md`
- `README.md`
- `docs/README.md`
- `.vscode/mcp.json`
- `pyproject.toml`
- `doc-loop-vibe-coding/pyproject.toml`

## 候选阶段名称

- `Post-v1.0 Installation Flow Documentation`

## 本轮只做什么

- 核对当前 MCP 的可用性与当前 workspace 配置形态。
- 新增一份权威安装指南，覆盖本地路径安装、wheel 安装、基础验证与 MCP 接入示例。
- 把根 README、文档索引以及 adoption 文档接到该安装指南上。

## 本轮明确不做什么

- 不进入新的打包实现切片
- 不实现 registry / marketplace / 发布自动化
- 不修复 MCP `get_pack_info` 的缓存刷新一致性
- 不在本轮生成 handoff

## 验收与验证门

- 针对性测试：无新增代码测试要求，以文档命令和已存在 smoke 结果为依据
- 更广回归：MCP 约束检查通过
- 手测入口：确认 MCP 工具可调用；确认文档中的安装与验证命令与当前包元数据一致
- 文档同步：README、docs/README、project-adoption 与新安装指南对齐

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `.codex/checkpoints/latest.md`
- `README.md`
- `docs/README.md`
- `docs/project-adoption.md`
- 新增安装指南文档

## 子 agent 切分草案

- 当前不需要子 agent；该切片以权威文档写作和状态同步为主。

## 收口判断

- 当 MCP 当前运行情况已核对、安装流程有权威文档落点、并且入口文档都已接到该指南时，本切片即可收口。
- 做到这里就应停，不顺手扩成新的打包或缓存修复切片。

## 执行结果

- 已确认当前 MCP 工具可调用，`check_constraints` 与 `get_pack_info` 均返回有效结果，且当前 workspace 无约束阻塞。
- 已新增 `docs/installation-guide.md`，覆盖本地路径安装、wheel 安装、最小验证与安装态 MCP 接入示例。
- 已将 `README.md`、`docs/README.md` 与 `docs/project-adoption.md` 接到该安装指南。
- 已在文档中明确区分当前 workspace 的开发态 MCP 配置与安装态项目推荐配置。