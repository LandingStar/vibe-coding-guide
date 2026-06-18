# Planning Gate - ExchangeArtifact Operator Admission Workflow Polish

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

The completed CLI admission gate left the operator workflow split across
inspection, exact-version admission, optional scheduler readback, and optional
scheduler-derived projection refresh.

Direction analysis:

- `design_docs/exchange-artifact-operator-admission-followup-direction-analysis.md`

## Problem

`doc-based-coding scheduler admit-exchange-artifact` can admit one exact stored
scheduler submission artifact, but an operator still has no CLI-only way to
verify the resulting scheduler snapshot and event-log state or to refresh the
scheduler-derived trajectory projection without an MCP host.

The next slice should polish the operator workflow while preserving the
authority split:

1. Exchange artifact inspection remains read-only.
2. Exact-version admission writes scheduler snapshot and event-log state.
3. Scheduler readback inspects scheduler authority without mutation.
4. Scheduler projection refresh writes only the scheduler-derived view artifact.
5. Provider execution and agent-owned Local Work Trajectory mutation remain out
   of scope.

## Scope

### Slice 1 - Scheduler State Readback CLI

Add:

```text
doc-based-coding scheduler inspect-state
```

Required options:

```text
--snapshot-path PATH
```

Optional options:

```text
--event-log-path PATH
--merge-gate-event-log-path PATH
```

Behavior:

1. Resolve relative paths under the detected project root.
2. Read the scheduler snapshot and optional JSONL logs.
3. Print compact JSON with task/dependency/run/merge counts, task state counts,
   task IDs by state, and event-log clues.
4. Return exit code 1 with a readable error if the snapshot cannot be read.
5. Do not write scheduler state, projection artifacts, exchange artifacts, or
   Local Work Trajectory.

### Slice 2 - Scheduler Projection CLI

Add:

```text
doc-based-coding scheduler project
```

Required options:

```text
--snapshot-path PATH
```

Optional options:

```text
--event-log-path PATH
--merge-gate-event-log-path PATH
--output-path PATH
--trajectory-id ID
--title TITLE
--guide-context PATH_OR_LABEL
--source-graph-id ID
--source-node-id ID
```

Behavior:

1. Resolve relative paths under the detected project root.
2. Read the scheduler snapshot and optional scheduler history logs.
3. Write `.codex/progress-graph/scheduler-work-trajectory.json` by default, or
   the explicit output path when provided.
4. Print JSON with projection path, trajectory identity, event/lane/relation
   counts, and authority clues.
5. Do not run providers or mutate `.codex/progress-graph/local-work-trajectory.json`.

### Slice 3 - Workflow Guidance And Tests

Update prompt guidance and tests so the intended operator sequence is visible:

```text
doc-based-coding resources read dbc://exchange-artifacts/bundle
doc-based-coding scheduler admit-exchange-artifact ...
doc-based-coding scheduler inspect-state ...
doc-based-coding scheduler project ...
```

## Non-Goals

This gate does not:

1. Add a stored-artifact MCP write/admission tool.
2. Add scheduler daemon behavior or durable queue processing.
3. Add UI binding.
4. Run fake, Qoder, or any other provider.
5. Mark exchange artifacts consumed, accepted, rejected, or superseded.
6. Choose global default scheduler snapshot or event-log paths.
7. Mutate `.codex/progress-graph/local-work-trajectory.json`.

## Acceptance Criteria

The gate may close when:

1. The CLI help advertises admission, readback, and projection as separate
   scheduler operator actions.
2. A temp-project workflow can inspect stored candidates, admit an exact
   version, inspect scheduler state, and refresh scheduler projection.
3. Readback returns event-log clues without writing new artifacts.
4. Projection writes only the scheduler-derived trajectory artifact.
5. Missing required paths and missing snapshots fail clearly.
6. Focused CLI/doc-loop/runtime/MCP tests pass.
7. Status docs and review record the authority split and deferred candidates.

## Implementation Notes

### 2026-06-19 - CLI Readback And Projection Fallbacks

Added:

```text
doc-based-coding scheduler inspect-state
doc-based-coding scheduler project
```

`inspect-state` reads a scheduler snapshot plus optional scheduler and
merge-gate event logs, then prints compact JSON with task/dependency/run/merge
counts, task state counts, task IDs by state, dependency IDs, event IDs, event
kind counts, and authority clues. It is read-only and does not write scheduler
state, projection artifacts, exchange artifacts, or Local Work Trajectory.

`project` reads the scheduler snapshot plus optional scheduler history logs and
writes the scheduler-derived trajectory artifact, defaulting to:

```text
.codex/progress-graph/scheduler-work-trajectory.json
```

The command prints projection path, trajectory identity, event/lane/relation
counts, metadata, and authority clues. It does not run providers, mutate
scheduler state, mark exchange artifacts consumed, expose a stored-artifact MCP
write tool, or mutate `.codex/progress-graph/local-work-trajectory.json`.

Updated:

- `src/__main__.py`
- `tests/test_cli.py`
- `tests/test_doc_loop_prompts.py`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
18 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k scheduler
1 passed, 17 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
267 passed
```
