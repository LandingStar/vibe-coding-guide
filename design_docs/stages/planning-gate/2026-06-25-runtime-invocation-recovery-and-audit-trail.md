# Runtime Invocation Recovery And Audit Trail

> Date: 2026-06-25
> Status: IMPLEMENTED

## Trigger

Codex/Qoder runtime wrappers can report retryable failures, and scheduler state
can recover from snapshot plus event log, but runtime invocation attempts are
not yet persisted as a compact auditable stream and retry orchestration is not
available as a reusable host-owned layer.

## Goal

Add a narrow runtime invocation audit and retry contract that records bounded,
redacted attempt metadata for provider calls and can retry retryable failures
without changing the low-level provider client semantics.

## Scope

This gate includes:

1. a provider-neutral `RuntimeInvocationRecord` / `RuntimeAttemptRecord`
   contract;
2. JSONL persistence for compact runtime invocation records;
3. redaction and bounded excerpt handling for error/log summaries;
4. a reusable retry runner that wraps a provider call and records every
   attempt;
5. readback/compaction helpers for old invocation records;
6. host-owned Codex/Qoder guide-worker provider wrapper integration;
7. focused tests for success, retryable failure recovery, fail-fast behavior,
   compaction, and wrapper-level retry/audit wiring.

## Non-goals

This gate does not:

1. change `CodexCliProcessClient` or `QoderSDKQueryClient` retry behavior;
2. persist raw runtime transcripts;
3. start an always-on daemon or OS service;
4. expose a live provider through MCP;
5. build a Web UI;
6. mutate agent-owned Local Work Trajectory from runtime code.

## Contract

Runtime invocation audit records are append-only JSONL records. They must be
safe to inspect in normal project artifacts:

- command/env/token values must be absent or redacted;
- stdout/stderr/raw model transcripts must not be persisted;
- bounded excerpts may be stored only after explicit redaction;
- every record must identify provider, invocation id, task/session/run ids when
  available, status, attempt count, retry policy, and final error summary.

Retry belongs to the host/scheduler orchestration wrapper, not the raw provider
client. A provider call is retried only when the raised error exposes
`retryable=True` and the configured retry limit has not been reached.

## Validation Plan

- Focused runtime tests for audit store and retry runner.
- Focused import/compile validation for runtime modules.
- `git diff --check`.
- Compact Checklist writeback after close.

## Closure Criteria

This gate closes when the project has a tested, provider-neutral audit/retry
facility and the current host-owned Codex/Qoder guide-worker provider wrapper
uses it without changing the existing low-level client contracts.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/runtime_invocation_audit.py`.
- New contract:
  - `RuntimeRetryPolicy`
  - `RuntimeAttemptRecord`
  - `RuntimeInvocationRecord`
  - `RuntimeInvocationLogSummary`
  - `RuntimeInvocationCompactionResult`
- New JSONL store: `JsonlRuntimeInvocationLog`.
- New runner: `run_with_runtime_invocation_audit()`.
- New readback helpers:
  - `inspect_runtime_invocation_log()`
  - `compact_runtime_invocation_log()`
  - `runtime_invocation_record_from_json_dict()`

CLI:

- Added `doc-based-coding scheduler inspect-runtime-invocations`.
- Default readback path:
  `.codex/runtime/invocations.jsonl`.
- Added host-owned guide-worker smoke flags for Codex and Qoder:
  - `--runtime-invocation-log-path`
  - `--runtime-invocation-max-attempts`
  - `--runtime-invocation-backoff-seconds`

Host-owned wrapper:

- `run_host_owned_guide_worker_provider_execution()` now wraps injected or
  constructed Qoder/Codex provider clients before building the runtime registry.
- Default invocation audit path:
  `.codex/runtime/invocations.jsonl`.
- Default retry policy:
  `max_attempts=2`, `backoff_seconds=0.0`.
- The wrapper records one compact JSONL record per provider client invocation,
  including retryable failures that later recover.

The runner retries only when an exception exposes `retryable=True` and the
configured `RuntimeRetryPolicy.max_attempts` allows another attempt. The raw
provider clients remain unchanged.

The audit record explicitly reports:

- `raw_transcript_persisted=false`;
- no scheduler mutation;
- no ExchangeArtifact mutation;
- no Local Work Trajectory mutation.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\__main__.py src\runtime\orchestration\runtime_invocation_audit.py src\runtime\orchestration\leader_worker_activation.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py tests\test_cli.py -k "runtime_invocation or leader_worker_activation or scheduler_help_includes_exchange_artifact_admission" -q
```

Observed focused result:

```text
15 passed, 397 deselected
```

Additional wrapper integration validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\__main__.py src\runtime\orchestration\runtime_invocation_audit.py tools\progress_graph\guide_worker_provider_execution.py tests\test_progress_graph_trajectory.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_progress_graph_trajectory.py -k "guide_worker_provider_execution_audits_and_retries_qoder_invocation or host_owned_guide_worker_provider_execution_runs_mock_qoder_wave or host_owned_guide_worker_provider_execution_runs_planned_codex_workers" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_guide_worker_smoke_help_describes_host_owned_boundary or qoder_guide_worker_smoke_help_describes_host_owned_boundary or runtime_invocation or leader_worker_activation or scheduler_help_includes_exchange_artifact_admission" -q
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "runtime_invocation or leader_worker_activation" -q
```

Observed focused results:

```text
3 passed, 76 deselected
5 passed, 87 deselected
10 passed, 308 deselected
```

## Residual Risk After Close

This slice now covers the current host-owned guide-worker provider wrapper, but
it is still not an always-on dispatcher or process supervisor. Readiness/auth
failures that occur before a provider invocation is created remain readiness
errors rather than runtime invocation records.
