# Planning Gate - Monitoring UI Backend API

> Date: 2026-06-28
> Status: COMPLETED

## Trigger

After C9, the Codex worker runtime has durable evidence for live lane-distinct
concurrency, serialized writeback, compact runtime invocation audit, and
repeatable smoke readback. The next product need is an operator-facing
monitoring UI, but the frontend visual design should be handled in a separate
session.

This gate therefore builds the backend/read-model contract first and documents
how the frontend should consume it.

## Scope

Implement a frontend/backend-separated monitoring surface:

1. add a read-only backend API/read model for orchestration monitoring;
2. expose the read model through CLI as a stable JSON surface that a host UI or
   later HTTP/webview adapter can call;
3. summarize scheduler state, leader-worker delivery state, runtime invocation
   audit, C9 smoke report, worker report consumption surfaces, and actionable
   operator signals;
4. write detailed API usage documentation for frontend/API integrators;
5. write frontend UI expectation documentation for the next visual design
   session.

## Non-Goals

This gate does not:

1. implement final frontend visuals;
2. add a persistent daemon;
3. add WebSocket streaming;
4. mutate scheduler, delivery, runtime, exchange, Local Work Trajectory, or
   worker report artifacts;
5. expose raw transcripts or secret-bearing logs;
6. add distributed worker leases or live process resume.

## Backend API Contract

The first read model should be a snapshot API. It may be called repeatedly by a
future UI poller.

Required sections:

1. `scheduler`: task state counts, target task states, waiting/blocked/review
   task ids, known lanes, and next-action clue.
2. `delivery`: delivery state counts, pending Codex delivery count, failed
   delivery summaries, review-required summaries.
3. `runtimeInvocations`: compact counts, latest records, failed records, and
   overlap/concurrency hints.
4. `liveCodexSmoke`: optional C9 report summary if present.
5. `workerReports`: paths/surface hints for worker trajectory report
   consumption, without directly reading arbitrary raw report directories in
   the first slice.
6. `operatorSignals`: prioritized issues and suggested next host actions.
7. `authoritySplit`: read-only, redacted, no raw transcript, no Local Work
   Trajectory mutation.

## Acceptance Criteria

This gate may close when:

1. a runtime helper returns a structured monitoring snapshot without mutation;
2. a CLI command prints the snapshot as JSON;
3. missing optional files are represented as absent/unavailable instead of
   crashing;
4. the snapshot includes C9 live smoke report summary when the report exists;
5. focused runtime and CLI tests cover healthy, missing-file, and C9-report
   readback cases;
6. docs describe API usage and frontend expectations in enough detail for a
   separate frontend session to proceed.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/monitoring_api.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "monitoring_api" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "monitoring_api" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

No screenshot validation is required for this backend/API gate because it does
not implement frontend visuals. The follow-up frontend visual gate must use a
screenshot-capable validation tool before acceptance.

## Implementation

Implemented a read-only monitoring snapshot API:

1. runtime helper:
   `src/runtime/orchestration/monitoring_api.py`;
2. runtime API:
   `inspect_monitoring_snapshot(MonitoringSnapshotRequest)`;
3. CLI:
   `doc-based-coding scheduler inspect-monitoring-snapshot`;
4. backend API documentation:
   `docs/monitoring-ui-backend-api.md`;
5. frontend visual handoff expectations:
   `design_docs/monitoring-ui-frontend-expectations.md`.

The snapshot composes existing readback surfaces and does not replace them:

1. scheduler recovery via snapshot/event log;
2. leader-worker delivery inspection;
3. compact runtime invocation audit inspection;
4. artifact ref summary through the exchange artifact store;
5. optional C9 live Codex concurrent-worker smoke report summary;
6. worker report consumption hints without consuming reports.

The frontend-facing JSON uses stable top-level sections:

```text
scheduler
delivery
runtimeInvocations
liveCodexSmoke
workerReports
operatorSignals
authoritySplit
```

## Completion Evidence

Validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/monitoring_api.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "monitoring_api" -q
2 passed, 346 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "monitoring_snapshot" -q
2 passed, 110 deselected
```

Adjacent validation passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "live_codex_concurrent_worker_smoke or monitoring_api or bounded_codex_delivery_supervisor_loop_runs_lane_distinct_codex_concurrently" -q
5 passed, 343 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "live_codex_concurrent_worker_smoke or monitoring_snapshot or codex_delivery_supervisor_loop" -q
8 passed, 104 deselected
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
Validation passed
```

## Closure

This gate closes the backend/API portion of monitoring UI work. The next UI
session can design visuals from `docs/monitoring-ui-backend-api.md` and
`design_docs/monitoring-ui-frontend-expectations.md` without reading internal
JSONL files directly.
