# Planning Gate - Continuous Worker Session Policy

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode now has host-owned attach/session selection, a durable OpenCode
session ledger, delivery-time lookup, stale recovery, and provider-generic
delivery naming. The next requested capability is stronger than selecting a
session for one task: the same worker should be able to continue across
successive nodes in one lane, or across a configured lane group, while the
project scheduler remains the source of truth.

## Scope

Implement the first provider-neutral continuous worker binding slice:

1. define a durable `ContinuousWorkerBinding` ledger;
2. support lane, lane-group, agent, and task scopes;
3. keep OpenCode as the first runtime provider that can consume the binding;
4. resolve active bindings by task, then agent, then lane;
5. allow lane-group bindings to cover multiple lanes;
6. expose compact lifecycle data: worker id, provider, scope, lane ids,
   lifecycle status, lease timestamps, compact context ref, and audit refs;
7. make OpenCode delivery automatically convert a matched continuous worker
   binding into an OpenCode host session selector;
8. prevent a concurrent delivery batch from selecting two tasks that resolve to
   the same continuous worker binding;
9. keep Local Work Trajectory, scheduler state, patch merge, and worker report
   ownership boundaries unchanged.

## Non-Goals

This gate does not:

1. start, stop, restart, or supervise `opencode serve`;
2. create OpenCode sessions automatically;
3. call OpenCode's HTTP API directly;
4. implement the final direct OpenCode server/API adapter;
5. give OpenCode scheduler, leader, Local Work Trajectory, or merge authority;
6. store raw transcripts or secret values;
7. make Codex emulate OpenCode server/session continuity.

## Completion Target

This gate is complete when:

1. lane-scope OpenCode continuous worker bindings can be claimed, inspected,
   released, and excluded after release or stale expiry;
2. same-lane consecutive OpenCode tasks reuse the same host session selector
   through the continuous worker binding lookup;
3. task binding beats agent binding, and agent binding beats lane binding;
4. lane-group bindings can match member lanes;
5. concurrent OpenCode delivery does not dispatch two tasks that resolve to the
   same continuous worker binding in the same batch;
6. compact audit metadata identifies selector source, binding id, scope, worker
   id, lane ids, compact context ref, and audit refs;
7. worker trajectory ownership remains report-only for workers;
8. docs explain the provider-neutral binding contract and the OpenCode-specific
   selector implementation boundary.

## Implementation

Completed the first continuous worker session policy slice:

1. added provider-neutral durable ledger module
   `src/runtime/orchestration/continuous_worker_binding.py`;
2. added schema `continuous-worker-binding-ledger.v1` and compact JSONL event
   log schema `continuous-worker-binding-event-log.v1`;
3. added claim, release, inspect, recover-stale, and delivery-time resolve
   helpers;
4. added delivery reuse, fork, compact context, and archive/stale lifecycle
   helpers without provider execution;
5. added
   `doc-based-coding worker-binding claim|reuse|fork|compact|release|inspect|recover-stale`;
6. extended `OpenCodeCliAgentRuntimeAdapter` so OpenCode host session selection
   checks continuous worker bindings before the older OpenCode session ledger;
7. extended delivery runtime audit metadata with selector source, continuous
   worker binding id, worker id, scope, lane ids, compact context ref, and
   audit refs;
8. extended OpenCode delivery supervisor batch selection so concurrent batches
   do not include two tasks that resolve to the same continuous worker binding;
9. OpenCode delivery now records `binding_reused` on successful binding-backed
   delivery and marks binding-backed retryable/process failures `stale`;
10. delivery-time lookup now excludes expired bindings even before explicit
   `recover-stale`;
11. added provider-neutral compact context bundle creation under
   `.codex/runtime/continuous-worker-contexts/`; the bundle records summaries,
   decisions, current state, artifact refs, mailbox cursor, worker report refs,
   and audit refs without raw transcripts or secrets;
12. exposed CLI flags `--worker-binding-ledger-path`,
   `--worker-binding-event-log-path`, and
   `--no-worker-binding-lookup` on OpenCode delivery surfaces;
13. documented the provider-neutral binding layer and OpenCode-specific selector
   fallback in `docs/opencode-host-provisioning-check-guide.md`.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/continuous_worker_binding.py src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/runtime_wiring.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "continuous_worker_binding or opencode_delivery_supervisor_uses_continuous_worker_binding or worker_binding_blocks_same_session" -q
4 passed, 384 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "worker_binding or opencode_delivery_supervisor_help" -q
3 passed, 152 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_session or opencode_delivery_supervisor or opencode_delivery_e2e_smoke or bounded_opencode_delivery_supervisor_loop or provider_generic_delivery_naming or continuous_worker_binding" -q
17 passed, 371 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_session or worker_binding or opencode_delivery_supervisor or opencode_delivery_e2e_smoke or opencode_delivery_supervisor_loop or live_opencode" -q
25 passed, 130 deselected
```

Additional lifecycle validation passed after the extension:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/continuous_worker_binding.py src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/opencode_cli_client.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "continuous_worker_binding or opencode_delivery_supervisor_uses_continuous_worker_binding or worker_binding_blocks_same_session or opencode_bounded_loop_reuses_same_continuous_worker or marks_continuous_worker_binding_stale" -q
7 passed, 384 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "worker_binding or opencode_delivery_supervisor_help or opencode_delivery_e2e_smoke_help or opencode_delivery_supervisor_loop_help" -q
7 passed, 150 deselected
```

No screenshot validation is required because this gate does not implement UI.

## Remaining Work

This gate deliberately stops before the direct OpenCode server/API adapter.
Future slices should cover:

1. direct server/API adapter after session lifecycle semantics stabilize;
2. richer monitoring UI readback for continuous worker bindings;
3. optional lane-group assignment policy surfaced from the scheduler planner;
4. explicit compact context bundle creation and retention policy beyond storing
   compact refs on the binding ledger.
