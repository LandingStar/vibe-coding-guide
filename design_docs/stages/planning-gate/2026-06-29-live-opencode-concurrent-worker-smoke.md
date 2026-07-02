# Planning Gate - Live OpenCode Concurrent Worker Smoke

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode now has runtime-provider adapter, guide-worker smoke, mixed
Codex+OpenCode smoke, delivery-supervisor-once parity, and bounded supervisor
loop parity. The remaining Codex-level evidence gap is live process overlap:
Codex has a repeatable C9 smoke proving two lane-distinct CLI worker
invocations were active at the same time, while OpenCode only had bounded-loop
tests proving the shared scheduler semantics.

## Scope

Add the matching OpenCode live concurrency evidence slice:

1. reuse the bounded OpenCode supervisor loop and compact runtime invocation
   audit;
2. add a host-owned runtime entry point:
   `run_live_opencode_concurrent_worker_smoke()`;
3. add a scheduler CLI:
   `doc-based-coding scheduler live-opencode-concurrent-worker-smoke`;
4. seed a default multi-lane OpenCode fixture with at least two independent
   lane-distinct workers and one dependent follow-up worker;
5. compute overlap from audited `started_at` / `ended_at` intervals, not from
   scheduler batch metadata alone;
6. keep OpenCode host options explicit and reject Codex-only sandbox/approval
   options;
7. write a durable compact report under
   `.codex/scheduler/live-opencode-concurrent-worker-smoke-report.json`.

## Non-Goals

This gate does not:

1. start or manage `opencode serve`;
2. implement long-lived OpenCode worker sessions;
3. expose live provider execution through MCP;
4. apply worker edits to the source workspace automatically;
5. rename historical `CodexDelivery...` product types;
6. change monitoring UI contracts.

## Acceptance Criteria

This gate may close when:

1. runtime tests prove the OpenCode live smoke can produce an overlap-positive
   report from compact audit records;
2. CLI help lists the live OpenCode smoke boundary and OpenCode-specific host
   options;
3. missing OpenCode CLI fails closed before fixture/scheduler/delivery/runtime
   mutation while still writing an inconclusive report;
4. `--max-concurrent-deliveries 1` is rejected for the live smoke;
5. adjacent Codex live smoke tests still pass;
6. docs/checklist identify live OpenCode concurrency evidence as completed and
   leave `opencode serve`, long-lived sessions, and provider-generic naming as
   future work.

## Implementation

Completed the live OpenCode concurrent worker smoke slice:

1. generalized the existing live Codex smoke report over
   `runtime_provider="codex" | "opencode"`;
2. preserved the existing Codex C9 public API and CLI behavior;
3. added `LiveOpenCodeConcurrentWorkerSmokeRequest`,
   `LiveOpenCodeConcurrentWorkerSmokeResult`, and
   `run_live_opencode_concurrent_worker_smoke()`;
4. added CLI command:
   `doc-based-coding scheduler live-opencode-concurrent-worker-smoke`;
5. added OpenCode-specific default smoke paths under:
   `.codex/scheduler/live-opencode-concurrent-worker-smoke-*`,
   `.codex/runtime/live-opencode-concurrent-worker-smoke-invocations.jsonl`,
   and
   `.codex/orchestration/live-opencode-concurrent-worker-smoke-exchange-artifacts.json`;
6. kept OpenCode live smoke on `opencode run` one-shot execution and explicit
   `--output-format text|json` host options;
7. tightened the live-smoke success criteria so overlap alone is not enough:
   the bounded loop must be `ok`, three OpenCode workers must complete, and
   failed worker count must be zero;
8. resolved the host CLI executable before spawning the process, which makes
   Windows `.CMD` launcher paths usable after readiness succeeds;
9. kept MCP live-provider execution closed and Local Work Trajectory mutation
   false.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/live_codex_concurrent_worker_smoke.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "live_opencode_concurrent_worker_smoke or live_codex_concurrent_worker_smoke" -q
4 passed, 359 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "live_opencode_concurrent_worker_smoke or live_codex_concurrent_worker_smoke" -q
6 passed, 124 deselected
```

Live host validation also passed in a temporary project workspace:

```text
.\.venv\Scripts\python.exe -m src opencode readiness
ready=true
executable_resolved=C:\Users\16329\AppData\Roaming\npm\opencode.CMD

.\.venv\Scripts\python.exe -m src scheduler live-opencode-concurrent-worker-smoke \
  --replace-existing-fixture \
  --runtime-invocation-max-attempts 1 \
  --max-ticks 4 \
  --max-deliveries 4 \
  --max-runtime-failures 3 \
  --max-concurrent-deliveries 2 \
  --cwd <temp-project> \
  --snapshot-path <temp-project>\.codex\scheduler\live-opencode-concurrent-worker-smoke-state.json \
  --event-log-path <temp-project>\.codex\scheduler\live-opencode-concurrent-worker-smoke-events.jsonl \
  --artifact-store-path <temp-project>\.codex\orchestration\live-opencode-concurrent-worker-smoke-exchange-artifacts.json \
  --dispatcher-state-path <temp-project>\.codex\scheduler\live-opencode-concurrent-worker-smoke-dispatcher-state.json \
  --dispatch-event-log-path <temp-project>\.codex\scheduler\live-opencode-concurrent-worker-smoke-dispatcher-events.jsonl \
  --delivery-state-path <temp-project>\.codex\scheduler\live-opencode-concurrent-worker-smoke-delivery-state.json \
  --delivery-event-log-path <temp-project>\.codex\scheduler\live-opencode-concurrent-worker-smoke-delivery-events.jsonl \
  --runtime-invocation-log-path <temp-project>\.codex\runtime\live-opencode-concurrent-worker-smoke-invocations.jsonl \
  --report-path <temp-project>\.codex\scheduler\live-opencode-concurrent-worker-smoke-report.json
```

Live report summary:

```json
{
  "ok": true,
  "runtime_provider": "opencode",
  "verdict": "passed",
  "counts": {
    "worker_tasks": 3,
    "attempted_live_provider_invocations": 3,
    "attempted_live_opencode_invocations": 3,
    "completed_workers": 3,
    "failed_workers": 0,
    "skipped_or_waiting_workers": 0,
    "concurrent_batch_count": 1,
    "overlap_pair_count": 1
  }
}
```

First overlapping pair:

```text
opencode-smoke:worker
2026-06-28T18:42:49.356651+00:00
-> 2026-06-28T18:43:08.285904+00:00

opencode-smoke:parallel-worker
2026-06-28T18:42:49.356651+00:00
-> 2026-06-28T18:43:17.260166+00:00
```

No screenshot validation is required because this gate does not implement UI.

## Remaining Parity Gap

OpenCode now has Codex-level one-shot provider adapter, guide-worker smoke,
mixed provider smoke, delivery-once, bounded supervisor loop, and live
concurrent worker smoke evidence. Remaining OpenCode work is no longer basic
Codex-level parity: `opencode serve`, long-lived worker sessions, and
provider-generic naming cleanup remain separate future gates.
