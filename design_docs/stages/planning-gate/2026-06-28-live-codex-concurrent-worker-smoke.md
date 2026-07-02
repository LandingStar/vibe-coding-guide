# Planning Gate - Live Codex Concurrent Worker Smoke

> Date: 2026-06-28
> Status: COMPLETED

## Trigger

The completed Codex Concurrent Delivery Gate proves the supervisor can run a
lane-distinct concurrent runtime batch through fake-client validation. A test
workspace inspection then showed that the available smoke artifacts prove
scheduler-level parallel waves, but do not yet prove live Codex CLI worker
processes overlapped in a real run.

The next narrow gap is evidence quality, not a broad scheduler redesign: create
a repeatable live smoke that leaves durable, redacted proof of how many Codex
workers were started, which lanes they owned, whether at least two were
concurrently active, and how their reports were consumed by the leader-owned
write-back path.

## Scope

This gate defines and then implements a live Codex concurrent worker smoke:

1. seed or construct a small scheduler-owned test fixture with at least two
   independent lane-distinct Codex worker tasks and one dependent fan-in task;
2. run the existing bounded Codex delivery supervisor with
   `max_concurrent_deliveries >= 2`;
3. execute live Codex worker runtime invocations through the existing
   host-owned wrapper and runtime invocation audit path;
4. persist per-worker compact evidence: worker id, lane id, task id, runtime
   provider, invocation id, started-at, finished-at, terminal state, output
   artifact ref, and redacted failure/retry metadata when applicable;
5. persist batch-level evidence that can distinguish scheduling parallelism
   from process-level overlap;
6. consume worker `Subagent Report.trajectory_update` only through the
   leader/main/supervisor `consumeWorkerTrajectoryReport` path or matching CLI
   surface;
7. write a concise test-workspace report that says exactly how many workers ran
   and whether live process-level concurrency was proven.

## Evidence Contract

The smoke cannot be considered passing unless its artifacts answer these
questions without relying on chat transcript memory:

1. How many worker tasks were created?
2. How many distinct worker runtime invocations were attempted?
3. Which worker tasks were in the first concurrent batch?
4. Did at least two live Codex invocations have overlapping active intervals?
5. Were result consumption and delivery acknowledgement serialized after
   runtime completion?
6. Did any worker directly mutate Local Work Trajectory?
7. Which leader-owned report consumer calls, if any, turned worker
   `trajectory_update` into Local Work Trajectory changes?

Minimum acceptable artifacts:

1. scheduler snapshot and event log;
2. delivery state/log;
3. runtime invocation audit with compact timing fields;
4. output artifact store refs for each completed worker;
5. worker reports with `trajectory_update` where relevant;
6. leader-consumption result payloads for any trajectory updates;
7. a final smoke report that includes worker count, concurrent batch count,
   overlap verdict, and residual gaps.

## Non-Goals

This gate does not:

1. add a daemon or long-lived worker pool;
2. add distributed leases;
3. implement live Codex process resume;
4. broaden process-level concurrency to Qoder, opencode, generic providers, or
   the guide-worker wave executor;
5. automatically apply worker patches to the source workspace;
6. change the worker-owned report schema beyond the existing
   `trajectory_update` contract;
7. mutate agent-owned Local Work Trajectory directly from worker/runtime code.

## Acceptance Criteria

This gate may close when:

1. the smoke creates at least three scheduler tasks across at least two
   independent lanes, with one dependent fan-in task;
2. at least two lane-distinct tasks are delivered by live Codex runtime
   invocations in the same supervisor pass when concurrency is explicitly
   enabled;
3. runtime invocation audit proves overlapping active intervals for at least
   two live Codex worker invocations, or the run is clearly marked as
   inconclusive with a diagnostic that explains why overlap could not be
   attempted;
4. the final report states the exact number of worker tasks, attempted live
   Codex invocations, completed workers, failed workers, and skipped/waiting
   workers;
5. result consumption, delivery acknowledgement, scheduler writes, and exchange
   artifact writes remain serialized after runtime completion;
6. direct worker/subagent `localTrajectory` mutation is absent or explicitly
   rejected, and any trajectory write-back uses the leader-owned report
   consumer;
7. the smoke can be re-run in a documented test workspace without relying on
   manually edited generated artifacts.

## Planned Validation

The exact command may be refined during implementation, but validation should
include:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/runtime_invocation_audit.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "codex_delivery_supervisor and concurrent" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_delivery_supervisor_loop" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

For the live smoke itself, the final validation evidence should be a concrete
test-workspace run, preferably under
`C:\Users\16329\OneDrive\Desktop\tmp\dbc-test`, with durable artifacts linked
from the smoke report.

## Current Evidence Boundary

As of this gate opening, the inspected test workspace contains:

1. fake-runtime scheduler evidence with three worker tasks:
   `agent:server`, `agent:client`, and `agent:followup`;
2. scheduler event-log evidence that `server` and `client` were made running
   in the same timestamped wave while `followup` waited for both;
