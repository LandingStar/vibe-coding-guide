# ExchangeArtifact Operator Admission CLI Review — 2026-06-19

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-operator-admission-cli.md`.

Verdict: ready for close.

The slice adds a CLI-first operator surface over the existing exact-version
admission helper. It gives host scripts and operators a non-Python way to admit
stored scheduler submission artifacts while keeping MCP stored-artifact write
exposure, provider execution, scheduler projection refresh, and artifact
lifecycle consumption out of scope.

## Implementation Evidence

Changed:

- `src/__main__.py`
  - added `doc-based-coding scheduler <subcommand>`
  - added `doc-based-coding scheduler admit-exchange-artifact`
  - resolves relative paths under the detected project root
  - defaults the artifact store to `.codex/orchestration/exchange-artifacts.json`
  - requires explicit scheduler snapshot and event-log paths
- `tests/test_cli.py`
  - covered scheduler help, admission help, single-task CLI admission,
    missing required paths, and non-submission rejection without scheduler
    mutation
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - documented CLI operator admission and non-goals
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - kept bootstrap prompt copy in sync
- `tests/test_doc_loop_prompts.py`
  - guarded the CLI guidance text

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| CLI admits an exact stored single-task artifact and writes scheduler state. | `test_scheduler_admit_exchange_artifact_cli_submits_exact_single_task`. | Met |
| Required-argument failures are clear and non-mutating. | `test_scheduler_admit_exchange_artifact_cli_requires_explicit_paths`. | Met |
| Non-submission artifacts fail before scheduler mutation. | `test_scheduler_admit_exchange_artifact_cli_rejects_non_submission_without_mutation`. | Met |
| CLI result exposes task IDs and authority clues. | Single-task CLI test asserts `submitted_task_ids`, `state_written`, `ran_tasks=false`, `refreshed_projection=false`, and `authority_split.local_work_trajectory_mutated=false`. | Met |
| Prompt guidance distinguishes resource inspection, CLI admission, and MCP non-goal. | `tests/test_doc_loop_prompts.py -k scheduler`. | Met |

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
12 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k scheduler
1 passed, 17 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
261 passed
```

The `tests/test_cli.py` run returned exit code 0 after reporting `12 passed`.
The recurring Windows/Python access-violation printout appeared after pytest
reported success. This matches the residual signal recorded in recent reviews
and did not correspond to a failed assertion. The combined focused suite later
reported `261 passed` with exit code 0 and no access-violation printout.

## Residual Risk

1. The CLI is an admission surface only. It does not run the scheduler or
   refresh the scheduler-derived trajectory projection.
2. There is still no stored-artifact MCP write tool. That remains intentional
   until a separate gate accepts the larger trust surface.
3. The exchange artifact is not marked consumed. Lifecycle/ledger behavior
   remains a future decision.
4. The recurring Windows/Python pytest access-violation printout should still
   be watched if it starts producing non-zero exits or appears in normal CLI
   paths.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

1. Add an operator-facing projection refresh or admission-result inspection
   polish only if users need a smoother CLI workflow.
2. Keep stored-artifact MCP write exposure as a separate reviewed gate.
3. Do not combine this with provider execution or scheduler daemon behavior.
