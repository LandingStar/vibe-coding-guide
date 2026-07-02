# Planning Gate - OpenCode Bounded Supervisor Loop Parity

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode now has delivery-supervisor-once parity with Codex. The next gap is
the bounded supervisor loop: Codex can repeatedly recover scheduler state, mark
newly-ready tasks, dispatch leader-worker delivery records, run provider
delivery with result consumption, and stop through bounded criteria.

## Scope

Add OpenCode bounded supervisor loop parity:

1. add a host-owned runtime entry point for OpenCode bounded delivery loops;
2. reuse the same dispatcher, delivery sync, ready marking, result
   consumption, retry, concurrency, and serialized writeback semantics used by
   Codex;
3. make the loop provider-parametric without duplicating the full Codex loop;
4. keep OpenCode fixture tasks under `runtime_provider="opencode"`;
5. expose scheduler CLI:
   `doc-based-coding scheduler opencode-delivery-supervisor-loop`;
6. use OpenCode-specific host options and reject Codex-only sandbox/approval
   options;
7. document the loop path and remaining live-concurrency evidence gap.

## Non-Goals

This gate does not:

1. prove live OpenCode process overlap;
2. start or manage `opencode serve`;
3. implement long-lived OpenCode worker sessions;
4. expose live provider execution through MCP;
5. rename historical `CodexDelivery...` product types;
6. apply worker edits to the source workspace automatically.

## Acceptance Criteria

This gate may close when:

1. runtime tests prove an OpenCode bounded loop completes a simple chain;
2. runtime tests prove an OpenCode multi-lane fixture can run lane-distinct
   deliveries concurrently through the shared delivery supervisor;
3. scheduler help lists `opencode-delivery-supervisor-loop`;
4. CLI help documents the bounded loop boundary and OpenCode-specific options;
5. missing OpenCode CLI fails closed before fixture/scheduler/delivery state
   mutation;
6. invalid concurrency is rejected;
7. focused Codex and OpenCode loop tests pass after provider parameterization;
8. docs/checklist identify loop parity as completed and live concurrency smoke
   as remaining work.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_bounded or bounded_codex_delivery_supervisor_loop" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_supervisor_loop or codex_delivery_supervisor_loop" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

No screenshot validation is required because this gate does not implement UI.

## Implementation

Completed the OpenCode bounded supervisor loop parity slice:

1. parameterized the existing bounded delivery loop over
   `runtime_provider="codex" | "opencode"` while keeping the existing Codex
   public entry point compatible;
2. added `run_bounded_opencode_delivery_supervisor_loop()` and a process-client
   wrapper;
3. updated fixture generation so OpenCode loop fixtures create
   `runtime_provider="opencode"` worker tasks and `:opencode-result` output
   artifacts;
4. preserved shared dispatcher, delivery sync, ready marking, result
   consumption, retry, max-delivery, max-runtime-failure, lane-distinct
   concurrency, and serialized writeback semantics;
5. added scheduler CLI:
   `doc-based-coding scheduler opencode-delivery-supervisor-loop`;
6. exposed OpenCode-specific host options and rejected Codex-only sandbox /
   approval / patch-publication flags;
7. updated the OpenCode host provisioning guide.

Historical `CodexDelivery...` product type names remain in use as
provider-parametric delivery products. Renaming is still deferred to a later
cleanup gate.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_bounded or bounded_codex_delivery_supervisor_loop" -q
7 passed, 354 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_supervisor_loop or codex_delivery_supervisor_loop" -q
7 passed, 120 deselected

.\.venv\Scripts\python.exe -m src scheduler opencode-delivery-supervisor-loop --help
listed OpenCode loop usage and boundary text

.\.venv\Scripts\python.exe -m src scheduler --help
listed opencode-delivery-supervisor-loop
```

## Remaining Parity Gap

OpenCode now has delivery-once and bounded supervisor loop parity. It still
does not have a live OpenCode concurrent worker smoke proving real OpenCode
process overlap, `opencode serve` integration, long-lived worker sessions, or
provider-generic naming cleanup.
