# Slice 1 Draft — Release-Close Handoff / CURRENT Refresh Hardening

## Contract focus

本 Slice 只固定 `0.9.5` release-close 之后哪些状态面必须一起对齐，以及“对齐完成”到底意味着什么。

## Alignment surfaces

1. latest canonical handoff 本体
2. `.codex/handoffs/CURRENT.md` 的 active mirror pointer
3. `design_docs/Project Master Checklist.md` 中的 `Current Handoff Footprint`
4. `.codex/checkpoints/latest.md` 中的 `Current Handoff`
5. 如当前 active gate / phase narrative 被改变，则补最小 `design_docs/Global Phase Map and Current Position.md` 记录

## Success rule

1. 四类 pointer surface 指向同一 latest canonical handoff
2. 当前 active planning-gate 与 latest completed slice 的表述不再自相矛盾
3. 更新后的 authority state 能重新投影到 `.codex/progress-graph/latest.json` / `.dot` / `.html`

## Decision fork to settle in Slice 2

### A. Reuse existing handoff workflow only

- 做什么：用现有 `generate` / `refresh current` 路径收口 release-close，对当前漂移只补边界和调用顺序，不新增自动化入口
- 适合条件：如果现有 workflow 已经足够，只是本轮 release-close 没有走完它

### B. Add minimal release-close hardening

- 做什么：在既有 handoff workflow 仍不够的前提下，只补当前缺失的最小 control path，让 release-close 更不容易再次漏掉 `CURRENT.md` / authority-doc footprint 对齐
- 适合条件：如果复用现有路径仍无法稳定把 release-close 写到当前状态面

## Out of scope

1. 重新设计 handoff schema
2. 增加新的 history ledger 或 tracing layer
3. 扩展到 install / dogfood / companion prose 主线