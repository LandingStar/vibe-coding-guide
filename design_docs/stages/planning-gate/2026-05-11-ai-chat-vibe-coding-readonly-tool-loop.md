# Planning Gate — AI Chat Vibe Coding Read-Only Tool Loop

> 日期: 2026-05-11
> 状态: PROPOSED
> 来源: `tmp/feedback.md`
> 关联实现面: `vscode-extension/src/views/aiChatView.ts`, `vscode-extension/src/chat/participant.ts`, `vscode-extension/src/mcp/client.ts`

## Why this exists

当前自定义 AI Chat 已具备：

1. provider 切换、模型切换、base URL 与 API key 配置入口
2. 基本对话历史拼接
3. 单次 prompt -> 单次回答的流式输出

但它还不具备 `vibe coding` 的关键闭环：

1. 看工作区
2. 查代码
3. 读诊断
4. 基于工具结果继续推理
5. 在安全边界内逐步升级到改代码与跑命令

`tmp/feedback.md` 已经把目标能力列全，但直接同时实现读、写、搜索、终端、诊断、Git、测试会把协议、权限和验证面一次性扩爆。因此先起一个窄 gate，把第一刀收敛成 read-only tool loop。

## Scope

本 gate 只处理：

1. 自定义 AI Chat 的最小工具循环协议
2. 只读工具的第一批接入
3. 工具调用结果在聊天视图中的最小可见性
4. 与该切片直接相关的 focused validation

本 gate 不处理：

1. 文件写入或 patch 应用
2. 终端命令执行
3. Git、测试、任务自动执行
4. 自动多步自治代理
5. 完整 Copilot 风格的消息卡片、审批时间线或富工具面板

## Working hypothesis

当前假设是：

1. 自定义 AI Chat 当前真正缺的不是“更多 prompt”，而是“中间工具执行环”
2. 第一刀先做只读工具，已经足够把聊天从空泛回答推进到 grounded project assistance
3. 写文件和跑命令必须放到下一刀，再接治理与审批，否则会把安全边界做坏
4. 仓库里现有的 `chat participant + MCP client` 已经证明扩展宿主可以承载受控工具调用，因此不应从零重造第二套宿主桥

## Required inputs

当前第一刀优先复用：

1. `vscode-extension/src/views/aiChatView.ts` 的现有聊天视图与消息桥
2. `vscode-extension/src/chat/participant.ts` 的宿主侧对话与 MCP 调用经验
3. VS Code extension host 已有的工作区 API

当前不允许：

1. 先把 write/terminal 权限混进 read-only 协议
2. 为了工具循环直接绕过现有治理边界
3. 在没有 focused validation 的情况下宣称“已支持 vibe coding”

## Success bar

本 gate 的最小成功标准：

1. AI Chat 可以在一次会话中调用至少三类只读工具并继续回答
2. 第一批工具至少覆盖：工作区列举、文件读取、文本搜索、诊断读取中的三项
3. 用户在聊天中能看见工具调用的最小痕迹，而不是只看到最终结论
4. 当前 provider abstraction 不被破坏，Copilot 与 OpenAI-compatible 路线都还能工作
5. focused validation 至少包含扩展构建通过，以及一条面向工具循环的可执行或可断言验证

## First slice suggestion

当前推荐第一刀固定为：

1. 给自定义 AI Chat 增加一个最小 action protocol，允许模型请求只读工具
2. 首批只接入 `list files`、`read file`、`search text`、`get diagnostics`
3. 先把工具调用过程显示为简洁的聊天事件块或系统消息
4. 只在单轮内支持有限次工具调用，避免直接进入开放式 agent loop

推荐顺序：

1. 先打通协议与一个工具
2. 再扩到其余三个只读工具
3. 验证稳定后，再起下一份 gate 讨论 write/terminal slice

## Focused validation

当前计划中的 focused validation：

1. `npm run build`
2. 关键入口文件 diagnostics clean
3. 最小 smoke path：用户在 AI Chat 提问“列出工作区根目录文件”或“读取某个文件”，聊天能显示工具调用痕迹并返回 grounded 结果

## Stop condition

满足以下条件即可在本 gate 内安全停点：

1. 只读工具循环最小闭环已成立
2. 至少三类只读工具可用
3. focused validation 通过
4. write/terminal 能力仍明确留在后续 gate，不在本刀偷渡