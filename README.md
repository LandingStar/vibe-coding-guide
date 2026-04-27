# Doc-Based Coding

本仓库当前的目标已经升维：它不再只是沉淀一套“doc-driven vibe coding skill”，而是尝试定义一个更通用的**协议/治理驱动工作流平台**，用于承载规则、限制、标准、gate、文档对象、提示词、校验器与脚本扩展。

在这个新定位下：

- 平台本体负责核心模型、优先级、意图分类、权限边界与插件扩展点
- `doc-driven vibe coding` 不再是项目本体，而是这个平台上的一个**官方实例**
- 当前 `doc-loop-vibe-coding/` 目录应视为该官方实例的**原型资产**，暂时封存，等待按新平台文档回头复审

## 先读哪里

如果你是第一次进入当前仓库，先读：

- `docs/starter-surface.md`

当前权威文档位于 `docs/`：

- `docs/platform-positioning.md`
- `docs/core-model.md`
- `docs/plugin-model.md`
- `docs/pack-manifest.md`
- `docs/governance-flow.md`
- `docs/review-state-machine.md`
- `docs/subagent-management.md`
- `docs/subagent-schemas.md`
- `docs/official-instance-doc-loop.md`
- `docs/host-interaction-model.md`
- `docs/project-adoption.md`
- `docs/current-prototype-status.md`

建议阅读顺序：

1. `starter-surface.md`
2. `platform-positioning.md`
3. `official-instance-doc-loop.md`
4. `installation-guide.md`
5. `project-adoption.md`
6. `host-interaction-model.md`

如果你想看完整文档地图，再去 `docs/README.md`。

## 安装与接入

当前仓库已经具备双发行包的最小安装骨架。

如果你当前主要在 **Codex** 中使用本项目，默认应这样理解接入面：

- 仓库级长期指令入口是 `AGENTS.md`
- 可用 `doc-based-coding generate-instructions --target codex --output AGENTS.md` 生成或刷新治理指令块
- MCP 推荐通过项目级 `.codex/config.toml` 或 `codex mcp add ...` 接入 `doc-based-coding-mcp`

如果你仍在 **VS Code / Copilot** 中使用本项目，兼容入口保持可用：

- 可用 `doc-based-coding generate-instructions --target copilot --output .github/copilot-instructions.md`
- MCP 可继续通过 workspace 级 `.vscode/mcp.json` 接入

如果你想把它安装到其他项目中，优先看：

- [docs/installation-guide.md](docs/installation-guide.md)

如果你想进一步把某个真实仓库接入这套 workflow，再看：

- [docs/project-adoption.md](docs/project-adoption.md)

研究与设计推导另外分层存放：

- `review/`
  - 外部产品研究与对比材料
- `design_docs/`
  - 从研究推导到本平台的内部设计笔记

## 现有资产如何理解

`example/` 保留的是一套手工跑出来的参考文档语料，主要用于反向提炼模式，而不是当前平台协议本身。

`doc-loop-vibe-coding/` 保留的是一版已经做出的原型实现，当前用途是：

- 提供一个可讨论的官方实例雏形
- 帮助识别平台需要哪些扩展点
- 作为后续复审和重构的输入

它现在已经包含一套更具体的实例化资产：

- `pack-manifest.json`
- `examples/` 下的子 agent schema 样例
- `assets/bootstrap/.codex/contracts/` 下可复制到项目中的合同模板
- `assets/bootstrap/.codex/packs/project-local.pack.json` 作为项目级 overlay pack 模板
- `scripts/validate_instance_pack.py` 与 `scripts/validate_doc_loop.py` 作为实例级和项目级自检脚本

它**暂时不是**本仓库的权威定义来源。
