# Codex Interruption Recovery And Retry Policy

> Date: 2026-06-27
> Status: IMPLEMENTED

## Trigger

The Codex delivery supervisor now handles success, failure, and
permission-review outcomes. Runtime invocation audit already retries inside one
provider call and stores compact attempt records, but a failed delivery record is
terminal for later supervisor passes because the supervisor only scans
`pending` records.

That leaves a C4 gap: after a transient CLI/network/service failure or an
operator restart, the host cannot quickly resume eligible Codex work without
manual delivery-state surgery.

## Goal

Implement Gate C4 from
`design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`: make
interrupted or transient failed Codex delivery inspectable and retryable on
supervisor restart, without duplicating completed work and without retaining raw
transcripts or secrets.

## Scope

This gate includes:

1. a bounded retry policy for failed Codex delivery records;
2. retry eligibility based on stable failure kinds and max delivery attempts;
3. supervisor selection of retryable failed delivery records in addition to
   pending records;
4. compact retry metadata in delivery acknowledgement/readback;
5. preservation of acknowledged and review-required records as non-retryable;
6. focused tests proving restart-like retry after transient failure succeeds
   without duplicating completed scheduler events;
7. focused tests proving non-retryable failure remains failed.

## Non-goals

This gate does not:

1. resume a live Codex process mid-turn;
2. implement distributed leases or heartbeats;
3. implement a daemon;
4. expose live provider execution through MCP;
5. persist raw transcripts;
6. apply worker patches;
7. mutate agent-owned Local Work Trajectory from runtime code.

## Contract

The first C4 implementation treats restart recovery as durable delivery retry:

- `pending` delivery records remain eligible as before;
- failed Codex delivery records become eligible only when their `failure_kind`
  is retryable and `delivery_attempt_count` is below the supervisor retry cap;
- acknowledged and review-required records are never retried;
- successful retry acknowledges delivery and, when result consumption is
  enabled, appends one scheduler completion event;
- already completed scheduler tasks are skipped by recovery/admission checks and
  do not receive duplicate completion events;
- retry metadata is compact and credential-redacted;
- runtime invocation logs continue to show each host invocation attempt.

## Validation Plan

- Focused runtime test where the first supervisor pass records a retryable
  Codex failure, a second pass over the same delivery state succeeds, and
  recovered scheduler state is complete exactly once.
- Focused runtime test where a non-retryable Codex failure remains failed on a
  later supervisor pass.
- Focused runtime/readback assertion that acknowledged and review-required
  records are not retried.
- Focused CLI/help test for retry policy flags/wording if CLI options are
  added.
- `py_compile`, focused pytest selections, doc-loop validator, and
  `git diff --check`.

## Closure Criteria

This gate closes when a restarted/bounded Codex supervisor pass can recover
eligible transient failed delivery by retrying it under explicit policy, while
not duplicating already completed work and while preserving compact audit,
delivery, scheduler, and artifact authority boundaries.

## Implemented Surface

Runtime:

- Extended `CodexDeliverySupervisorRequest` with:
  - `retry_failed_delivery`
  - `retryable_failure_kinds`
  - `max_delivery_attempts_per_record`
- Extended `CodexDeliverySupervisorRecord` readback with `retry_attempt`.
- Extended `CodexDeliveryBoundedLoopRequest` with
  `max_delivery_attempts_per_record`.

Behavior:

- `run_codex_delivery_supervisor_once()` still processes `pending` delivery
  records by default.
- When `retry_failed_delivery=True`, failed delivery records are eligible if:
  - their `failure_kind` is in the retryable set;
  - their `delivery_attempt_count` is below
    `max_delivery_attempts_per_record`.
- A successful retry acknowledges the same delivery record and can consume the
  Codex result into one scheduler `task_completed` event.
- Non-retryable failed records remain failed and are not attempted.
- Already completed scheduler tasks are skipped rather than failed again.
- `run_bounded_codex_delivery_supervisor_loop()` enables failed-delivery retry
  for eligible records on later loop runs, so an operator restart can resume
  transient failed Codex work.

CLI:

- `doc-based-coding scheduler codex-delivery-supervisor-once` now exposes:
  - `--retry-failed-delivery`
  - `--max-delivery-attempts-per-record N`
- `doc-based-coding scheduler codex-delivery-supervisor-loop` now exposes:
  - `--max-delivery-attempts-per-record N`

Authority split:

- runtime invocation audit remains compact JSONL and does not store raw
  transcripts;
- delivery state remains the retry/acknowledgement authority;
- scheduler completion is still append-only event-log based;
- ExchangeArtifact store is only mutated after successful result consumption or
  permission-review evidence persistence;
- runtime code does not mutate agent-owned Local Work Trajectory.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\__main__.py src\runtime\orchestration\leader_worker_codex_delivery.py src\runtime\orchestration\codex_delivery_smoke.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "retries_retryable_failed_delivery_after_restart or does_not_retry_non_retryable_failed_delivery" -q
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "bounded_codex_delivery_supervisor_loop_retries_failed_delivery_after_restart" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery_supervisor_help_describes_result_consumption or codex_delivery_supervisor_loop_help_describes_c2_boundary" -q
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery or codex_result_consumer or codex_permission or bounded_codex_delivery_supervisor_loop or leader_worker_delivery or leader_worker_dispatcher or runtime_invocation" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery or leader_worker_delivery or runtime_invocation or scheduler_help_includes_exchange_artifact_admission" -q
```

Observed focused results:

```text
2 passed, 331 deselected
1 passed, 333 deselected
2 passed, 99 deselected
25 passed, 309 deselected
9 passed, 92 deselected
```

## Residual Risk After Close

This closes durable failed-delivery retry after restart. It does not resume a
live Codex process mid-turn, implement distributed leases/heartbeats, run a
daemon, apply patches, expose MCP live-provider execution, or provide a full
operator status dashboard.
