# Planning Gate - Scheduler Operator Unified Workflow Surface

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/scheduler-operator-workflow-dogfood-fixture-followup-direction-analysis.md`
recommends lifting the now-proven operator sequence into a shared
host-neutral workflow surface.

The completed dogfood fixture proved this sequence:

```text
seed -> resources read -> admit -> inspect -> daemon-loop fake -> project -> host-evidence presentation
```

The remaining product problem is that each host currently has to re-compose
the same low-level commands or MCP calls.

## Problem

The scheduler operator path has stable pieces:

1. `dbc://exchange-artifacts/bundle` inspects scheduler-admission candidates.
2. `admitExchangeArtifact` / `scheduler admit-exchange-artifact` admits one
   exact stored artifact version.
3. `scheduler daemon-loop` runs a bounded fake-runtime loop and can write
   durable scheduler-loop evidence.
4. `scheduler project` refreshes the read-only scheduler-derived Local Work
   Trajectory projection.
5. `dbc://host-evidence/presentation` reads the operator-facing evidence view.

Those pieces are correct but awkward for Codex MCP and Host UX layers because
the host must know the whole choreography. The next surface should package the
operator workflow as a structured request/result while preserving explicit
mutation choices and step-level failure isolation.

## Scope

### Slice 1 - Contract

Define a host-neutral workflow request/result contract for:

```text
inspect candidates
optionally admit one exact candidate
optionally run bounded fake scheduler loop with evidence id
optionally refresh scheduler projection
read Host Evidence presentation
```

The request must make mutating steps explicit:

- `admit`: default `false`;
- `runLoop`: default `false`;
- `refreshProjection`: default `false`;
- `runtimeProvider`: default and only supported value `fake`;
- exact `artifactId` and `version` are required when `admit=true`;
- scheduler paths may default to the standard local scheduler paths, but the
  result must report the resolved paths.

The result must include:

- overall `ok`;
- ordered `steps[]` with name/status/mutated/error/result fields;
- compact `paths`;
- `authority_split`;
- candidate summary before mutation;
- optional admission result;
- optional loop result;
- optional projection result;
- Host Evidence presentation readback.

### Slice 2 - Backend Helper

Implement the workflow outside core orchestration runtime, near the existing
operator/progress graph composition layer, so runtime models stay host-neutral
and do not depend on UI/progress graph readback code.

The helper should reuse existing durable APIs rather than shelling out to the
CLI:

- ExchangeArtifact store inspection;
- exact-version admission with ledger;
- bounded fake scheduler daemon loop;
- scheduler-loop evidence writer;
- scheduler-derived trajectory projection writer;
- Host Evidence presentation builder.

### Slice 3 - MCP / CLI Surface

Expose the helper through:

1. `GovernanceTools.scheduler_operator_workflow(...)`;
2. MCP tool `schedulerOperatorWorkflow`;
3. CLI command `doc-based-coding scheduler operator-workflow`.

The MCP and CLI surfaces must share the helper contract and keep existing
lower-level tools intact.

### Slice 4 - Validation

Add focused tests for:

1. read-only workflow inspection with no mutation;
2. full dogfood flow over a seeded candidate;
3. duplicate admission failure isolated to the admission step before loop or
   projection steps run;
4. MCP exposure and routing;
5. CLI command behavior.

## Non-Goals

This gate does not:

1. run live Qoder or other real providers;
2. add background daemon lifecycle management;
3. auto-admit candidates by default;
4. auto-run scheduler tasks by default;
5. mark ExchangeArtifacts consumed;
6. mutate agent-owned Local Work Trajectory;
7. replace lower-level MCP tools or CLI commands;
8. change scheduler task, admission ledger, Host Evidence, or trajectory
   schemas;
9. bind or redesign VS Code UI.

## Authority Boundary

This workflow is an operator convenience surface, not a new scheduler authority.

Mutation authority remains explicit and step-scoped:

- ExchangeArtifact store readback is inspection only.
- Admission mutates scheduler snapshot/event log and admission ledger only when
  `admit=true`.
- Loop execution mutates scheduler snapshot/event log and writes evidence only
  when `runLoop=true`.
- Projection refresh writes only the scheduler-derived read-only trajectory
  artifact when `refreshProjection=true`.
- Host Evidence presentation readback is always read-only.
- Agent-owned `.codex/progress-graph/local-work-trajectory.json` is never
  mutated by this workflow.

## Acceptance Criteria

The gate may close when:

1. A host-neutral request/result helper composes the scheduler operator workflow
   with ordered per-step status.
2. Read-only mode can inspect candidates and Host Evidence presentation without
   mutating scheduler state, admission ledger, projection, evidence, or Local
   Work Trajectory.
3. Full mode over the dogfood fixture admits the exact candidate, runs bounded
   fake loop, writes loop evidence, refreshes scheduler projection, and reads
   Host Evidence presentation.
4. Step failures stop dependent later steps and preserve clear error metadata.
5. MCP `schedulerOperatorWorkflow` and CLI `scheduler operator-workflow` expose
   the same contract.
6. Focused tests cover helper, MCP, CLI, and regression surfaces.
7. Status/review/follow-up docs record the completed boundary and next
   recommended slice.

## Completion Notes

Implemented:

1. `tools/progress_graph/scheduler_operator_workflow.py` now defines
   `SchedulerOperatorWorkflowRequest`, ordered step results, and
   `run_scheduler_operator_workflow()`.
2. The workflow defaults to read-only inspection/readback and requires explicit
   `admit`, `runLoop`, and `refreshProjection` flags for mutating steps.
3. Full workflow mode composes existing durable APIs: ExchangeArtifact
   inspection, exact-version ledgered admission, bounded fake scheduler loop,
   scheduler-loop evidence write, scheduler-derived projection refresh, and
   Host Evidence presentation readback.
4. `GovernanceTools.scheduler_operator_workflow()` and MCP
   `schedulerOperatorWorkflow` expose the shared contract for Codex/MCP hosts.
5. `doc-based-coding scheduler operator-workflow` exposes the same contract for
   CLI/Host UX smoke usage.
6. Duplicate admission failure remains isolated to the `admit` step and skips
   dependent `runLoop` / `refreshProjection` steps.

Validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_operator_workflow"
3 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "operator_workflow"
3 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "operator_workflow"
1 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_doc_loop_prompts.py tests/test_mcp_admission.py -k "scheduler or exchange_artifact or host_evidence or operator_workflow"
134 passed
```

No UI surface changed in this slice, so screenshot validation was not required.
