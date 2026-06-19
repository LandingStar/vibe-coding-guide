# Planning Gate - Scheduler Operator Workflow Dogfood Fixture

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/scheduler-admission-host-evidence-operator-workflow-ui-followup-direction-analysis.md`
recommends adding a controlled fixture so the newly completed Scheduler
Operator panel can be validated over a real ExchangeArtifact candidate instead
of only empty-state readback and rendered HTML fixtures.

## Problem

The VS Code Scheduler Operator panel can now show admission candidates and call
explicit scheduler actions, but the default development workspace has no
ExchangeArtifact store and no scheduler-admission candidate. This makes the
visible product flow hard to dogfood:

```text
candidate -> admit -> bounded fake loop -> projection refresh -> Host Evidence readback
```

Existing tests already construct this shape manually. The missing product
facility is a small repeatable way to seed the candidate into a target
workspace using the same runtime models as production admission.

## Scope

### Slice 1 - Controlled Fixture Contract

Add a narrow helper that writes exactly one deterministic
`scheduler_task_batch_submission` ExchangeArtifact into the local durable
ExchangeArtifact store:

```text
.codex/orchestration/exchange-artifacts.json
```

The fixture should represent a small two-task dependency chain so the operator
workflow proves both candidate discovery and bounded scheduler advancement:

1. `dogfood:prepare`
2. `dogfood:verify`, depending on `dogfood:prepare`

The tasks use fake runtime only.

### Slice 2 - CLI Surface

Expose the helper as a scheduler operator command:

```text
doc-based-coding scheduler seed-dogfood-fixture
```

The command may accept explicit `--artifact-store-path`, `--artifact-id`,
`--version`, and `--replace-existing` options, but defaults should target the
standard local store and stable fixture coordinates.

### Slice 3 - Workflow Smoke

Validate the full sequence over a temporary project:

1. seed fixture;
2. read `dbc://exchange-artifacts/bundle` and observe one admission candidate;
3. admit the exact candidate through existing `scheduler admit-exchange-artifact`;
4. run a bounded fake loop through existing `scheduler daemon-loop`;
5. refresh scheduler-derived projection through existing `scheduler project`;
6. read `dbc://host-evidence/presentation` and observe scheduler-loop evidence
   when the loop is run with an evidence id.

## Non-Goals

This gate does not:

1. auto-admit the candidate;
2. auto-run scheduler tasks;
3. auto-refresh scheduler projection;
4. add live Qoder / real-provider execution;
5. create a background daemon lifecycle;
6. mark ExchangeArtifacts consumed;
7. mutate agent-owned Local Work Trajectory;
8. change scheduler/admission/evidence schemas;
9. replace existing MCP tools or CLI commands.

## Authority Boundary

The fixture is demo/test data injection only. It mutates only the local
ExchangeArtifact store because its purpose is to create an operator-visible
candidate. Scheduler state, admission ledger, scheduler event log, scheduler
projection, and Host Evidence remain changed only by their existing explicit
operator commands.

The helper must use the existing `SchedulerTaskBatchSubmission`,
`scheduler_task_batch_submission_to_artifact()`, and `JsonArtifactVersionStore`
runtime models rather than handwritten store JSON.

## Acceptance Criteria

The gate may close when:

1. A controlled fixture helper can write a deterministic
   `scheduler_task_batch_submission` ExchangeArtifact candidate.
2. `doc-based-coding scheduler seed-dogfood-fixture` creates that candidate in
   the default local ExchangeArtifact store.
3. The command reports explicit artifact id/version, candidate task ids, store
   path, and authority clues.
4. The command refuses to overwrite an existing exact fixture version unless an
   explicit replace flag is provided.
5. Focused tests cover helper behavior, CLI behavior, and the full
   seed/read/admit/run/project/readback smoke path.
6. Status docs record that the fixture mutates only the ExchangeArtifact store
   and keeps downstream actions explicit.

## Completion Notes

Implemented:

1. `src/runtime/orchestration/scheduler_operator_fixture.py` now builds a
   deterministic two-task fake-runtime `scheduler_task_batch_submission`
   ExchangeArtifact candidate.
2. `doc-based-coding scheduler seed-dogfood-fixture` writes that candidate to
   the default `.codex/orchestration/exchange-artifacts.json` store, or to an
   explicit `--artifact-store-path`.
3. The seed command reports artifact id/version, batch id, candidate task ids,
   dependency ids, store path, replace state, and authority clues.
4. Existing exact-version overwrite protection remains the default. Resetting
   the fixture requires explicit `--replace-existing`.
5. The full seed/read/admit/run/project/readback path is covered through CLI and
   runtime tests.

Validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "seed_scheduler_operator_dogfood_fixture"
2 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "seed_dogfood_fixture or scheduler_operator_workflow"
2 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_doc_loop_prompts.py -k "scheduler or exchange_artifact or host_evidence"
126 passed
```

This slice did not change the UI surface, so no new screenshot validation was
required. The exercised product path is backend/CLI fixture seeding plus the
existing operator workflow commands.
