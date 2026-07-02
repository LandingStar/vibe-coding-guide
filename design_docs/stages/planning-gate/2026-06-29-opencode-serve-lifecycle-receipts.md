# Planning Gate - OpenCode Serve Lifecycle Receipts

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode now has delivery execution, bounded loop, live concurrency evidence,
status readback, attach/session bridge, durable session ledger, delivery-time
session lookup, and stale session recovery. The remaining OpenCode-specific
gap is `opencode serve` lifecycle handling.

The project already has a credential-safe readiness check, but no durable
receipt product for host-owned serve start/stop decisions. That makes
OpenCode session reuse harder to audit: a later agent can see a session
binding, but not the host lifecycle decision that made the attach target
available or unavailable.

## Scope

Add the smallest host-owned serve lifecycle receipt layer:

1. define an append-only OpenCode serve lifecycle ledger;
2. record host-owned lifecycle actions such as `start`, `stop`, `restart`,
   `status`, or `external`;
3. expose a CLI surface:
   `doc-based-coding opencode serve-lifecycle record|inspect`;
4. include attach URL, command preview, pid/process refs when known, timestamp,
   status, reason, and metadata-safe notes;
5. preserve authority split in every result;
6. do not start, stop, restart, supervise, or health-monitor `opencode serve`
   in this gate.

## Non-Goals

This gate does not:

1. spawn an `opencode serve` process;
2. terminate a server process;
3. implement a daemon or heartbeat;
4. call OpenCode's HTTP task API directly;
5. create or delete OpenCode sessions;
6. run providers;
7. mutate scheduler, delivery, runtime invocation, or Local Work Trajectory
   state;
8. persist raw transcript or secret values;
9. rename historical provider-parametric `CodexDelivery...` product types.

## Acceptance Criteria

This gate may close when:

1. runtime tests prove lifecycle receipts append to a durable ledger and can
   be inspected without mutation;
2. CLI help documents that the surface records host-owned lifecycle receipts
   and does not manage `opencode serve`;
3. CLI record/inspect roundtrip writes under the project-local `.codex`
   runtime directory by default;
4. receipt JSON includes authority split showing no provider execution,
   scheduler mutation, delivery mutation, runtime invocation mutation, Local
   Work Trajectory mutation, raw transcript persistence, or secret
   persistence;
5. `docs/opencode-host-provisioning-check-guide.md` documents the receipt
   workflow;
6. the compact checklist identifies this slice and leaves direct server/API
   adapter plus provider-generic naming cleanup as remaining work.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/opencode_serve_lifecycle.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_serve_lifecycle or opencode_serve_readiness" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_serve_lifecycle or opencode_serve_readiness" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

No screenshot validation is required because this gate does not implement UI.

## Implementation

Completed the host-owned OpenCode serve lifecycle receipt slice:

1. added an append-only lifecycle ledger schema:
   `opencode-serve-lifecycle-ledger.v1`;
2. added runtime models:
   `OpenCodeServeLifecycleReceipt`,
   `OpenCodeServeLifecycleLedger`,
   `OpenCodeServeLifecycleRecordRequest`,
   `OpenCodeServeLifecycleInspectRequest`, and
   `OpenCodeServeLifecycleLedgerResult`;
3. added runtime helpers:
   `record_opencode_serve_lifecycle_receipt()`,
   `inspect_opencode_serve_lifecycle_receipts()`,
   `read_opencode_serve_lifecycle_ledger()`, and
   `write_opencode_serve_lifecycle_ledger()`;
4. added CLI:
   `doc-based-coding opencode serve-lifecycle record|inspect`;
5. documented the operator workflow in
   `docs/opencode-host-provisioning-check-guide.md`;
6. preserved the boundary that this gate records host lifecycle facts but does
   not start, stop, restart, supervise, health-monitor, or call OpenCode's
   server API.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/opencode_serve_lifecycle.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_serve_lifecycle or opencode_serve_readiness" -q
5 passed, 378 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_serve_lifecycle or opencode_serve_readiness" -q
6 passed, 147 deselected

.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
Validation passed
```

## Remaining OpenCode Work

OpenCode now has readiness, attach/session selection, durable session binding,
delivery-time lookup, stale binding recovery, and serve lifecycle receipts.
Remaining work is:

1. direct OpenCode server/API adapter, only after lifecycle semantics are
   accepted and stable;
2. provider-generic naming cleanup for historical `CodexDelivery...` product
   types.
