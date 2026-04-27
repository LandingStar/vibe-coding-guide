# Starter Surface

## 文档定位

本文件是当前仓库的**最短入口路由**。

它回答 4 个最小问题：

1. 第一次进入仓库先读什么
2. 你的当前目标对应哪条入口
3. 哪些深文档现在先不要读
4. 什么时候跳到更深的 authority docs

它只负责路由，不定义第二份平台语义真相源。

## 如果你是第一次进入仓库

先按这个顺序：

1. 读 `docs/platform-positioning.md`，确认这个仓库是平台，不是单一 skill
2. 读 `docs/official-instance-doc-loop.md`，确认官方实例是什么
3. 再根据你的当前目标，跳到下面对应入口

如果你只想知道文档全景，再读 `docs/README.md`。

## 按目标选择入口

### 1. 我想安装/运行它

先读：

- `docs/installation-guide.md`

然后：

- 若要把它接入真实仓库，再读 `docs/project-adoption.md`

### 2. 我想理解平台本体

先读：

- `docs/platform-positioning.md`
- `docs/core-model.md`
- `docs/plugin-model.md`

### 3. 我想理解官方实例如何落在平台上

先读：

- `docs/official-instance-doc-loop.md`
- `docs/project-adoption.md`

### 4. 我正在当前仓库里继续开发

先读：

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- 当前 active planning-gate 或 phase 文档

### 5. 我只想知道当前宿主/客户端如何接入

先读：

- `docs/host-interaction-model.md`
- `docs/installation-guide.md`

## 不同宿主的最小差异面

### Codex

- 指令入口：`AGENTS.md`
- MCP 注册：优先 `.codex/config.toml` 或 `codex mcp add`
- 更深说明：`docs/codex-entry-contract.md` 与 `docs/installation-guide.md`

### VS Code / Copilot

- 指令入口：`.github/copilot-instructions.md` 或生成后的 Copilot instructions
- MCP 注册：workspace `mcp.json`
- 若需要宿主分层说明：`docs/host-interaction-model.md`

### Claude / generic assistant

- 指令入口：优先走 `generic` 目标生成的 instructions 片段
- MCP 注册：按宿主支持的 stdio MCP 路径接入
- 当前没有单独的 Claude helper surface；若只想理解边界，先读 `docs/host-interaction-model.md`

### 其他 MCP Host

- 默认先按 `docs/installation-guide.md` 的 stdio MCP 路径接入
- 若宿主有 UI 扩展面，再参考 `docs/host-interaction-model.md` 判断它属于哪一层

## 现在先不要读什么

如果你只是第一次进入仓库，先不要从这些地方开始：

- `design_docs/` 全量历史方向分析
- `review/` 全量外部研究
- `.codex/handoffs/history/`
- `release/` 下的发布材料

这些内容要么是内部设计推导，要么是研究资产，要么是 safe-stop 恢复面，不适合作为首跳入口。

## 什么时候跳到更深文档

- 当你需要完整文档地图时，跳到 `docs/README.md`
- 当你需要安装态细节时，跳到 `docs/installation-guide.md`
- 当你需要宿主差异与平台边界时，跳到 `docs/host-interaction-model.md`
- 当你需要 Codex 的独立入口闭环时，跳到 `docs/codex-entry-contract.md`
- 当你需要当前仓库的开发状态时，跳到 Checklist / Phase Map
- 当你需要历史研究依据时，再去 `review/` 与 `design_docs/`

## 当前边界

本文件当前固定的是：

- 最短首跳路由
- 不同目标的入口分流
- 宿主差异的最小入口说明
- 首次进入时应暂时忽略的文档面

本文件当前不固定：

- helper entry 设计
- companion packaging
- 第二宿主实现
- 运行时或 UI 交互细节
