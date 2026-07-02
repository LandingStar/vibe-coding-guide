# Planning Gate - Server/API-Created Session Promotion API

Date: 2026-06-30

Status: COMPLETED

## Purpose

This gate defines Continuous Worker Ownership Slice E. The slice adds an
explicit host-owned promotion API for turning one OpenCode
`server_api_created` session result into a durable continuous worker binding.

The focus is the promotion API itself. Delivery supervisor integration,
doctor/self-check diagnostics, private storage allocation, compact execution,
and monitoring UI are intentionally left for later slices.

## Source Context

- `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-session-ledger-binding-alignment.md`
- `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-stage-live-smoke-closure.md`
- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-schema-alignment.md`
- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-lane-ownership-tooling.md`
- `docs/opencode-host-provisioning-check-guide.md`
- `src/runtime/orchestration/opencode_server_api_client.py`
- `src/runtime/orchestration/continuous_worker_binding.py`

## Goal

Provide a deterministic data-layer API that accepts a credential-safe
server/API-created OpenCode session summary plus explicit host ownership scope
and creates a provider-neutral continuous worker binding carrying an OpenCode
session selector.

The API must make the authority boundary visible:

```text
server/API delivery creates a session result
-> host/leader explicitly chooses scope, worker id, and policy
-> promotion API claims a continuous worker binding
```

There must be no silent delivery-time persistence.

## Scope

Implement a narrow runtime helper, likely in
`src/runtime/orchestration/continuous_worker_binding.py` or a small adjacent
module, with request/result dataclasses such as:

- `ServerApiCreatedSessionPromotionRequest`
- `ServerApiCreatedSessionPromotionResult`

The request should require:

- source provider: `opencode`;
- source selector/source marker equivalent to `server_api_created`;
- `attach_url`;
- `session_id`;
- `scope_kind`;
- `scope_id`;
- `worker_id`;
- lane metadata when scope is `lane` or `lane_group`;
- explicit timestamp/reason/audit refs where available;
- target continuous worker binding ledger path and event log path.

The helper should:

1. validate that the source session is a promotable `server_api_created`
   OpenCode session;
2. reject missing scope, worker id, attach URL, or session id;
3. reject raw transcript or secret-like payloads;
4. call the existing continuous worker binding claim path rather than
   duplicating binding semantics;
5. persist a durable binding with `active_session_selector.provider=opencode`;
6. preserve promotion provenance in metadata/audit refs without storing raw
   transcript or secret values;
7. return clear result metadata showing:
   - `promotion_source=server_api_created`;
   - `provider=opencode`;
   - `binding_claimed=true|false`;
   - `delivery_state_mutated=false`;
   - `provider_executed=false`;
   - `local_work_trajectory_mutated=false`;
8. produce compact audit evidence through the existing binding event log.

## Non-Goals

This slice must not:

1. run OpenCode, Codex, Qoder, or any provider;
2. create a server/API session;
3. start, stop, restart, supervise, or health-monitor `opencode serve`;
4. automatically persist sessions during delivery;
5. wire promotion into delivery supervisor execution;
6. add doctor/self-check diagnostics;
7. add MCP or CLI unless the runtime helper is complete and the exposure is
   explicitly kept as a tiny wrapper;
8. create private storage directories or agent homes;
9. implement compact or `llm-auto`;
10. modify monitoring UI;
11. mutate Local Work Trajectory from runtime code.

## Acceptance Criteria

1. A valid `server_api_created` OpenCode session promotion creates a continuous
   worker binding with an OpenCode session selector.
2. The created binding round-trips through the durable binding ledger.
3. The binding event log includes compact promotion evidence without raw
   transcript or secret values.
4. Non-`server_api_created` selector sources are rejected with an actionable
   error.
5. Missing `attach_url`, missing `session_id`, missing `scope_id`, or missing
   `worker_id` are rejected.
6. Scope rules are preserved:
   - `lane` promotion records the lane id;
   - `lane_group` promotion requires at least one lane id;
   - conflicting active bindings follow the existing claim behavior.
7. Promotion does not create or mutate the older OpenCode session ledger.
8. Promotion does not mutate scheduler state, delivery state, runtime
   invocation logs, provider state, or Local Work Trajectory.
9. Focused tests cover success, durable readback, event log evidence, invalid
   source rejection, required-field rejection, secret/raw-transcript rejection,
   and no OpenCode session ledger mutation.
10. `py_compile`, focused tests, and `git diff --check` pass for touched files.

## Expected Tests

Add focused tests in `tests/test_runtime_orchestration.py` for:

- successful server/API-created session promotion to lane binding;
- successful lane-group promotion with preserved lane ids;
- rejection for `session_selector_source=explicit_config`;
- rejection for `session_selector_source=session_ledger`;
- rejection for missing attach URL/session id/scope id/worker id;
- rejection for secret/raw transcript-like metadata;
- no OpenCode session ledger file is created or modified;
- binding event log includes a compact `binding_claimed` event with promotion
  provenance.

## Later Slices

After this API is stable, later slices may separately add:

1. delivery supervisor readback or explicit operator command for promotion;
2. CLI/MCP wrappers;
3. doctor/self-check validation for promotable session artifacts;
4. private worker storage allocation;
5. continuous same-worker compact policy;
6. monitoring UI readback.

## Completion Notes

Implemented on 2026-06-30.

Runtime surface added:

- `ServerApiCreatedSessionPromotionRequest`
- `ServerApiCreatedSessionPromotionResult`
- `promote_server_api_created_session_to_continuous_worker_binding()`

The helper validates an explicit OpenCode `server_api_created` selector,
requires attach URL, session id, worker id, scope id, and lane ids for
lane-group scope, then delegates to `claim_continuous_worker_binding()` so the
existing binding ledger and event log semantics remain authoritative.

Behavior:

- Promoted bindings use
  `active_session_selector.provider=opencode`.
- Promotion provenance is stored as compact metadata:
  `promotion_source=server_api_created`,
  `session_selector_source=server_api_created`, and
  `promotion_authority=explicit_host_owned_claim`.
- The older OpenCode session ledger is not created or mutated.
- The helper does not run a provider, create a server/API session, mutate
  scheduler state, mutate delivery state, write runtime invocation logs, or
  mutate Local Work Trajectory.
- Raw transcript and secret-like metadata are rejected through the existing
  continuous worker validation guard.

Validation passed:

```text
python -m pytest tests/test_runtime_orchestration.py -k "server_api_created_session_promotion" -q
12 passed, 435 deselected

python -m pytest tests/test_runtime_orchestration.py -k "server_api_created_session_promotion or continuous_worker_binding or lane_ownership" -q
25 passed, 422 deselected

python -m py_compile src/runtime/orchestration/continuous_worker_binding.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py

git diff --check -- src/runtime/orchestration/continuous_worker_binding.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py "design_docs/Project Master Checklist.md" design_docs/stages/planning-gate/2026-06-30-server-api-created-session-promotion-api.md .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` only reported Windows LF/CRLF warnings for already-edited
files.
