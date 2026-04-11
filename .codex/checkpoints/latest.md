# Checkpoint — 2026-04-12T06:16:07+08:00
## Current Phase
Phase 35: v1.0 Stable Release Confirmation — 完成
## Release
v1.0.0 — First stable release
## Active Planning Gate
—
## Current Todo
- [x] 完成 Phase 35 handoff intake
- [x] 确认 doc-based-cod MCP 服务在当前 workspace 可用
- [x] 确认双发行包为 post-v1.0 安装发布方向
- [x] 起草职责边界与依赖方向标准初稿
- [x] 固定安装入口与 MCP 接入标准初稿
- [x] 固定版本兼容与最小验证门标准初稿
- [x] 起草 post-v1.0 候选方向文档
- [x] 确认 post-v1.0 首个实现方向为双发行包实现切片
- [x] 收敛 build backend / package data / 入口命名方案
- [x] 实现 runtime 包与官方实例包的最小安装骨架
- [x] 补齐最小 smoke 验证
- [x] 选择双发行包实现后的下一切片
- [x] 文档化 validators / checks / scripts 的消费边界
- [x] 修正官方实例 manifest 的字段归属
- [x] 清理官方实例 `missing-validate` 诊断并更新测试
- [x] 选择下一切片（兼容元数据声明或 MCP pack info 刷新一致性）
- [x] 定型 pack/实例语义层的 runtime 兼容字段
- [x] 对齐官方实例 pyproject 与 pack manifest 的兼容范围
- [x] 增加兼容元数据的 targeted tests
- [x] 将“未经用户显式许可不得主动终止对话”写入正式规则载体
- [x] 核对当前 MCP 运行情况并记录开发态配置现状
- [x] 新增安装流程权威文档并补齐入口链接
- [x] 修复 `—` active planning gate 哨兵值误判
- [x] 同步 project-local pack 的 C1 约束文案
- [x] 将 MCP 叙述改为面向通用 MCP 客户端
- [x] 评估是否进入 strict doc-loop runtime enforcement 切片
- [x] 起草 strict doc-loop runtime enforcement planning-gate
- [x] 同步 runtime machine-checked / instruction-layer 约束边界
- [x] 更新 MCP 暴露面的 enforcement 公开表述
- [x] 增加 strict doc-loop runtime enforcement 的 targeted tests
- [x] 决定进入 MCP pack info 刷新一致性切片
- [x] 起草 MCP pack info refresh consistency planning-gate
- [x] 修复长生命周期 GovernanceTools 的 pack state 刷新策略
- [x] 增加 pack state refresh consistency 的 targeted tests
- [x] 决定在生成 handoff 前先收口 handoff 主动调用语义
- [x] 起草 handoff model-initiated invocation planning-gate
- [x] 对齐 handoff protocol / workflow / skill invocation contract
- [x] 同步 bootstrap 与 example 副本
- [x] 保留 slash 入口名示例并修复 portable handoff kit 安装测试回归
- [x] 在当前安全停点生成 handoff
- [x] 起草并激活 `2026-04-12-conversation-progression-contract-stability.md`
- [x] 将 C1/C3 收口为结构化 conversation progression contract
- [x] 同步本地与 bootstrap prompt surfaces 的推进式提问 / `askQuestions` 步骤
- [x] 为 instructions generator 增加 `Conversation Progression Contract` section
- [x] 让 MCP `get_next_action()` / `writeback_notify()` 在 `ask_user=true` 时返回显式 interaction contract
- [x] 跑完 targeted tests 并完成当前切片 write-back
- [x] 实现 `Safe-Stop Writeback Bundle` 的 bundle contract 与必做/条件写回边界
- [x] 补齐 safe-stop bundle 的 targeted validation 与状态面一致性回归
- [x] 完成 H（通用外部 skill 交互接口能力）方向分析，并明确 `authority -> shipped copies` 为 companion mechanism
- [x] 基于 `design_docs/phase-35-external-skill-interface-direction-analysis.md` 起草 H planning-gate
- [x] 固定 external skill interaction 最小 contract（invocation / continuation / authority / integration）
- [x] 让当前 handoff family 对齐为首个 reference implementation
- [x] 为本轮触达的 shipped copies 落地 companion drift-check / distribution rule
- [x] 增加 H 切片的 targeted tests 并完成 write-back
- [x] 确认下一方向为继续受控 dogfood，而不是立即起新的 planning-gate
- [ ] 若 dogfood 命中新 regression / gap signal，再起新的 planning-gate
- [x] 记录 driver / adapter / 转接层 backlog 已结构化为 BL-1 / BL-2 / BL-3
- [x] release 构建验证通过——双包 wheel 构建成功、内容物完整
- [x] release 安装验证通过——干净 venv 安装 → CLI 入口可用 → 资产可发现
- [x] 打包 `release/doc-based-coding-v1.0.0.zip`（双 wheel + AI 安装指南）
## Direction Candidates (post-v1.0)
- continued pre-release dogfood feedback capture — source: design_docs/Project Master Checklist.md, design_docs/direction-candidates-after-phase-35.md
- driver / adapter / transfer-layer backlog recording — source: design_docs/Project Master Checklist.md, design_docs/direction-candidates-after-phase-35.md
- next post-v1.0 narrow slice selection — source: design_docs/direction-candidates-after-phase-35.md
## Key Context Files
- CHANGELOG.md
- docs/first-stable-release-boundary.md
- docs/plugin-model.md
- docs/pack-manifest.md
- docs/project-adoption.md
- docs/subagent-management.md
- design_docs/phase-35-external-skill-interface-direction-analysis.md
- design_docs/stages/planning-gate/2026-04-12-external-skill-interaction-interface.md
- docs/installation-guide.md
- design_docs/stages/planning-gate/2026-04-11-doc-loop-enforcement-and-mcp-client-neutrality.md
- design_docs/stages/planning-gate/2026-04-11-installation-flow-documentation.md
- design_docs/tooling/Document-Driven Workflow Standard.md
- design_docs/stages/planning-gate/2026-04-12-conversation-progression-contract-stability.md
- design_docs/stages/planning-gate/2026-04-12-safe-stop-writeback-bundle.md
- design_docs/tooling/Dual-Package Distribution Standard.md
- design_docs/tooling/Session Handoff Standard.md
- design_docs/stages/planning-gate/2026-04-11-compatibility-metadata-and-version-declaration.md
- design_docs/stages/planning-gate/2026-04-11-official-instance-validator-check-contract.md
- design_docs/stages/planning-gate/2026-04-11-dual-package-minimal-install-implementation.md
- AGENTS.md
- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- design_docs/direction-candidates-after-phase-35.md
- .github/copilot-instructions.md
- .codex/handoffs/CURRENT.md
- .codex/handoffs/history/2026-04-11_2348_handoff-model-initiated-invocation_stage-close.md
