# Planning Gate - ExchangeArtifact Consumption Lifecycle

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/host-ux-binding-reference-visibility-followup-direction-analysis.md`
recommends moving from Host UX readback to runtime lifecycle semantics.

The operator can now see exact-version binding readiness and latest admission
results, but stored `ExchangeArtifact` versions still do not have a concrete
runtime path for moving from available/admitted to consumed.

## Problem

Earlier slices intentionally kept consumption out of scope:

```text
inspect bundle -> read-only
admission -> scheduler snapshot + admission ledger only
Host UX -> compact readback only
```

That preserved authority boundaries while the admission path was immature, but
now operators need a durable signal that an exact artifact version has been
used intentionally.

The existing `ExchangeArtifact.lifecycle_state` already supports `consumed`, so
this slice should not invent a second lifecycle store. It should define the
smallest explicit mutation path that updates the stored exact version and can be
projected by the existing `dbc://exchange-artifacts/bundle` read model.

## Contract Decision

### Lifecycle States In Scope

This slice only makes the following state transition executable:

```text
accepted/proposed/draft -> consumed
```

The store may preserve other historical states, but this slice does not define
a full state machine for rejected, superseded, or archived artifacts.

### Mutation Authority

The ExchangeArtifact store is the authority for `artifact.lifecycle_state`.

The admission ledger remains the authority for admission attempts. Scheduler
snapshot and event log remain the authority for admitted tasks.

### Consumption Timing

Default admission must not automatically mark an artifact consumed.

Reason: admission is currently an operator action that may be retried,
duplicated explicitly, or used for dry operator workflows. Treating every
successful admission as consumption would silently change duplicate-admission
and audit semantics.

Instead, this slice adds an explicit opt-in mutation:

```text
mark_consumed_on_success=true
```

When enabled, a successful ledger-backed admission marks the exact admitted
artifact version consumed after scheduler snapshot/event-log mutation and after
the admission ledger record is written.

### Result Shape

The mutating result must expose:

```text
consumption_state
consumed
previous_lifecycle_state
current_lifecycle_state
exchange_store_mutated
consumption_actor
consumption_reason
```

Inspection bundles must continue to project `lifecycle_state` from the stored
artifact. No raw admission ledger records are duplicated into the store.

## Scope

### Slice 1 - Store Mutation Primitive

Add a narrow runtime helper that marks one exact stored artifact version
consumed by rewriting that exact version in the JSON store.

The helper should:

1. require non-empty `artifact_id` and `version`;
2. fail if the exact version is missing;
3. preserve artifact identity, version, payload parts, scope, and visibility;
4. set `lifecycle_state="consumed"`;
5. append a compact `log` part recording actor, timestamp, and reason;
6. be idempotent for already-consumed artifacts while still returning a visible
   result.

### Slice 2 - Ledger-Backed Admission Opt-In

Add optional `mark_consumed_on_success` to the shared ledger-backed admission
helper.

When false, current behavior must remain unchanged.

When true and admission succeeds:

1. write the admission ledger record;
2. mark the exact artifact version consumed;
3. return the compact consumption result;
4. report `exchange_store_mutated=true` in authority split.

Failure, duplicate rejection, and binding-ref validation failure must not mark
the store consumed.

### Slice 3 - CLI Surface

Add a CLI flag to `scheduler admit-exchange-artifact`:

```text
--mark-consumed-on-success
```

The flag should map to the shared helper only. This slice does not add a
standalone consume CLI command.

### Slice 4 - MCP Surface

Expose the same opt-in on the existing `admitExchangeArtifact` MCP tool.

This slice does not add a standalone `consumeExchangeArtifact` MCP tool.

## Non-Goals

This gate does not:

1. make admission auto-consume by default;
2. define a complete ExchangeArtifact lifecycle state machine;
3. mark input binding artifacts consumed when a scheduler submission references
   them;
4. mutate scheduler state after consumption;
5. mutate Local Work Trajectory;
6. change Host UX rendering;
7. add consumed-state filtering or disabled controls;
8. add a new store schema.

## Acceptance Criteria

The gate may close when:

1. a runtime test proves explicit store consumption changes bundle
   `lifecycle_state` to `consumed`;
2. a runtime test proves ledger-backed admission can opt in to consumption and
   returns the consumption result;
3. a runtime test proves failed admission does not consume the artifact;
4. a CLI test proves `--mark-consumed-on-success` marks the admitted exact
   version consumed;
5. an MCP test proves `markConsumedOnSuccess` routes to the shared helper;
6. help/schema text makes the opt-in semantics clear;
7. status/review docs record the default non-auto-consumption decision.

## Completion Notes

Completed on 2026-06-22.

Implemented:

1. `mark_exchange_artifact_version_consumed()` as the explicit exact-version
   store lifecycle mutation primitive;
2. order-preserving `JsonArtifactVersionStore.replace_exact()` so lifecycle
   updates do not change latest-version projection;
3. `mark_consumed_on_success` on the shared ledger-backed admission helper;
4. CLI `scheduler admit-exchange-artifact --mark-consumed-on-success`;
5. MCP `admitExchangeArtifact.markConsumedOnSuccess`;
6. focused runtime, CLI, and MCP tests for success, failure, idempotence, and
   readback.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/exchange_store.py src/runtime/orchestration/exchange_admission_ledger.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
277 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
53 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
19 passed
```

`analyze_changes` reported no impact nodes and one expected MCP
tools/server-registration coupling alert, satisfied by `src/mcp/server.py`
schema/routing updates and MCP route tests.
