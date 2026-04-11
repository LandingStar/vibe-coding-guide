# Planning Gate — Dogfood Feedback Remediation Part 2 (F8 First)

- Status: **CLOSED**
- Phase: 30
- Date: 2026-04-11

## 问题陈述

Phase 27 的 dogfood 反馈还剩两个未收敛的 runtime 摩擦点，而它们现在已经直接影响“首个稳定 release 之前能否继续高质量 dogfood”：

2. **F8**: CLI `check` 命令同时输出约束检查和完整治理链，对纯状态恢复 / 约束检查场景噪音过大。

Phase 29 已经把“文档型成果立即自用、运行时入口在稳定版前保持 pre-release dogfood”写成长期规则。基于这个边界，F4/F8 现在应被视为 pre-release runtime ergonomics 的直接 backlog，而不是可无限后推的低价值杂项。

## 审核后边界

用户已确认当前 Phase 30 先只处理 **F8**，保持 CLI `check` 切片最窄；**F4** 后拆为单独诊断切片，避免当前 Phase 牵出 validator 接口语义扩 scope。

## 权威输入

- `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/direction-candidates-after-phase-29.md`
- `design_docs/stages/planning-gate/2026-04-11-self-hosting-workflow-rule.md`
- `src/pack/registrar.py`
- `src/__main__.py`

## 本轮只做什么

### Slice A: PackRegistrar skipped validator diagnostics

当前 Phase 不做。F4 后拆为独立切片。

### Slice B: CLI `check` 输出分层

- 调整 `src/__main__.py` 中 `check` 命令的输出边界，让它默认聚焦约束 / 状态检查
- 保留完整治理链入口，但不要在纯 `check` 场景里默认混出完整 PDP → PEP 结果
- 视需要补充帮助文本或新增更清晰的输出结构
- 补测试，覆盖 `check` 命令输出形状和帮助文本

## 本轮明确不做什么

- 不制定首个稳定 release 的完整 criteria
- 不进入错误恢复 / 重试策略
- 不做 CI/CD 集成
- 不处理 F4；后续单独起诊断切片
- 不处理 `depends_on` / `provides` / `checks` 的其他尾部 gap
- 不修改 MCP 协议层，除非 CLI 输出分层必须同步一个极小修补

## 验收与验证门

- F8 的 `check` 输出不再默认混入完整治理链细节
- 新增或更新的相关 pytest 通过
- 如实现触及 CLI 主入口，跑对应 targeted tests；必要时再跑全量回归

## 需要同步的文档

- `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`

## 收口判断

- 该切片进一步收窄：当前只处理 F8
- 只要 `check` 输出分层完成并有测试覆盖，就应收口
- 完成后再决定是否立刻补 F4 诊断，或并入稳定版收口计划