3. no durable live Codex process-level overlap evidence for that smoke;
4. a separate `tower-deck-builder` Local Work Trajectory with four lanes, but
   no matching scheduler/runtime audit proving live worker concurrency for that
   task.

Therefore the current state proves scheduler-level parallelism, not live Codex
process-level concurrent worker execution.

## Implementation

Implemented C9 as a narrow evidence product over the existing bounded Codex
delivery supervisor:

1. runtime helper:
   `src/runtime/orchestration/live_codex_concurrent_worker_smoke.py`;
2. exported runtime API:
   `run_live_codex_concurrent_worker_smoke()` and
   `LiveCodexConcurrentWorkerSmokeRequest`;
3. CLI:
   `doc-based-coding scheduler live-codex-concurrent-worker-smoke`;
4. C9-specific default artifact paths under:
   `.codex/scheduler/live-codex-concurrent-worker-smoke-*`,
   `.codex/runtime/live-codex-concurrent-worker-smoke-invocations.jsonl`,
   and
   `.codex/orchestration/live-codex-concurrent-worker-smoke-exchange-artifacts.json`;
5. final report:
   `.codex/scheduler/live-codex-concurrent-worker-smoke-report.json`.

The helper composes the C2 bounded loop, then reads the compact runtime
invocation audit and computes pairwise overlap from `started_at` / `ended_at`
intervals. This deliberately distinguishes scheduler batch parallelism from
audited live process overlap.

For repeatability, the C9 helper clears its own dispatcher, delivery, runtime
invocation, and exchange artifact smoke files when
`initialize_fixture=True` and `replace_existing_fixture=True`. This reset is
limited to the C9 smoke product and does not change the C2 bounded supervisor's
normal resume/retry semantics.

During live validation, the Codex CLI process wrapper was also updated for the
current Codex CLI surface: the internal `ask_for_approval` field is now passed
as a config override (`approval_policy="..."`) instead of the removed
`--ask-for-approval` CLI argument. Subprocess stdout/stderr decoding is forced
to UTF-8 with replacement to avoid Windows reader-thread decode noise in audit
runs.

## Completion Evidence

Focused validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/live_codex_concurrent_worker_smoke.py src/runtime/orchestration/codex_cli_client.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "live_codex_concurrent_worker_smoke" -q
2 passed, 344 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "live_codex_concurrent_worker_smoke" -q
3 passed, 107 deselected
```

Adjacent validation passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "live_codex_concurrent_worker_smoke or bounded_codex_delivery_supervisor_loop_runs_lane_distinct_codex_concurrently" -q
2 passed, 343 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "live_codex_concurrent_worker_smoke or codex_delivery_supervisor" -q
9 passed, 101 deselected
```

Live test workspace validation was run in:

```text
C:\Users\16329\OneDrive\Desktop\tmp\dbc-test
```

Command:

```text
E:\workspace\tool develop\vibe coding facilities\doc based coding\.venv\Scripts\python.exe -m src scheduler live-codex-concurrent-worker-smoke --replace-existing-fixture --runtime-invocation-max-attempts 1 --max-ticks 4 --max-deliveries 4 --max-runtime-failures 3 --max-concurrent-deliveries 2 --sandbox workspace-write --ask-for-approval never --cwd C:\Users\16329\OneDrive\Desktop\tmp\dbc-test
```

Durable report:

```text
C:\Users\16329\OneDrive\Desktop\tmp\dbc-test\.codex\scheduler\live-codex-concurrent-worker-smoke-report.json
```

Report summary:

```json
{
  "ok": true,
  "verdict": "passed",
  "diagnostic": "live Codex invocation overlap proven",
  "counts": {
    "worker_tasks": 3,
    "attempted_live_codex_invocations": 3,
    "completed_workers": 3,
    "failed_workers": 0,
    "skipped_or_waiting_workers": 0,
    "concurrent_batch_count": 1,
    "overlap_pair_count": 1
  }
}
```

Overlap pair:

```text
codex-smoke:worker
  2026-06-28T12:22:25.771597+00:00
  -> 2026-06-28T12:22:47.605304+00:00

codex-smoke:parallel-worker
  2026-06-28T12:22:25.772776+00:00
  -> 2026-06-28T12:23:09.114980+00:00
```

The first concurrent batch contained:

```text
codex-smoke:worker
codex-smoke:parallel-worker
```

The follow-up worker then ran after the first worker dependency completed:

```text
codex-smoke:followup
2026-06-28T12:23:09.276799+00:00
-> 2026-06-28T12:23:35.561430+00:00
```

Authority split was preserved:

1. runtime invocation audit is host-owned and compact;
2. raw transcripts were not persisted;
3. first-batch Codex worker processes overlapped;
4. result consumption, scheduler event writes, delivery acknowledgement, and
   exchange artifact writes remained serialized after runtime completion;
5. worker/runtime code did not mutate Local Work Trajectory;
6. MCP live-provider execution remains absent.

## Closure

C9 closes the live-evidence gap left by C8. The project now has a repeatable
live Codex concurrent-worker smoke that proves lane-distinct Codex worker
process overlap with durable timing evidence and successful serialized
writeback.
