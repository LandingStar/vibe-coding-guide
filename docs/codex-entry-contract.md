# Codex Entry Contract

## 文档定位

本文件定义 Codex 在当前平台中的**独立入口 contract**。

它回答的是：

- 在 Codex 中使用本平台时，最短入口闭环是什么
- Codex 与 VS Code/Copilot extension 的职责边界是什么
- 为什么 Codex 不等于 extension 第二 provider
- 未来若有 Codex helper surface，哪些内容可以薄层化，哪些仍必须留在 authority docs

它不定义 helper entry、第二 provider 或 Codex 专用 runtime。

## 最短入口闭环

当前推荐把 Codex 的最短入口理解为四步：

1. 生成或刷新 Codex 指令入口
2. 注册 MCP server
3. 运行最小验证
4. 按需要跳到更深 authority docs

### 1. 指令入口

Codex 的项目级长期指令入口是：

- `AGENTS.md`

生成方式：

- `doc-based-coding generate-instructions --target codex --output AGENTS.md`

若输出文件名已是 `AGENTS.md`，CLI 也会自动推断 Codex 目标。

### 2. MCP 注册入口

Codex 当前优先走项目级 MCP 注册：

- `.codex/config.toml`
- 或 `codex mcp add`

这两者都属于宿主注册适配面，而不是平台核心语义。

### 3. 最小验证

完成 instructions 与 MCP 注册后，最小验证建议是：

1. 确认 `AGENTS.md` 已生成或刷新
2. 确认 Codex 能看到 `doc-based-coding-mcp`
3. 在目标仓库里执行最小命令验证，例如：
   - `doc-based-coding info`
   - `doc-based-coding validate`

### 4. 需要更深说明时跳哪里

- 安装与 MCP 接入细节：`docs/installation-guide.md`
- 宿主分层与边界：`docs/host-interaction-model.md`
- 第一次进入仓库的总入口：`docs/starter-surface.md`

## Codex 与 VS Code/Copilot extension 的边界

Codex 当前应被理解为 **Interaction Adapter Layer** 的一个子案例。

VS Code extension 当前应被理解为 **Host UX Layer** 的一个宿主实现。

这意味着：

- Codex 默认走 `AGENTS.md` + MCP + CLI/validation 闭环
- VS Code/Copilot extension 默认走宿主 UI、TreeView、WebView、notification、chat participant 等交互面
- 两者都消费同一条平台 authority contract，但不应互相替代

## 为什么 Codex 不等于 extension 第二 provider

当前不应把 Codex 简化成“给 extension 再加一个 provider”。原因是：

1. Codex 的最短入口不依赖 VS Code Host UX
2. `2026-04-22-vscode-extension-llm-provider-abstraction` 只解决 extension 命令层 provider 解耦
3. 若先把 Codex 当成 extension 第二 provider，会把宿主 UI 语义误当成 Codex 的产品 contract

因此，是否继续比较 extension 第二 provider，应放在 Codex 独立入口 contract 清晰之后再判断。

## 未来 helper surface 的边界

若后续出现 Codex helper surface，允许被薄层化的内容包括：

- instructions 生成提示
- MCP 注册提示
- 最小验证步骤
- authority docs 的跳转路由

仍必须保留在 authority docs 的内容包括：

- 平台核心语义
- planning-gate / handoff / safe-stop / authority priority
- 宿主分层模型
- 工作流长期协议

## 当前边界

本文件当前固定的是：

- Codex 最短入口闭环
- Codex 与 VS Code/Copilot extension 的职责边界
- 对 extension 第二 provider 问题的基本判断
- helper surface 的非目标边界

本文件当前不固定：

- Codex helper entry 设计
- Codex companion packaging
- 第二 provider 实现
- 第二宿主 UI 适配
