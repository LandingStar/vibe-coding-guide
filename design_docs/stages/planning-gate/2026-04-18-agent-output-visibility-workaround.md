# Planning Gate: 子 Agent 输出可见性临时方案

> 日期: 2026-04-18
> Gate: inform
> 来源: 用户反馈 — VS Code Copilot Chat 中 AI 文本输出完全不可见

## 问题

在 VS Code Copilot Chat 中，用户只能看到 `askQuestions` 工具弹出的选项和描述。AI 在 tool 调用之间输出的文本（分析、表格、链接、Markdown）完全不可见。

这导致：
- 方向对比表、审计报告等关键分析无法被用户看到
- 用户做决策时缺少必要上下文
- AI 输出的大量工作成果被浪费

## 临时方案

1. **Agent Output File**: 创建 `.codex/agent-output/latest.md`，AI 每次输出关键分析时先写入此文件
2. **askQuestions 引用**：在 askQuestions 的选项描述中包含文件路径，提示用户打开查看
3. **写入工具函数**：在 `src/workflow/` 中创建 `agent_output.py` helper，封装写入逻辑

## 保留约定

- 所有代码和逻辑保留，不做临时 hack
- 插件化时将 `write_agent_output()` 替换为 UI 面板输出
- helper 函数设计为可扩展：支持 file / UI panel / chat stream 多种输出目标

## 验证门

- [x] `src/workflow/agent_output.py` 已创建
- [x] `.codex/agent-output/` 目录可用
- [x] 测试覆盖（10 passed）
- [x] Checklist 已更新
