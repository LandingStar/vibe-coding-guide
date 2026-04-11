# Phase 29 完成后方向分析

> 基于 Phase 29 Self-Hosting Workflow Rule Formalization 完成时的观察
> 来源：`design_docs/stages/planning-gate/2026-04-11-self-hosting-workflow-rule.md`、`design_docs/Project Master Checklist.md`、`design_docs/dogfood-feedback-phase-27.md`、`design_docs/direction-candidates-after-phase-28.md`、`docs/official-instance-doc-loop.md`、`docs/current-prototype-status.md`

## Phase 29 实施中的观察

1. 当前仓库已经正式确认：文档型成果应立即自用，但运行时链路在首个稳定 release 前仍是 pre-release dogfood 入口。
2. 这意味着“真正把项目用起来”的前置条件已经收敛为稳定版收口，而不是继续抽象讨论是否应该自用。
3. 当前剩余的 F4 / F8 与默认入口升级路径，比新增功能更直接影响首个稳定版落地。

## 候选方向

### A. 首个稳定 Release 收口

**描述**: 围绕“何时可以把运行时链路提升为默认 self-hosting 主路径”建立第一版收口标准，补齐 release criteria、关键 bug burn-down、默认入口升级条件。

**来源**:
- `design_docs/stages/planning-gate/2026-04-11-self-hosting-workflow-rule.md`
- `design_docs/Project Master Checklist.md`
- `docs/current-prototype-status.md`

**价值**: 直接回应当前用户判断，把“先出稳定版再真正默认自用”变成可执行的下一阶段目标。

### B. Dogfood Feedback Remediation Part 2

**描述**: 继续收敛剩余的两个 dogfood 反馈项：
- F4: PackRegistrar skipped validator 的路径解析 / 诊断
- F8: CLI `check` 输出过多，拆分为更清晰的约束检查与治理结果

**来源**:
- `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/direction-candidates-after-phase-28.md`

**价值**: 继续降低 pre-release dogfood 摩擦，也可能成为稳定版收口前的必要清单。

### C. 错误恢复与重试策略

**描述**: 为 Pipeline / CLI / MCP 增加异常分类、恢复建议和可选重试策略。

**来源**:
- `design_docs/phase-0-26-review.md`
- `review/research-compass.md`

**价值**: 能提升稳定版可靠性，但更适合在 A 或 B 确认后进入，以免范围再次发散。

### D. CI/CD 集成

**描述**: 增加 pre-commit / GitHub Actions，自动运行 `pytest tests/`、pack 校验和 bootstrap 校验。

**来源**:
- `docs/project-adoption.md`
- `design_docs/phase-0-26-review.md`

**价值**: 有助于稳定版基线，但对当前“能否默认自用”问题不如 A 和 B 直接。

## 推荐排序

| 优先级 | 方向 | 理由 |
|---|---|---|
| 1 | **A. 首个稳定 Release 收口** | 已经被用户明确设为默认 self-hosting 的前置条件 |
| 2 | **B. Dogfood Feedback Remediation Part 2** | 直接消化剩余 runtime 摩擦，可能并入 A 的收口清单 |
| 3 | **C. 错误恢复与重试策略** | 对稳定版有价值，但需要更明确的失败样本 |
| 4 | **D. CI/CD 集成** | 工程收益稳定，但不是当前 gating 问题 |

## 倾向判断

**推荐 A 作为下一阶段。**

原因：
- 现在的关键不是“要不要自用”，而是“何时够稳定才允许默认自用”。
- 用户已经把首个稳定 release 设为前置条件，A 直接把这个条件变成可执行目标。
- B 仍然重要，但更适合作为 A 的组成部分或并行 checklist，而不是替代 A。