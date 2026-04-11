# Phase 27 完成后方向分析

> 基于 Phase 27 Dogfood 深度验证完成时的观察
> 来源：`design_docs/dogfood-feedback-phase-27.md`、`design_docs/phase-0-26-review.md`、`docs/pack-manifest.md`、`docs/project-adoption.md`、`review/research-compass.md`

## Phase 27 实施中的观察

1. 真实 dogfood 比纯测试更快暴露状态恢复和 phase 推进中的逻辑缺口。
2. 当前 blocking 级问题已修复，但中优先级问题仍集中在“分类准确率”和“状态同步一致性”。
3. Pack gap analysis 已接近收口，剩余 `depends_on/provides` 等字段价值较低。
4. 平台功能面已完整，下一阶段更应关注可靠性与实际使用摩擦，而不是继续堆功能。

## 候选方向

### A. Dogfood Feedback Remediation

**描述**: 继续收敛 Phase 27 中未修复的中优先级问题，重点包括：
- `issue-report` 关键词扩充（"bug"/"错误"/"异常"/"崩溃"/"error"）
- `current_phase` / checkpoint / planning-gate 状态同步策略
- PackRegistrar skipped validator 的路径解析检查
- CLI `check` 输出精简

**来源**:
- `design_docs/dogfood-feedback-phase-27.md` — F1/F4/F5/F8
- `review/research-compass.md` — dogfood-first / error recovery / operator ergonomics

**价值**: 直接提升真实使用可靠性，避免下一轮 dogfood 反复踩同一类坑。

### B. 错误恢复与重试策略

**描述**: 为 Pipeline / CLI / MCP 调用增加更明确的异常分类、恢复建议与可选重试策略。

**来源**:
- `review/research-compass.md` — OpenHands / LangGraph 的恢复机制
- `design_docs/phase-0-26-review.md` — 后续候选方向表中的“错误恢复”

**价值**: 提升生产可用性，但需要在现有问题收敛后再做更稳妥。

### C. CI/CD 集成

**描述**: 增加 pre-commit / GitHub Actions，把 `pytest tests/`、bootstrap 校验、pack 校验纳入自动化。

**来源**:
- `docs/project-adoption.md`
- `design_docs/phase-0-26-review.md` — 后续候选方向表中的“CI/CD 集成”

**价值**: 进一步固化基线，减少回归，但不直接解决当前 dogfood 暴露的产品问题。

### D. Pack 尾部间隙收口

**描述**: 实施 `depends_on` 校验、`provides` 消费、`checks` manifest 直连。

**来源**:
- `docs/pack-manifest.md`
- `design_docs/phase-0-26-review.md` — “未实施的有意省略”

**价值**: 闭合规范，但当前只有单 pack 主路径，优先级低。

## 推荐排序

| 优先级 | 方向 | 理由 |
|---|---|---|
| 1 | **A. Dogfood Feedback Remediation** | 问题已有明确样本，修复收益直接且可验证 |
| 2 | **B. 错误恢复与重试策略** | 可靠性建设的自然延伸，但应在 A 之后 |
| 3 | **C. CI/CD 集成** | 稳定基线有价值，但不如 A 直接 |
| 4 | **D. Pack 尾部间隙收口** | 规范完整性工作，当前业务收益最低 |

## 倾向判断

**推荐 A 作为 Phase 28。**

原因：
- 它直接来自 Phase 27 的真实使用反馈，而不是推测性 backlog。
- 范围可收窄为 3-4 个点，适合继续用 planning-gate 切片推进。
- 完成后可以马上再做一次 dogfood，验证 Phase 27 的反馈是否真正被消化。
