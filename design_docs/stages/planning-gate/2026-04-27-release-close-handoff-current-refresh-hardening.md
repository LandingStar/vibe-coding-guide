# Planning Gate — Release-Close Handoff / CURRENT Refresh Hardening

> 日期: 2026-04-27
> 状态: ACTIVE
> 来源: `design_docs/v0.9.5-preview-release-followup-direction-analysis.md`、`design_docs/Project Master Checklist.md`

## Why this exists

当前 `0.9.5` preview release 已构建、验证并打包完成，但 release-close 的恢复入口仍存在明显漂移：

1. `design_docs/Project Master Checklist.md` 的 `Current Handoff Footprint` 仍指向 `2026-04-27_1931_global-direction-candidates-section-recency-semantics_stage-close`
2. `.codex/checkpoints/latest.md` 的 `Current Handoff` 仍是同一旧 safe stop
3. `.codex/handoffs/CURRENT.md` 尚未刷新到本次 release-close 的真实安全停点
4. 本轮 release 证明 release 本体可重复生成，但 safe-stop / handoff / authority-doc footprint 仍主要依赖人工串联，而不是被当前 release-close 路径稳定收口

用户已在 post-release 下一方向中明确选定这条 B 线，因此需要先把问题收窄成新的 planning-gate，而不是把它继续留在 release 注释或会话总结里。

## Scope

本 gate 只处理：

1. 固定本次 release-close drift 的最小状态面边界：canonical handoff、`.codex/handoffs/CURRENT.md`、Checklist footprint、checkpoint footprint，以及必要的 phase-map 记录
2. 判断当前问题是否可通过既有 `handoff generate` + `refresh current` 路径收口，而无需新增 schema 或大范围重构
3. 若既有路径不足，只修补当前命中的最小控制路径，让 release-close 能与 handoff / authority-doc footprint 保持一致
4. 在状态面写回后刷新 `.codex/progress-graph/latest.json` / `.dot` / `.html`

本 gate 不处理：

1. handoff history ledger 或更宽的 trace redesign
2. 新的 handoff schema、额外 audit event type 或通用 safe-stop executor 改写
3. `companion prose projection`
4. `selected-next-step linkage projection`
5. post-release install UX / extension 安装向导

## Working hypothesis

当前最小可行路线应是：

1. 当前 gap 更像 release-close workflow 没有稳定串起既有 handoff 更新路径，而不是 handoff data model 本身缺字段
2. 先固定哪些文件必须在 release-close 后对齐，可以快速区分“只是漏执行既有 refresh”与“现有 helper 还缺一个必要控制点”
3. 只有在既有 `generate / refresh current` 路径无法把 release-close 结果写到当前权威状态面时，才进入最小代码修补

## Slices

### Slice 1 — Drift surface and writeback target contract

- 固定 release-close 后必须对齐的状态面、成功标准与 out-of-scope

当前状态：ACTIVE。

### Slice 2 — Minimal refresh path decision

- 判断应沿既有 handoff workflow 串联收口，还是需要补最小 automation/hardening

当前状态：pending。

### Slice 3 — Smallest repair and verification

- 实施选定最小路径，更新状态面并刷新 progress graph artifacts，再留下最小验证

当前状态：pending。

## Validation gate

- `Current Handoff Footprint`、checkpoint `Current Handoff` 与 `.codex/handoffs/CURRENT.md` 指向同一最新 canonical handoff
- 若触及代码，必须留下当前控制路径的最小可执行验证
- 状态面写回后必须刷新 `.codex/progress-graph/latest.json` / `.dot` / `.html`

## Stop condition

- 当 release-close 的最新 handoff pointer 与 authority-doc footprint 对齐后停止
- 不在本 gate 内顺手扩大为通用 handoff 自动化重构
- 若发现问题超出“release-close 对齐”边界，先写回新的 direction-analysis 或 planning-gate，而不是继续扩 scope