# Phase 31 完成后方向分析

> 基于 Phase 31 F4 Validator Diagnostics Follow-up 完成时的观察
> 来源：`design_docs/dogfood-feedback-phase-27.md`、`design_docs/stages/planning-gate/2026-04-11-f4-validator-diagnostics-followup.md`、`design_docs/Project Master Checklist.md`、`design_docs/direction-candidates-after-phase-30.md`、`docs/official-instance-doc-loop.md`

## Phase 31 实施中的观察

1. F8 和 F4 两个直接影响 dogfood 可解释性的 CLI / diagnostics 问题都已经收口。
2. 当前运行时链路仍然被明确标记为 pre-release，但“为什么它现在还不能默认依赖”的未知项已经少了很多。
3. 在这种状态下，最自然的下一步不再是继续修 dogfood 盲点，而是把首个稳定 release 的收口条件正式化。

## 候选方向

### A. 首个稳定 Release 收口

**描述**: 建立首个稳定 release 的收口标准，定义何时可以把运行时链路提升为默认 self-hosting 主路径。

**来源**:
- `design_docs/stages/planning-gate/2026-04-11-self-hosting-workflow-rule.md`
- `design_docs/Project Master Checklist.md`
- `docs/current-prototype-status.md`

**价值**: 直接回应当前仓库已经确认的边界，把“稳定版前不默认依赖”推进为一条可执行的 release 主线。

### B. 错误恢复与重试策略

**描述**: 为 Pipeline / CLI / MCP 增加异常分类、恢复建议和可选重试策略。

**来源**:
- `design_docs/phase-0-26-review.md`
- `review/research-compass.md`

**价值**: 对稳定版可靠性有帮助，但优先级低于 A，因为 A 先定义了“要达到什么程度才算稳定”。

### C. CI/CD 集成

**描述**: 增加 pre-commit / GitHub Actions，自动运行 `pytest tests/`、pack 校验和 bootstrap 校验。

**来源**:
- `docs/project-adoption.md`
- `design_docs/phase-0-26-review.md`

**价值**: 可以帮助稳定版基线，但更适合作为 A 的配套，而不是替代 A。

### D. Validator 语义升级讨论

**描述**: 单独讨论 script-style validator 是否应该拥有不同于 `validate(data) -> dict` 的长期协议入口。

**来源**:
- `design_docs/stages/planning-gate/2026-04-11-f4-validator-diagnostics-followup.md`
- `design_docs/dogfood-feedback-phase-27.md`

**价值**: 现在已经不是阻塞项，除非稳定版收口明确需要统一 validator 语义，否则应保持低优先级。

## 推荐排序

| 优先级 | 方向 | 理由 |
|---|---|---|
| 1 | **A. 首个稳定 Release 收口** | 现在最需要把“稳定前不默认依赖”转成正式 release 目标 |
| 2 | **B. 错误恢复与重试策略** | 对稳定版可靠性有帮助，但应放在 A 之后 |
| 3 | **C. CI/CD 集成** | 工程收益稳定，但更像 A 的配套工作 |
| 4 | **D. Validator 语义升级讨论** | 诊断已清楚，短期不必升格为主线 |

## 倾向判断

**推荐 A 作为下一阶段。**

原因：
- 当前两轮 dogfood 修复已经把最直接的 UX / diagnostics 盲点消化掉了。
- 用户之前已经明确表示，真正默认自用要等首个稳定 release。
- 现在最有价值的工作是把“什么叫稳定 enough”写成一条窄 scope planning-gate，而不是继续零散修补。