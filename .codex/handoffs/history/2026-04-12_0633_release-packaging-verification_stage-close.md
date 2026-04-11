---
handoff_id: 2026-04-12_0633_release-packaging-verification_stage-close
entry_role: canonical
kind: stage-close
status: draft
scope_key: release-packaging-verification
safe_stop_kind: stage-complete
created_at: 2026-04-12T06:33:33+08:00
supersedes: null
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
conditional_blocks: []
other_count: 0
---

# Summary

Release 封装验证已完成：双发行包构建、干净环境安装、空项目 adoption 端到端验证全部通过。可分发安装包 `release/doc-based-coding-v1.0.0.zip` 已生成（含 AI 安装指南 + 双 wheel）。当前仓库处于无 active planning gate 的 safe stop。

## Boundary

- 完成到哪里：release 构建验证 + 安装验证 + adoption 端到端验证 + 可分发 zip 打包
- 为什么这是安全停点：所有验证通过，状态文档已写回，无未完成的实现工作
- 明确不在本次完成范围内的内容：CI/CD 发布自动化、PyPI 发布、runtime `src` 命名空间重命名

## Authoritative Sources

- `design_docs/Project Master Checklist.md` — 总状态板
- `design_docs/Global Phase Map and Current Position.md` — 阶段图
- `design_docs/direction-candidates-after-phase-35.md` — 方向候选文档
- `design_docs/tooling/Dual-Package Distribution Standard.md` — 双发行包标准
- `release/README.md` — release 验证结果与状态
- `release/INSTALL_GUIDE.md` — AI 安装指南
- `.codex/checkpoints/latest.md` — 最新 checkpoint

## Session Delta

- 本轮新增：`release/INSTALL_GUIDE.md`、`release/doc-based-coding-v1.0.0.zip`
- 本轮修改：`release/README.md`、`.gitignore`（dist-verify*、.venv-*、release/*.zip）、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`（A 状态更新）、`.codex/checkpoints/latest.md`
- 本轮形成的新约束或新结论：
  - 构建时 setuptools 残留的 egg-info 会干扰后续干净 venv 安装，需提前清理
  - runtime 包顶层命名空间为 `src`，如需发布到 PyPI 应重命名
  - adoption 端到端路径已验证可用：zip 解压 → 安装 → bootstrap → validate → MCP

## Verification Snapshot

- 自动化：双包 wheel 构建成功（runtime 83KB, instance 48KB）；干净 venv 安装 + CLI 入口验证通过；adoption 端到端（bootstrap 21 文件 + info + validate + generate-instructions + MCP 启动）全部通过
- 手测：无
- 未完成验证：CI/CD 流水线未配置、PyPI 发布流程未验证
- 仍未验证的结论：无

## Open Items

- 未决项：CI/CD 自动化依赖发布目标选择（PyPI？GitHub Releases？私有 registry？）
- 已知风险：runtime `src` 命名空间与其他包潜在冲突（仅 PyPI 场景）
- 不能默认成立的假设：无

## Next Step Contract

- 下一会话建议只推进：继续受控 dogfood，或在确定发布目标后配置 CI/CD
- 下一会话明确不做：不在未确认发布目标前搭建 CI/CD
- 为什么当前应在这里停下：核心验证已全部通过，剩余工作依赖外部决策（发布目标）

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：release 构建 + 安装 + adoption 验证三层验证全部通过，可分发安装包已打包
- 当前不继续把更多内容塞进本阶段的原因：CI/CD 自动化依赖发布目标决策，属于不同切片

## Planning-Gate Return

- 应回到的 planning-gate 位置：当前无 active gate，safe stop
- 下一阶段候选主线：继续受控 dogfood + 按需 CI/CD 配置
- 下一阶段明确不做：不做 runtime `src` 命名空间重命名（除非用户明确要求 PyPI 发布）

## Conditional Blocks

None.

## Other

None.
