# Phase 30 完成后方向分析

> 基于 Phase 30 Dogfood Feedback Remediation Part 2 (F8 First) 完成时的观察
> 来源：`design_docs/dogfood-feedback-phase-27.md`、`design_docs/stages/planning-gate/2026-04-11-dogfood-feedback-remediation-part-2.md`、`design_docs/Project Master Checklist.md`、`design_docs/direction-candidates-after-phase-29.md`、`docs/official-instance-doc-loop.md`

## Phase 30 实施中的观察

1. `check` / `process` 的职责边界已经更清晰，纯约束 / 状态检查场景不再被完整治理链噪音淹没。
2. 当前剩余的 dogfood runtime 摩擦点已经主要收敛到 F4：PackRegistrar skipped validator 的真实原因和接口边界仍不透明。
3. 首个稳定 release 仍然是更高层目标，但在进入 release criteria 之前，先收掉 F4 能让运行时链路的可解释性更完整。

## 候选方向

### A. F4 Validator Diagnostics Follow-up

**描述**: 聚焦 PackRegistrar skipped validator 的诊断与接口语义，明确区分“路径问题”“模块加载失败”“脚本不满足 `validate()` 自动注册约定”等情况。

**来源**:
- `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/stages/planning-gate/2026-04-11-dogfood-feedback-remediation-part-2.md`
- `design_docs/Project Master Checklist.md`

**价值**: 收掉最后一个已知 dogfood 诊断盲点，为稳定版收口提供更清晰的 runtime 解释面。

### B. 首个稳定 Release 收口

**描述**: 建立首个稳定 release 的收口标准，定义何时可以把运行时链路提升为默认 self-hosting 主路径。

**来源**:
- `design_docs/stages/planning-gate/2026-04-11-self-hosting-workflow-rule.md`
- `design_docs/direction-candidates-after-phase-29.md`
- `design_docs/Project Master Checklist.md`

**价值**: 直接回应“稳定版前不默认依赖”的当前仓库决策，但需要在已知 runtime 摩擦基本透明后更稳妥地推进。

### C. 错误恢复与重试策略

**描述**: 为 Pipeline / CLI / MCP 增加异常分类、恢复建议和可选重试策略。

**来源**:
- `design_docs/phase-0-26-review.md`
- `review/research-compass.md`

**价值**: 对稳定版可靠性有帮助，但当前没有比 F4 更直接的样本驱动。

### D. CI/CD 集成

**描述**: 增加 pre-commit / GitHub Actions，自动运行 `pytest tests/`、pack 校验和 bootstrap 校验。

**来源**:
- `docs/project-adoption.md`
- `design_docs/phase-0-26-review.md`

**价值**: 稳定工程基线，但不如 A / B 直接回应当前 dogfood 和稳定版前置条件。

## 推荐排序

| 优先级 | 方向 | 理由 |
|---|---|---|
| 1 | **A. F4 Validator Diagnostics Follow-up** | 这是最后一个已知的 runtime dogfood 诊断盲点，范围仍然足够窄 |
| 2 | **B. 首个稳定 Release 收口** | 方向正确，但最好在 F4 清晰后再定 release criteria |
| 3 | **C. 错误恢复与重试策略** | 价值明确，但当前样本不足 |
| 4 | **D. CI/CD 集成** | 工程收益稳定，但不是当前最直接问题 |

## 倾向判断

**推荐 A 作为下一阶段。**

原因：
- 用户已经明确把稳定版作为默认 self-hosting 的前置条件。
- 在这种前提下，先把剩余的 F4 诊断盲点清掉，比立刻进入更宽的 release criteria 设计更稳。
- A 做完后，再进入稳定版收口，范围和依据都会更干净。