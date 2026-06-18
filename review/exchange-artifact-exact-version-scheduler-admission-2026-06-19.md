# ExchangeArtifact Exact-Version Scheduler Admission Review — 2026-06-19

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-exact-version-scheduler-admission.md`.

Verdict: ready for close.

The slice adds a runtime helper that consumes one exact stored
`ExchangeArtifact` version and admits it into scheduler-owned snapshot/event-log
state. It keeps the exchange artifact store as source material only; scheduler
snapshots remain the task-contract authority.

## Implementation Evidence

Changed:

- `src/runtime/orchestration/scheduler_submission.py`
  - added `PersistedSchedulerTaskSubmissionResult`
  - added `PersistedExchangeArtifactAdmissionResult`
  - added `submit_scheduler_task_with_persistence()`
  - added `admit_exchange_artifact_version_to_scheduler()`
  - shared submission-event writing between single and batch persistence paths
- `src/runtime/orchestration/__init__.py`
  - exported the new admission and persistence surfaces
- `tests/test_runtime_orchestration.py`
  - covered exact single admission, exact batch admission, missing version,
    non-submission rejection, ambiguous scheduler payload rejection, and
    malformed store propagation
- `tests/test_doc_loop_prompts.py`
  - guarded the scheduler smoke prompt guidance for exact-version admission
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - documented exact-version admission and non-goals
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - kept bootstrap prompt copy in sync
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Exact stored single-task submission persists into scheduler state. | `test_admit_exchange_artifact_version_submits_exact_single_task`. | Met |
| Exact stored batch submission persists into scheduler state. | `test_admit_exchange_artifact_version_submits_exact_batch`. | Met |
| Missing exact versions fail clearly. | `test_admit_exchange_artifact_version_reports_missing_exact_version`. | Met |
| Non-submission artifacts are rejected before scheduler mutation. | `test_admit_exchange_artifact_version_rejects_non_submission_without_mutation`. | Met |
| Ambiguous scheduler payloads are rejected. | `test_admit_exchange_artifact_version_rejects_ambiguous_submission_payloads`. | Met |
| Malformed stores surface existing readable store errors. | `test_admit_exchange_artifact_version_surfaces_malformed_store_error`. | Met |
| No Local Work Trajectory or scheduler projection side effects. | Single-task test asserts no projection/local trajectory artifacts are created; result authority split reports both false. | Met |
| Prompt guidance records non-goals. | Scheduler smoke prompt and bootstrap copy mention `admit_exchange_artifact_version_to_scheduler()`. | Met |

## Validation

Targeted validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "admit_exchange_artifact_version or submit_scheduler_task_batch_with_persistence"
7 passed, 145 deselected
```

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "admit_exchange_artifact_version or json_artifact_version_store or exchange_artifact_store_inspection or scheduler_task_submission or scheduler_task_batch_submission" tests/test_doc_loop_prompts.py -k "scheduler"
60 passed, 110 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
249 passed
```

The final focused run returned exit code 0 after reporting `249 passed`. The
Windows Python process again printed access-violation stacks after pytest
reported success. This matches the previous slice's residual test-process
signal and did not correspond to a failed assertion.

## Residual Risk

1. The helper is a Python/runtime surface only. There is still no
   operator-facing stored-artifact admission command, MCP tool, or UI control.
2. The exchange artifact is not marked consumed. That is intentional for this
   slice, but a future lifecycle/admission ledger may need to record
   consumption separately.
3. Existing scheduler submission validation remains the contract authority for
   task shape; the helper does not add a separate schema layer.
4. The recurring Windows/Python pytest access-violation printout should still
   be watched if it begins producing non-zero exits or appears in normal CLI
   paths.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

1. Add a narrow operator/host admission surface over
   `admit_exchange_artifact_version_to_scheduler()` if stored-artifact
   admission needs to be triggered outside Python tests.
2. Keep it separate from provider execution and scheduler projection refresh,
   unless a later gate explicitly chooses a combined workflow.
