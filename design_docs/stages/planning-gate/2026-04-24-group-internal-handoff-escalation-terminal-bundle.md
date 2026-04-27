# Planning Gate — Group Internal Handoff / Escalation Terminal Bundle

> 日期: 2026-04-24
> 状态: COMPLETE
> 关联方向分析: `design_docs/group-internal-handoff-escalation-terminal-semantics-direction-analysis.md`
> 对照分析: `design_docs/group-internal-handoff-escalation-terminal-semantics-comparison.md`

## 1. Why this gate exists

Route A 当前已经完成：

1. parallel-safe subgraph foundation
2. executor-local real multi-child batch
3. shared-review zone contract / preflight
4. zone-approved payload writeback semantics

因此当前 executor-local parallel runtime 已经拥有一条最小闭环：

- lineage / namespace
- strict preflight + shared-review zone 例外
- grouped review driver / grouped summary
- reviewer `approve` 后的 approval-driven grouped payload writeback

剩下最明显、且此前被显式延后的空洞是：

- 当 group 内某个 child 产生 `handoff` 或 `escalation` 时，整个 group 应如何收口为 terminal outcome

此前多份文档都故意先禁止这条路径，以免 scope 失控。现在重新起 gate 的原因，不是我们突然想扩 scope，而是其它更底层语义已经形成闭环，这条边界终于值得被单独处理。

## 2. Scope

本 gate 只处理：

1. group 内 child 的 `handoff` / `escalation` 如何升级成 group terminal outcome
2. grouped review / grouped writeback 遇到该 terminal outcome 时如何停止、延迟或转向
3. audit / tracing / checkpoint / summary 的最小 companion/result surface

本 gate 不处理：

1. orchestration bridge / daemon runtime
2. team/swarm scheduler
3. patch-level merge
4. 更深层跨 group 调度

## 3. Working hypothesis

当前最小可行路线应是：

1. child 仍可产生 `handoff` / `escalation` 请求
2. parent 不把它们当普通 child success 合并进 grouped review / writeback
3. 而是把 group 收口成一个明确的 terminal bundle，作为后续 authority transfer / human escalation 的唯一入口

## 4. Slices

### Slice 1 — Terminal bundle contract + comparison review

- 固定 group terminal bundle 的最小合同面
- 对比三条候选语义：group-level bundle / child-local continue / keep forbidden
- 明确第一版默认推荐与 stop condition

当前状态：基础实现已落地到 `src/interfaces.py` / `src/pep/executor.py`；当前已新增 `GroupTerminalOutcome` companion object、executor `group_terminal_outcome` 序列化 helper、以及基于显式 `escalation_recommendation` 的最小 terminal bundle stop/turn 路径。相关回归 `tests/test_collaboration.py` 已通过（50 passed）。

### Slice 2 — Result / summary / audit surface

- 定义 group terminal outcome 如何进入 result surface
- 定义 grouped review / grouped writeback summary 遇到该终态时的表现
- 定义最小 audit/tracing 字段

当前状态：显式 escalation 路径下的 result / summary / audit surface 已形成最小闭环。executor 现已在 `group_terminal_prepared` audit 事件 detail 中镜像 `suppressed_surfaces` 与 `blocked_reason`，`src/pep/writeback_engine.py` 也已把同一 suppression 镜像到 grouped review / grouped child writeback summary；相关联合回归 `tests/test_collaboration.py` + `tests/test_pep_writeback_integration.py` 已通过（74 passed）。当前下一窄切口收束为：是否把显式 child handoff 证据也接入同一 terminal bundle 与 validator/executor 路径。

### Slice 3 — Guard / validator / executor integration

- 决定 executor preflight / execution path 在何处识别该终态
- 补最小验证门
- 保证现有 shared-review/writeback 闭环不回归

当前状态：显式 child handoff 证据现已接入同一 terminal bundle。child report 可以携带正式 `Handoff` 对象作为 authority-transfer evidence；valid handoff 会收口为 `terminal_kind = handoff`，invalid handoff 则会在 subgraph child 路径经 `handoff_validator` 降级为 blocked child result，避免其伪装成普通 success。相关联合回归 `tests/test_collaboration.py` + `tests/test_pep_writeback_integration.py` + `tests/test_subagent_modules.py` 已通过（98 passed）。

## 5. Validation gate

- 文档验证：
  - terminal bundle 与对照分析能明确回答 authority transfer 到底挂在哪一层
  - 明确哪些路径仍禁止，哪些路径只允许进入 terminal bundle
- 未来代码验证：
  - group 内 child 触发 handoff 时不会继续进入普通 grouped review / writeback
  - escalation 会形成可审计的 group terminal outcome
  - 既有 multi-child `all_clear` 与 shared-review zone 路径不回归

## 6. Stop condition

- 当 terminal bundle contract、summary/audit 口径、以及 executor integration 入口都被说清楚后停止
- 不在本 gate 内扩展到更高层 orchestration runtime