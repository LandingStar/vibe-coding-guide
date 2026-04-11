# Phase 28 完成后方向分析

> 基于 Phase 28 Dogfood Feedback Remediation 完成时的观察
> 来源：`design_docs/dogfood-feedback-phase-27.md`、`design_docs/direction-candidates-after-phase-27.md`、`design_docs/phase-0-26-review.md`、`docs/project-adoption.md`、`review/research-compass.md`

## Phase 28 实施中的观察

1. `issue-report` 修正和 checkpoint 同步都是“高收益、小改动”的问题，说明 dogfood 反馈值得继续收敛。
2. 当前剩余问题主要集中在操作性细节，而不是核心架构缺口。
3. 平台主链路已稳定到 566 passed, 2 skipped，继续堆功能的收益在下降。

## 候选方向

### A. Dogfood Feedback Remediation Part 2

**描述**: 继续收敛剩余的两个 dogfood 反馈项：
- F4: PackRegistrar skipped validator 的路径解析/诊断
- F8: CLI `check` 输出过多，拆分为更清晰的约束检查与治理结果

**来源**:
- `design_docs/dogfood-feedback-phase-27.md` — F4/F8
- `design_docs/direction-candidates-after-phase-27.md` — 方向 A 的剩余部分

**价值**: 继续消化真实使用中的摩擦点，形成第二轮 dogfood 的更干净基线。

### B. 错误恢复与重试策略

**描述**: 为 Pipeline / CLI / MCP 增加异常分类、恢复建议和可选重试策略。

**来源**:
- `design_docs/phase-0-26-review.md` — 后续候选方向“错误恢复”
- `review/research-compass.md` — LangGraph / OpenHands 恢复机制

**价值**: 提升鲁棒性，但现在还缺少新的失败样本驱动具体设计。

### C. CI/CD 集成

**描述**: 增加 pre-commit / GitHub Actions，自动运行 `pytest tests/`、pack 校验和 bootstrap 校验。

**来源**:
- `docs/project-adoption.md`
- `design_docs/phase-0-26-review.md` — 后续候选方向“CI/CD 集成”

**价值**: 固化工程基线，但对当前 dogfood 体验提升不如 A 直接。

### D. Pack 尾部间隙收口

**描述**: 实施 `depends_on` 校验、`provides` 消费、`checks` manifest 直连。

**来源**:
- `docs/pack-manifest.md`
- `design_docs/phase-0-26-review.md` — “未实施的有意省略”

**价值**: 规范完整性工作，当前仍是低优先级。

## 推荐排序

| 优先级 | 方向 | 理由 |
|---|---|---|
| 1 | **A. Dogfood Feedback Remediation Part 2** | 直接来自真实使用反馈，改动仍可控 |
| 2 | **B. 错误恢复与重试策略** | 自然的可靠性延伸，但需要更具体样本 |
| 3 | **C. CI/CD 集成** | 工程收益稳定，但不是当前痛点 |
| 4 | **D. Pack 尾部间隙收口** | 规范收口，业务收益最低 |

## 倾向判断

**推荐 A 作为 Phase 29。**

原因：
- 还剩两项真实 dogfood 摩擦点没有处理完。
- 范围依旧窄，可以继续用 planning-gate 切片推进。
- 做完后再跑一次 dogfood，才更适合决定是否进入错误恢复或 CI/CD。