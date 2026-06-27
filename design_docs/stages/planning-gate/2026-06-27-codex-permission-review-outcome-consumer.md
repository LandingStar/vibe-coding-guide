# Codex Permission Review Outcome Consumer

> Date: 2026-06-27
> Status: IMPLEMENTED

## Trigger

Gate C2 can repeatedly deliver Codex worker tasks and consume successful
results, but the Codex delivery supervisor currently sends every successful
`RuntimeRunResult` through the success consumer when
`consume_success_results=True`. That is unsafe when the result includes
`permission_requests`: those runs need scheduler-owned review state instead of
`task_completed`.

## Goal

Implement Gate C3 from
`design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`: Codex
permission and review-required outcomes must become explicit recoverable
scheduler and delivery state, without being acknowledged as completed work.

## Scope

This gate includes:

1. a narrow Codex permission/review result consumer path;
2. reuse of the existing scheduler `task_review_required` event semantics;
3. durable delivery readback that distinguishes `review_required` from
   `acknowledged` and `failed`;
4. compact permission request metadata in delivery acknowledgement/readback;
5. focused tests proving downstream dependencies stay waiting;
6. focused CLI/help/readback wording updates if the existing CLI surface
   exposes the changed behavior.

## Non-goals

This gate does not:

1. implement a UI approval panel;
2. redesign permission policy or approval UX;
3. automatically approve or deny permission requests;
4. apply worker patches;
5. resume interrupted Codex sessions;
6. expose live Codex execution through MCP;
7. mutate agent-owned Local Work Trajectory from runtime code.

## Contract

When a Codex runtime result contains permission requests:

- the scheduler event log receives one `task_review_required` event;
- recovered scheduler state shows the task as `review_required`;
- the task output artifact reference is preserved as review evidence;
- no `task_completed` event is appended;
- downstream dependencies that require completion remain waiting;
- delivery is marked `review_required`, not `acknowledged` or provider
  `failed`;
- delivery metadata contains compact permission request facts, not raw
  transcripts or secrets;
- approval or rejection remains a separate scheduler-owned transition through
  the existing permission review resolver.

## Validation Plan

- Focused runtime test where a Codex result includes one permission request and
  `consume_success_results=True`.
- Assert scheduler event log contains `task_review_required` and no
  `task_completed` for that task.
- Assert recovered scheduler state has the Codex task `review_required` and a
  dependent task still waiting.
- Assert delivery state counts include `review_required`, not `acknowledged` or
  `failed`, for that record.
- Assert runtime invocation audit still records the provider attempt as
  succeeded.
- Focused CLI/help test for permission/review wording.
- `py_compile`, focused pytest selections, doc-loop validator, and
  `git diff --check`.

## Closure Criteria

This gate closes when the Codex delivery supervisor can safely consume
permission-requesting Codex results into durable review-required state, with no
false scheduler completion and no downstream wake-up until a scheduler-owned
permission approval event resolves the review.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/codex_permission_review_consumer.py`.
- New request/result models:
  - `CodexPermissionReviewConsumerRequest`
  - `CodexPermissionReviewConsumerResult`
- New helper:
  - `consume_codex_permission_review_result()`

Supervisor integration:

- `run_codex_delivery_supervisor_once()` now checks
  `RuntimeRunResult.permission_requests` before successful result consumption.
- Permission-requesting Codex runs:
  - store the output artifact as review evidence in
    `JsonArtifactVersionStore`;
  - append a scheduler `task_review_required` event;
  - mark delivery `review_required`;
  - include compact permission request metadata in supervisor and delivery
    readback;
  - do not append `task_completed`;
  - do not acknowledge delivery as completed work.

Delivery schema:

- Extended leader-worker delivery status/target/event support with
  `review_required` / `delivery_review_required`.
- Existing delivery state files remain readable; the new state appears only
  when a host-owned delivery attempt produces permission-review output.

CLI:

- Updated `doc-based-coding scheduler codex-delivery-supervisor-once --help`
  to describe the permission-review branch.

Authority split:

- scheduler snapshot remains unmutated;
- scheduler lifecycle advancement is append-only event-log based;
- ExchangeArtifact store keeps review evidence durable;
- delivery state distinguishes review-required from success and failure;
- runtime invocation audit still records the provider attempt;
- MCP live-provider surface remains absent;
- runtime code does not mutate agent-owned Local Work Trajectory.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\__main__.py src\runtime\orchestration\leader_worker_delivery.py src\runtime\orchestration\leader_worker_codex_delivery.py src\runtime\orchestration\codex_permission_review_consumer.py src\runtime\orchestration\__init__.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery_supervisor or codex_result_consumer or codex_permission" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery_supervisor" -q
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery or codex_result_consumer or leader_worker_delivery or leader_worker_dispatcher or runtime_invocation" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery or leader_worker_delivery or runtime_invocation or scheduler_help_includes_exchange_artifact_admission" -q
```

Observed focused results:

```text
11 passed, 320 deselected
4 passed, 97 deselected
20 passed, 311 deselected
9 passed, 92 deselected
```

## Residual Risk After Close

This closes permission-review outcome consumption only. Interruption/in-progress
resume, transient retry policy binding, runtime invocation log compaction policy
binding for the supervisor loop, source workspace patch review integration, MCP
live-provider execution, true process-level parallelism, and operator-friendly
status readback still require separate contract gates.
