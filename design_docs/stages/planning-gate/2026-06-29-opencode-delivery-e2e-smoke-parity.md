# Planning Gate - OpenCode Delivery E2E Smoke Parity

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

Codex had a C1 host-owned delivery smoke:
`doc-based-coding scheduler codex-delivery-e2e-smoke`. OpenCode already had the
underlying delivery-once, bounded-loop, live-concurrency, patch-review, and
status-readback parity surfaces, and a runtime helper for the same C1-style
flow existed, but it was not exposed as a public scheduler CLI surface.

That left OpenCode functionally capable at the runtime layer but not at the
same operator command level as Codex.

## Scope

Add OpenCode C1 delivery E2E smoke parity:

1. expose runtime exports for `run_opencode_delivery_e2e_smoke()` and its
   process-client wrapper;
2. add scheduler CLI:
   `doc-based-coding scheduler opencode-delivery-e2e-smoke`;
3. reuse the same dispatcher tick, delivery sync, OpenCode delivery-once,
   result consumption, recovery, retry/audit, and authority split as the Codex
   C1 smoke;
4. use OpenCode-specific host options:
   `--output-format`, `--attach-url`, `--session-id`, `--continue-session`,
   and `--fork-session`;
5. reject Codex-only `--sandbox` and `--ask-for-approval`;
6. keep default OpenCode E2E smoke state/runtime paths separate from Codex C1
   and OpenCode bounded-loop evidence paths.

## Non-Goals

This gate does not:

1. start or manage `opencode serve`;
2. implement durable long-lived OpenCode worker sessions;
3. expose live OpenCode execution through MCP;
4. apply worker patches to the source workspace;
5. rename historical `CodexDelivery...` provider-parametric product types;
6. change monitoring UI contracts.

## Implementation

Completed OpenCode delivery E2E smoke parity:

1. `src/runtime/orchestration/__init__.py` now exports
   `run_opencode_delivery_e2e_smoke()` and
   `run_opencode_delivery_e2e_smoke_with_process_client()`;
2. scheduler help and routing expose:
   `doc-based-coding scheduler opencode-delivery-e2e-smoke`;
3. the command uses OpenCode defaults:
   `.codex/scheduler/opencode-delivery-e2e-smoke-state.json`,
   `.codex/scheduler/opencode-delivery-e2e-smoke-events.jsonl`, and
   `.codex/runtime/opencode-delivery-e2e-smoke-invocations.jsonl`;
4. the command fails closed before mutation when OpenCode readiness is
   negative;
5. the CLI accepts OpenCode attach/session selectors and rejects Codex-only
   sandbox/approval flags;
6. `docs/opencode-host-provisioning-check-guide.md` documents the new surface.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_e2e_smoke or codex_delivery_e2e_smoke" -q
4 passed, 365 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_e2e_smoke or codex_delivery_e2e_smoke" -q
6 passed, 136 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_e2e_smoke or opencode_bounded or live_opencode_concurrent_worker_smoke or opencode_runtime_status or codex_delivery_e2e_smoke" -q
9 passed, 360 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_e2e_smoke or opencode_delivery_supervisor_loop or live_opencode_concurrent_worker_smoke or opencode_runtime_status or codex_delivery_e2e_smoke" -q
17 passed, 125 deselected
```

No screenshot validation is required because this gate does not implement UI.

## Remaining OpenCode Work

OpenCode now matches Codex for the current one-shot worker runtime operator
surface, including C1 delivery E2E smoke. Remaining work is beyond basic
one-shot Codex-level parity:

1. `opencode serve` / HTTP-server lifecycle contract;
2. durable long-lived OpenCode worker session policy;
3. provider-generic naming cleanup for historical `CodexDelivery...` product
   types.
