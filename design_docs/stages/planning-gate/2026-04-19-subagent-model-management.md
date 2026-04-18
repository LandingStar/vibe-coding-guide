# Planning Gate: 子 Agent Model 管理

- **状态**: CLOSED
- **scope_key**: subagent-model-management
- **来源**: Checklist 待办 "子 agent model 管理"

## 目标

让 Extension 中 `CopilotLLMProvider`（用于 classifyIntent、generatePackDescription、generatePackRules、interceptor）的模型 family 可配置、可运行时切换。

Chat Participant 的 `request.model` 由 VS Code Chat 框架管理（用户在 Chat 下拉菜单选择），不在本切片范围。

## 切片内容

1. **package.json** — 新增 `docBasedCoding.llm.family` 配置项（string，default `"gpt-4o"`）
2. **package.json** — 新增命令 `docBasedCoding.selectModel`
3. **copilot.ts** — `initialize()` 从 workspace config 读取 family（优先级：config > 参数 > 默认）
4. **extension.ts** — 注册 `selectModel` 命令（Quick Pick 列出可用模型 → 写入 config → 重新 initialize）
5. **extension.ts** — 注册 `onDidChangeConfiguration` 监听，family 变更时自动 re-init

## 验证门

- [x] esbuild 构建零错误
- [x] 配置默认值 `gpt-4o` → 行为与之前一致
- [x] `selectModel` 命令注册可见

## 不做

- 不修改 Chat Participant 的 model 选择（已由框架管理）
- 不引入第三方 LLM provider（仅 vscode.lm）
