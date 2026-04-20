# Commit Message（中文版）

```
feat: v0.9.4 架构合规性收口 + Worker schema 对齐

模块依赖方向强制 + 跨层违规全部消除 + HTTPWorker 报告格式对齐。
B-REF 系列全部完成。Multica 架构借鉴四项全部落地。
Release: doc-based-coding-v0.9.4.zip (192.4 KB)

## 新增

- Module Dependency Direction Standard（6 层架构 + 方向规则文档）
- scripts/lint_imports.py AST 跨包 import 方向自动化验证
- src/pack/pack_discovery.py：pack 发现逻辑独立模块（从 workflow 下沉）
- PLATFORM_INTENTS / IMPACT_TABLE / KEYWORD_MAP 提升到 src/interfaces.py
- src/runtime/bridge.py：RuntimeBridge 三入口统一初始化 + WorkerHealth
- src/pack/pack_integrity.py：pack-lock.json + compute_pack_hash()
- src/pack/user_config.py：user-global 配置层
- src/workflow/reply_progression.py + check_reply_progression MCP 工具
- PackManifest consumes 字段 + check_consumes() 能力依赖校验
- 条件化 always_on 加载（scope_path 过滤）
- VS Code Extension Config UI（configExplorer / configPanel）
- MCP pack_lock / pack_unlock / pack_verify 工具

## 修复

- 3/3 跨层依赖违规全部消除（pack→workflow / pack→pdp types / pack→pdp constants）
- HTTPWorker._error_report() schema 对齐（status: blocked + escalation: review_by_supervisor + unresolved_items）
- pack-lock hash mismatch 回归修复（consumes 字段新增后重新锁定）

## 改进

- B-REF-1~7 全部完成（渐进式加载 / description 质量 / pack 组织 / permission policy / 工作流中断 / 上下文隔离 / tool surface 审计）
- VS Code Extension 全功能（P0-P7 + 安装向导 + git push guard + Chat Participant）
- 全局记忆/文档/规则支持（user-global pack + config.json）
- Multica 架构借鉴落地（hash 锁定 / 条件化加载 / RuntimeBridge / consumes）

## 验证

- pytest: 1257 passed, 2 skipped
- lint_imports.py: 零违规、零已知例外
- pack_verify: 2/2 packs ok
- VS Code Extension esbuild: 零错误
- MCP 全工具链 dogfood 通过

## 文件统计

- 36 files changed, +1159 -555
```
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
