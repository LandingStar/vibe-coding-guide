# Planning Gate - Codex Concurrent Delivery Gate

> Date: 2026-06-28
> Status: COMPLETED

## Trigger

The completed multi-lane Codex fixture proves lane-aware scheduler progress but
explicitly keeps execution serial inside the bounded supervisor loop. The next
runtime gap is true process-level concurrency for independent lane-distinct
Codex worker delivery.

## Scope

Add a bounded, host-owned concurrent delivery gate over the existing Codex
delivery supervisor:

1. allow the bounded supervisor loop to select more than one eligible Codex
   delivery record per tick when records are lane-distinct;
2. run the Codex runtime invocation phase concurrently up to an explicit
   `max_concurrent_deliveries` limit;
3. keep delivery acknowledgement, result consumption, permission review
   publication, worker patch review publication, scheduler event-log writes,
   and exchange-store writes serialized after runtime completion;
4. expose JSON readback that distinguishes scheduling parallelism,
   process-level concurrent runtime execution, and serialized writeback;
5. keep the default behavior serial unless concurrency is explicitly enabled;
6. prove the behavior through a fake-client concurrent fixture and CLI parsing
   tests without requiring live Codex CLI.

## Non-Goals

This gate does not:

1. start a daemon or long-lived worker pool;
2. run multiple tasks from the same lane in the same concurrent batch;
3. make scheduler snapshot, scheduler event log, delivery state, delivery log,
   or exchange artifact writes concurrent;
4. auto-resolve merge gates or writeback conflicts;
5. resume a live Codex process mid-run;
6. mutate agent-owned Local Work Trajectory from runtime code.

## Acceptance Criteria

This gate may close when:

1. `CodexDeliverySupervisorRequest` and bounded loop request expose an explicit
   concurrency limit with serial defaults;
2. one supervisor pass can execute at least two independent lane-distinct Codex
   delivery records concurrently when the limit is greater than one;
3. the same pass never includes two records from the same lane in one
   concurrent runtime batch;
4. runtime invocation audit remains durable and redacted for every concurrent
   invocation;
5. result consumption and delivery acknowledgement still happen after runtime
   completion through the existing serialized write path;
6. loop / CLI JSON includes concurrency metadata such as requested limit,
   effective batch size, process-level parallelism flag, and serialized
   writeback flag;
7. focused runtime and CLI tests prove both serial default and explicit
   concurrent behavior.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "codex_delivery_supervisor and concurrent" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_delivery_supervisor_loop" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

## Implementation Summary

Completed on 2026-06-28.

Implemented a bounded process-level concurrency gate for Codex delivery:

1. `CodexDeliverySupervisorRequest` and
   `CodexDeliveryBoundedLoopRequest` now expose
   `max_concurrent_deliveries` with a serial default of `1`.
2. `run_codex_delivery_supervisor_once()` prepares at most one eligible
   delivery record per lane for a concurrent runtime batch, preserving
   same-lane records as pending work for later ticks.
3. The runtime invocation phase can run through a `ThreadPoolExecutor` when
   the explicit limit is greater than one and the selected batch has more than
   one lane-distinct Codex delivery.
4. Result consumption, permission review publication, worker patch review
   publication, scheduler event-log writes, exchange-store writes, and delivery
   acknowledgement remain serialized after runtime completion.
5. `CodexCliAgentRuntimeAdapter` now guards Codex session/run counters and
   session lookup with a lock so the adapter can be used by the concurrent
   delivery batch.
6. Supervisor and bounded-loop JSON now distinguish requested concurrency,
   observed batch size, process-level runtime parallelism, and serialized
   writeback.
7. CLI help, parsing, validation, and bounded-loop request wiring expose
   `--max-concurrent-deliveries`.

## Validation Evidence

Validated on 2026-06-28:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/runtime_adapter.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "codex_delivery_supervisor and concurrent" -q
2 passed, 338 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "codex_delivery_supervisor" -q
16 passed, 324 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_delivery_supervisor" -q
6 passed, 99 deselected
```

The focused runtime fixture uses a barrier-backed fake Codex client to prove
that the first two lane-distinct Codex calls overlap in the runtime invocation
phase. Adjacent regression tests prove the serial default remains serial, same
lane ready records are not included in the same concurrent runtime batch, and
CLI help / validation expose the opt-in concurrency limit.

## Residual Risk After Close

This gate proves bounded process-level concurrency for independent
lane-distinct Codex delivery records through fake-client validation. It still
does not prove always-on daemon scheduling, distributed leases, live Codex
session resume, safe automatic merge of worker edits, or live Codex CLI
throughput behavior under real provider latency.
