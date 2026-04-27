# Planning Gate: VS Code Extension LLM Provider Abstraction

- **状态**: CLOSED
- **scope_key**: vscode-extension-llm-provider-abstraction
- **来源**: 用户要求“抽象掉 Copilot 绑定，但不能影响原有功能；若无法保证，则为 Codex 走独立系统”

## 目标

在不改变当前 Copilot 功能语义的前提下，把 VS Code Extension 内部对 `CopilotLLMProvider` 的直接依赖收口到抽象 provider 接口上，为后续 Codex 专用入口预留边界。

## 设计结论

1. **可安全抽象的层**
   - `classifyIntent`
   - `generatePackDescription`
   - `generatePackRules`
   - Governance BLOCK explanation
   - Config Panel 的模型 family 列表读取

2. **本切片不抽象的层**
   - Chat Participant 的 `request.model`
   - VS Code 原生 Chat participant 注册语义
   - Python runtime / MCP contract

3. **原因**
   - 上述 5 个调用面已经通过 `LLMProvider` 接口天然具备抽象缝隙，只是调用层仍直接依赖 `CopilotLLMProvider`
   - Chat Participant 由 VS Code Chat 框架直接管理模型选择，强行并入共享 provider 层会扩大回归面，不满足“原有功能不受影响”的前提

## 切片内容

1. 扩展 `vscode-extension/src/llm/types.ts`，定义面向调用层的 managed provider 契约
2. 调整 `vscode-extension/src/llm/copilot.ts`，让 Copilot 继续作为默认实现并补齐 managed provider 能力
3. 新增 provider factory / 默认 provider 入口，避免调用层直接 `new CopilotLLMProvider()`
4. 将 `extension.ts`、`interceptor.ts`、`packGenerator.ts`、`configPanel.ts` 改为依赖抽象接口
5. 同步 extension 文档与命令描述，明确“当前默认 provider 是 Copilot，抽象已完成，但 Chat participant 仍保留 VS Code Chat 原生路径”

## 验证门

- [x] esbuild 构建零错误
- [x] 现有命令 ID 不变
- [x] `docBasedCoding.llm.family` 默认行为不变
- [x] 无 Copilot 时仍保持现有降级行为

## 不做

- 不把 Chat Participant 重写成独立于 VS Code Chat 的自定义系统
- 不在本切片实现新的 Codex provider
- 不修改 Python CLI / MCP runtime

## 后续分叉条件

- 若后续需要让 Codex 获得与 Extension 等价的交互面，应走**独立 Codex 系统/入口**，而不是复用 VS Code Chat participant 语义
- 当前切片仅负责把可安全复用的 provider 调用面先抽象出来

## 结果

- `CopilotLLMProvider` 继续保留为默认实现，但调用层已改为依赖抽象 provider 契约
- `extension.ts` 不再直接实例化具体 Copilot 类
- Chat Participant 保持 VS Code Chat 原生路径，不扩散回归面

## 依据

- `design_docs/stages/planning-gate/copilot-integration-runtime-simulation.md`
- `design_docs/stages/planning-gate/2026-04-19-subagent-model-management.md`
- `vscode-extension/src/llm/types.ts`
- `vscode-extension/src/extension.ts`
