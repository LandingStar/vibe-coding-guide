# Planning Gate — Shared-Review Zone Contract And Preflight

> 创建时间: 2026-04-24
> 状态: COMPLETE

## 文档定位

本文件把 `shared-review zone` 方向收敛为下一条可执行的窄 scope planning contract。

本候选直接承接：

- `design_docs/parallel-safe-subgraph-shared-review-zone-direction-analysis.md`
- `design_docs/parallel-safe-subgraph-conflict-bearing-grouped-review-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-24-executor-local-real-multichild-subgraph-batch.md`
- `docs/subagent-management.md`
- `docs/subagent-schemas.md`

当前只锁定**声明式 shared-review zone companion fields + preflight 例外路径 + grouped review 标记**，不提前进入 patch-level merge、group 内 handoff / escalation、或 thread-level scheduler。

## 当前问题

- 当前 real multi-child 第一版边界已经固定为 strict preflight + `all_clear-only`
- 当前 contract / preflight 只有两种语义：
  - `allowed_artifacts` 不重叠 -> 允许 dispatch
  - `allowed_artifacts` 重叠 -> 直接 preflight 拦截
- 若要让 conflict-bearing grouped review 在真实 multi-child runtime 中重新变成可达路径，需要一条显式、可审计、默认收紧的 overlap 例外机制

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/parallel-safe-subgraph-shared-review-zone-direction-analysis.md`
- `design_docs/parallel-safe-subgraph-conflict-bearing-grouped-review-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-24-executor-local-real-multichild-subgraph-batch.md`
- `docs/subagent-management.md`
- `docs/core-model.md`
- `docs/subagent-schemas.md`
- `src/interfaces.py`
- `src/pep/executor.py`

## 候选阶段名称

- `Shared-Review Zone Contract And Preflight`

## 本轮只做什么

- 为 child batch / `TaskGroup` 固定 shared-review zone 的最小 companion fields
- 固定 preflight 如何区分：
  - 默认禁止 overlap
  - 显式 shared-review zone 下允许 overlap 但强制进入 grouped review
- 固定 grouped review outcome 如何标记 zone-driven `review_required`
- 固定审计 / writeback / checkpoint 口径如何描述 shared-review zone child group

## 本轮明确不做什么

- 不做 patch-level 或 section-level merge
- 不做 group 内 handoff
- 不做 group 内 escalation
- 不做 thread-level parallel scheduler
- 不重写现有 `Subagent Contract` / `Subagent Report` 主 schema 家族

## 当前推荐的最小对象边界

当前默认不引入新的大对象。第一轮只允许补充 companion metadata：

1. child-level shared-review zone identity
2. group-level zone membership / approval hints
3. preflight classification reason for zone-driven overlap

当前推荐保持两条原则：

1. 默认仍然是 strict preflight，zone 只是显式例外，不是新默认
2. zone 允许的是“进入 grouped review 的资格”，不是自动 merge 权限

## 当前推荐的运行规则

### 1. Zone declaration rule

- 只有 parent-built child batch 可以声明 shared-review zone
- child 必须显式声明 zone identity，不能由 runtime 自动推断 overlap 后临时归组
- 未声明 zone 的 overlap 仍按当前 strict preflight 直接拦截

### 2. Preflight rule

- 默认 disjoint write set 规则继续保留
- 若 overlap child 明确属于同一 shared-review zone，则 preflight 不直接 `blocked`
- preflight 必须留下 machine-readable reason，说明该 overlap 是 zone-driven exception

### 3. Review rule

- 进入 shared-review zone 的 child group，join policy 默认倾向 `review_required`
- `GroupedReviewOutcome` 需要能区分：
  - 普通 conflict-driven `review_required`
  - shared-review-zone-driven `review_required`

### 4. Writeback rule

- shared-review zone 不改变当前 writeback 总原则
- 只有 grouped review 被显式 apply 后，相关 child payload 才允许进入 writeback planning

## 当前推荐的实施顺序

### Slice 1 — Companion fields + preflight exception surface

- 详细设计草案见：`design_docs/shared-review-zone-slice1-contract-draft.md`
- 定义最小 shared-review zone companion fields
- 扩展 preflight 结果，区分 strict overlap rejection 与 zone-driven allowed overlap

当前状态：基础实现已开始并落地到 `src/interfaces.py` / `src/pep/executor.py`；当前已新增 `ParallelChildTask.shared_review_zone_id`、preflight `overlap_decisions`、以及 same-artifact zone-driven overlap 例外。定向回归已通过。

### Slice 2 — Grouped review marking + audit surface

- 让 grouped review outcome 能表达 zone-driven `review_required`
- 同步审计与结果面字段

当前状态：基础实现已落地到 `src/interfaces.py` / `src/pep/executor.py`；当前已为 merge/grouped review 增加 `review_driver` 与 `shared_review_zone_ids`，并把 zone-driven driver 接到 audit detail。定向回归已通过。

### Slice 3 — Writeback planning alignment

- 明确 zone-driven grouped review 在 apply 后如何进入现有 grouped child payload writeback
- 只做 planning / contract 对齐，不扩 patch merge

当前状态：writeback planning 对齐已落地到 `src/pep/writeback_engine.py`；grouped review writeback summary 现已保留 `review_driver` 与 `shared_review_zone_ids`。定向回归已通过。

## 验收与验证门

- 针对性测试：
  - shared-review zone companion fields 的最小输入校验
  - preflight 对 zone-driven overlap 的允许/拒绝分类
  - grouped review outcome 对 zone-driven `review_required` 的标记测试
- 更广回归：
  - strict preflight 的现有 `all_clear-only` 路径不回归
  - executor-local multi-child 与 grouped child payload writeback 现有回归不回归
- 手测入口：
  - 两个 child overlap 但无 zone，预期 preflight `blocked`
  - 两个 child overlap 且属于同一 zone，预期 preflight 放行但 grouped review `review_required`

## 需要同步的文档

- `docs/subagent-management.md`
- `docs/core-model.md`
- `docs/subagent-schemas.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（仅当本候选完成并进入 safe stop 时）

## 子 agent 切分草案

- 若需要只读盘点，可让 investigator 汇总当前 overlap rejection、grouped review 标记与 writeback planning 的最接近复用点
- zone 字段命名、preflight 例外规则、以及 planning-gate write-back 仍由主 agent 负责

## 收口判断

- 为什么这条切片可以单独成立：它只增加一条显式 overlap 例外路径，不会把现有 strict preflight 与 path-boundary contract 整体推翻
- 做到哪里就应该停：当 shared-review zone companion fields、preflight exception、grouped review 标记与 writeback summary 对齐都成立后就应停，不继续扩到 patch merge 或终态 authority transfer
- 下一条候选主线是什么：
  - 若继续沿 shared-review zone 深化，应先分析“review 已批准后是否允许 zone-driven payload writeback”
  - 若要回到更高层协作语义，则单独分析 group 内 handoff / escalation terminal semantics
  - 若在设计中发现 child contract 不适合承载 zone metadata，再单独起 task-group review zone map 对比文档