# Commit Message（中文版）

```
feat: v1.0.0 稳定版发布 + 发布后验证

Phase 22-35 完成，v1.0.0 稳定版发布。发布后方向候选 A-J 全部完成。
发布封装通过完整验证链（构建→安装→空项目端到端采纳验证）。

## 核心里程碑

- v0.1 自用发布：Pipeline + MCP Server + Instructions Generator
- PackContext 下游贯通 + 深度自用验证
- MCP Prompts/Resources + Extension Bridging + on_demand 懒加载
- 自用反馈修复（第一轮与第二轮）
- 稳定版边界确认 + 错误恢复 + 结构化错误格式统一
- v1.0.0 稳定版发布确认

## 发布后方向候选

- A：双发行包实现（runtime + instance wheel）
- B：validator/check 契约收口
- C：兼容元数据与版本声明
- D：MCP pack info 刷新一致性
- E：严格 doc-loop 运行时强制
- F：handoff 主动调用
- H：外部 Skill 交互接口
- I：安全停点回写包
- J：对话推进契约稳定性

## 发布封装验证

- 双包构建：runtime 83KB wheel + instance 48KB wheel
- 干净虚拟环境安装：5 个 CLI 入口全部可用
- 空项目采纳验证：bootstrap → validate → MCP 启动
- 可分发安装包：release/doc-based-coding-v1.0.0.zip（含面向 AI 的安装指南）

## 新增关键文件

- pyproject.toml（runtime + instance）
- src/mcp/（MCP 服务端 + 治理工具）
- src/workflow/（pipeline、instructions、外部 skill、安全停点回写）
- doc-loop-vibe-coding/pyproject.toml + MANIFEST.in
- release/（README、INSTALL_GUIDE、zip）
- .codex/handoff-system/ + .codex/handoffs/ + .github/skills/
- docs/first-stable-release-boundary.md
- docs/external-skill-interaction.md
- docs/installation-guide.md
- CHANGELOG.md
```
