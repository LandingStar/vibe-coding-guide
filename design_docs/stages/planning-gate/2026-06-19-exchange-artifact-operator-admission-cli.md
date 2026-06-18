# Planning Gate — ExchangeArtifact Operator Admission CLI

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`review/exchange-artifact-exact-version-scheduler-admission-2026-06-19.md`
recommended a narrow operator/host admission surface over
`admit_exchange_artifact_version_to_scheduler()`.

Direction analysis:

- `design_docs/exchange-artifact-operator-admission-surface-direction-analysis.md`

## Problem

The runtime can admit an exact stored scheduler submission artifact, and the
resource surface can inspect stored candidates, but an operator still needs a
stable non-Python command to trigger admission without exposing a broader MCP
write surface.

The command must preserve the existing authority split:

1. Exchange artifact store supplies the exact coordination product version.
2. Scheduler snapshot and event log remain the scheduling authority.
3. Admission does not imply provider execution or projection refresh.

## Scope

### Slice 1 — CLI Command

Add:

```text
doc-based-coding scheduler admit-exchange-artifact
```

Required options:

```text
--artifact-id ID
--version VERSION
--snapshot-path PATH
--event-log-path PATH
```

Optional options:

```text
--artifact-store-path PATH
--replace-existing
--timestamp TIMESTAMP
```

Behavior:

1. Resolve relative paths under the detected project root.
2. Default `--artifact-store-path` to
   `.codex/orchestration/exchange-artifacts.json`.
3. Require explicit scheduler snapshot and event-log paths.
4. Call `admit_exchange_artifact_version_to_scheduler()`.
5. Print JSON containing `ok=true` plus the helper result.
6. Print a readable stderr error and return exit code 1 on helper rejection.

### Slice 2 — CLI Validation

Add focused tests for:

1. Help text advertises the scheduler/admission command.
2. A stored exact single-task artifact can be admitted from a temp project.
3. Missing required options fail with usage.
4. Non-submission artifacts fail without creating snapshot/event-log files.
5. The result reports `authority_split.local_work_trajectory_mutated=false`.

### Slice 3 — Guidance And Write-Back

Update scheduler smoke prompt guidance so operators know:

1. `resources read dbc://exchange-artifacts/bundle` is read-only inspection.
2. `scheduler admit-exchange-artifact` is CLI admission.
3. Admission still does not run providers or refresh projection.
4. MCP stored-artifact write exposure remains out of scope.

## Non-Goals

This gate does not:

1. Add a stored-artifact MCP write/admission tool.
2. Add UI controls.
3. Run scheduler tasks, Qoder, fake runtime, or any provider.
4. Refresh `.codex/progress-graph/scheduler-work-trajectory.json`.
5. Mark exchange artifacts consumed, accepted, rejected, or superseded.
6. Choose default scheduler snapshot or event-log paths.
7. Mutate `.codex/progress-graph/local-work-trajectory.json`.

## Acceptance Criteria

The gate may close when:

1. The CLI command admits an exact stored single-task artifact and writes the
   scheduler snapshot/event log.
2. Required-argument failures are clear and non-mutating.
3. Non-submission stored artifacts fail before scheduler mutation.
4. CLI result JSON exposes submitted task IDs and authority clues.
5. Focused CLI/runtime/doc-loop tests pass.
6. Status docs and review record the non-goals and authority split.

## Implementation Notes

### 2026-06-19 — CLI Operator Admission Surface

Added:

```text
doc-based-coding scheduler admit-exchange-artifact
```

The command accepts exact artifact identity plus explicit scheduler persistence
paths:

```text
--artifact-id
--version
--snapshot-path
--event-log-path
--artifact-store-path
--replace-existing
--timestamp
```

Relative paths resolve under the detected project root. If
`--artifact-store-path` is omitted, the command reads the conventional local
store:

```text
.codex/orchestration/exchange-artifacts.json
```

The implementation delegates to
`admit_exchange_artifact_version_to_scheduler()` and prints JSON with `ok=true`
plus `PersistedExchangeArtifactAdmissionResult.to_json_dict()`. It does not
run providers, refresh scheduler projection, mark exchange artifacts consumed,
expose a stored-artifact MCP write tool, or mutate Local Work Trajectory.

Updated:

- `src/__main__.py`
- `tests/test_cli.py`
- `tests/test_doc_loop_prompts.py`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
12 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k scheduler
1 passed, 17 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
261 passed
```

The CLI test run returned exit code 0 after reporting `12 passed`. The same
Windows/Python access-violation printout observed in previous focused runs
appeared after pytest reported success; it remains a residual test-process
signal rather than a failed assertion. The combined focused suite later
reported `261 passed` with exit code 0 and no access-violation printout.
