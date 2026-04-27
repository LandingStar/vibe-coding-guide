# Planning Gate — Project Progress Global Direction-Candidates Artifact Consistency Audit

> 日期: 2026-04-27
> 状态: COMPLETED
> 来源: `design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md`、`design_docs/direction-candidates-after-phase-35.md`

## Why this exists

在 `Global Direction-Candidates Section Recency Semantics` 完成后，当前下一条窄主线已切到真实 progress graph artifacts 的一致性审计。

当前已知信号说明这条 audit 不能再只停留在候选层：

1. `.codex/progress-graph/latest.json` 的 `latest_projection_at` 仍停在 `2026-04-26T17:10:41.936761+00:00`
2. `design_docs/direction-candidates-after-phase-35.md` 已在 2026-04-27 新增 `用户选定下一步` / `safe stop 后重新选定下一步` companion prose sections
3. 当前真实 artifact 尚未反映这些 2026-04-27 的文档更新，因此 release 前还缺一次针对 `.codex/progress-graph/latest.json` / `.dot` / `.html` 的 freshness + consistency spot check

## Scope

本 gate 只处理：

1. 固定 `direction-candidates-global` 的 artifact consistency audit boundary
2. 对真实 `.codex/progress-graph/latest.json`、`.dot`、`.html` 做 freshness precheck
3. spot check older plain lettered entries 与当前 latest numbered section 的纳入和状态一致性
4. 若问题只是 artifact stale，则刷新 artifacts 并复核结果
5. 若问题暴露为 projection 逻辑缺口，则只修复当前 audit 明确命中的最小控制路径
6. 在 audit 通过后，判断是否具备生成新 preview release 的条件

本 gate 不处理：

1. companion prose projection
2. selected-next-step linkage projection
3. 新的 graph node shape 或更宽的 prose 语义建模
4. UI / host workflow 扩展
5. 与 progress graph 无关的 release 叙事或大范围 state-surface 重写

## Working hypothesis

当前最小可行路线应是：

1. 当前最直接的 consistency gap 很可能是 artifact freshness 落后于 2026-04-27 文档更新，而不是 `build_global_direction_candidates_graph(...)` 的主逻辑再次失效
2. 只要重新生成并 spot check `latest.json` / `.dot` / `.html`，older plain lettered entries 与 latest numbered section 的状态应能与 source docs / targeted tests 对齐
3. 只有当刷新后仍出现 older plain lettered entries 缺失、status 错误或 current/latest section 错位时，才进入最小代码修复

## Slices

### Slice 1 — Audit contract and spot-check matrix

- 固定本次 audit 要核对的 source headings、artifact surfaces 与通过标准

当前状态：已完成。

### Slice 2 — Freshness check and artifact audit

- 对 `.codex/progress-graph/latest.json`、`.dot`、`.html` 执行 freshness precheck
- spot check older plain lettered entries、latest numbered section 与 current status
- 若确认为 stale artifacts，则刷新后重新核对

当前状态：已完成。

### Slice 3 — Minimal repair or release readiness judgment

- 若 audit 暴露最小 projection 缺口，则仅修复当前命中的控制路径并补最小验证
- 若 audit 通过，则把结果收束成 preview release readiness judgment

当前状态：已完成。

## Execution outcome

1. 确认本次问题是 `.codex/progress-graph/latest.*` stale，而不是 `build_global_direction_candidates_graph(...)` 投影逻辑再次回退
2. 重新生成 `.codex/progress-graph/latest.json`、`.dot`、`.html`，并 spot check older plain lettered entries 与 latest numbered section 的状态一致性
3. 通过 targeted regression：`pytest tests/test_progress_graph_doc_projection.py -q`（3 passed）
4. 判定当前 audit 已满足新的 preview release 边界，完成 `0.9.5` 版本面同步、pack lock 刷新与 release 打包
5. 通过 full suite 与 release consistency check，产出 `release/doc-based-coding-v0.9.5.zip`

## Validation gate

- `tests/test_progress_graph_doc_projection.py -q` 至少通过当前受影响的 targeted checks
- 真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 与 `design_docs/direction-candidates-after-phase-35.md` 当前选定范围一致
- 若触及代码，必须留下最小可执行验证；若只刷新 artifacts，也要留下 freshness + spot-check 记录

## Stop condition

- 当 artifact freshness、older plain lettered entries 一致性与 latest numbered section 状态都已确认后停止
- 不在本 gate 内顺手进入 companion prose / linkage projection
- 若 audit 结果表明当前链路已经满足 preview release 条件，则在本 gate 结束后进入 release 生成