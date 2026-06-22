# Review - ExchangeArtifact Consumption Lifecycle

> Date: 2026-06-22
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-22-exchange-artifact-consumption-lifecycle.md`

## Scope Reviewed

This slice added the first executable consumption lifecycle path for exact
stored `ExchangeArtifact` versions.

Implemented:

1. `ExchangeArtifactConsumptionResult`;
2. `mark_exchange_artifact_version_consumed()`;
3. order-preserving `JsonArtifactVersionStore.replace_exact()`;
4. `mark_consumed_on_success` on
   `admit_exchange_artifact_version_with_ledger()`;
5. CLI `scheduler admit-exchange-artifact --mark-consumed-on-success`;
6. MCP `admitExchangeArtifact.markConsumedOnSuccess`;
7. focused runtime, CLI, and MCP coverage.

## Contract Outcome

Admission does not auto-consume by default.

Consumption is explicit:

```text
mark_consumed_on_success=true
```

When enabled, the shared ledger-backed admission helper first completes
scheduler snapshot/event-log mutation and admission ledger write, then marks
the exact admitted artifact version `consumed`.

Failed admission, duplicate rejection, and validation failure do not consume
the artifact.

The ExchangeArtifact store remains the authority for
`artifact.lifecycle_state`. The admission ledger remains the authority for
admission attempts. Scheduler snapshot/event log remain the authority for
admitted scheduler tasks.

## Evidence

Syntax validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/exchange_store.py src/runtime/orchestration/exchange_admission_ledger.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py
passed
```

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "mark_exchange_artifact_version_consumed or can_mark_consumed_on_success or does_not_consume_on_failure"
3 passed, 274 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "mark_consumed_on_success or admit_exchange_artifact_cli_submits_exact_single_task"
2 passed, 51 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "can_mark_consumed or exposes_and_routes_admit_exchange_artifact"
2 passed, 17 deselected
```

Wider adjacent validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "exchange_artifact_store_inspection or exchange_artifact_admission_ledger or admit_exchange_artifact_version or binding_summary or binding_consumer_fixture"
22 passed, 255 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "admit_exchange_artifact or exchange_artifacts_bundle_cli_projects_binding_summary or binding_consumer_fixture or seed_dogfood_fixture_help"
10 passed, 43 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "admit_exchange_artifact or exchange_artifacts_bundle or binding_consumer_fixture or binding_summary or binding_reference_inspect"
7 passed, 12 deselected
```

Full touched test files:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
277 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
53 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
19 passed
```

Change analysis:

```text
analyze_changes
impact.direct=[]
impact.transitive=[]
coupling.alerts=[coupling-mcp-tools-registration]
```

The coupling alert is expected for MCP tool surface changes and is satisfied by
`src/mcp/server.py` schema/routing updates plus MCP route tests.

## Behavioral Notes

The store update appends a compact `log` payload part with
`action="artifact_consumed"`, actor, timestamp, reason, and related artifact id.

Already-consumed artifacts are idempotent: the helper returns
`already_consumed=true` and does not rewrite the store.

`replace_exact()` preserves record ordering, so consuming an older exact
version does not accidentally make it the latest version in inspection bundle
projection.

## Explicit Non-Goals Preserved

This slice did not:

1. make admission auto-consume by default;
2. define a complete ExchangeArtifact lifecycle state machine;
3. mark referenced input binding artifacts consumed;
4. mutate scheduler state after consumption;
5. mutate Local Work Trajectory from runtime/CLI/MCP surfaces;
6. change Host UX rendering;
7. add consumed-state filtering or disabled controls;
8. add a new store schema.

## Follow-Up

The next useful step should be operator-flow productization over the new
runtime fact:

1. project consumed state into Scheduler Operator Host UX candidate affordances;
2. decide whether consumed exact versions should be hidden, disabled, or shown
   as historical records;
3. decide whether an explicit standalone consume command/tool is needed after
   dogfood reveals non-admission consumption cases.
