# Operator Dogfood Closure MCP Surface

> Date: 2026-06-22
> Status: COMPLETED
> Scope: Contract-first MCP exposure for the existing operator dogfood closure product.

## Trigger

`design_docs/operator-dogfood-execution-evidence-closure-followup-direction-analysis.md`
recommends exposing the deterministic fake-runtime operator closure through the
primary Codex-facing MCP surface.

The prior completed slice already added the backend/CLI product:

```text
seed binding-consumer fixture
-> inspect binding refs
-> admit exact artifact/version
-> mark consumed on successful admission
-> run bounded fake scheduler loop
-> refresh scheduler projection
-> read Host Evidence presentation
-> return compact closure summary
```

## Goal

Add MCP tool `schedulerOperatorDogfoodClosure` that calls the existing
`SchedulerOperatorDogfoodClosureRequest` /
`run_scheduler_operator_dogfood_closure()` product and returns the same JSON
shape as runtime/CLI.

This is an agent-facing integration surface, not a new runtime behavior.

## In Scope

1. Add a `GovernanceTools` wrapper for the closure product.
2. Register `schedulerOperatorDogfoodClosure` in `src/mcp/server.py`.
3. Map MCP camelCase fields to the existing request object.
4. Preserve the fake-runtime-only guard and binding-consumer default.
5. Add focused MCP tests for tool listing, successful binding-consumer routing,
   and real-provider rejection.
6. Update scheduler MCP prompt and bootstrap prompt copy.
7. Update `design_docs/tooling/MCP Tool Surface Audit.md`.
8. Write review evidence and status-board writeback after validation.

## Out of Scope

- No Host UX control or visual change.
- No live Qoder or other real runtime provider.
- No daemon service, timer, watcher, or background process.
- No cleanup runner behavior.
- No agent home or scratch directory creation.
- No scheduler/runtime semantic changes beyond invoking the existing closure.
- No Local Work Trajectory mutation from runtime, CLI, or MCP closure code.

## Interface Draft

Tool name:

```text
schedulerOperatorDogfoodClosure
```

Primary arguments:

- `fixture`: `binding-consumer | simple | multilane`, default
  `binding-consumer`
- `artifactId`, `version`
- `artifactStorePath`, `admissionLedgerPath`
- `snapshotPath`, `eventLogPath`, `mergeGateEventLogPath`
- `projectionOutputPath`
- `evidenceId`, `evidencePath`
- `runtimeProvider`: only `fake`
- `maxTicks`, `maxRunsPerTick`, `maxRuntimeFailures`
- `replaceExisting`
- `inspectBindingRefs`
- `markConsumedOnSuccess`
- `actor`
- `timestamp`, `createdAt`
- `guideContext`, `sourceGraphId`, `sourceNodeId`

Expected result:

- top-level `ok`
- `workflow_surface = scheduler-operator-dogfood-closure`
- ordered `steps`
- `fixture_result`
- `workflow_result`
- compact `closure_summary`
- `final_candidate_summary`
- `authority_split`

## Validation Plan

Focused validation:

```text
python -m py_compile src/mcp/tools.py src/mcp/server.py tools/progress_graph/scheduler_operator_dogfood_closure.py tests/test_mcp_admission.py
python -m pytest tests/test_mcp_admission.py -k "OperatorDogfoodClosure"
python -m pytest tests/test_doc_loop_prompts.py -k "scheduler"
python -m pytest tests/test_runtime_orchestration.py -k "SchedulerOperatorDogfoodClosure"
python -m pytest tests/test_cli.py -k "operator_dogfood_closure"
```

Finish with `git diff --check` and `analyze_changes` for touched files.

## Completion Criteria

- MCP list_tools exposes `schedulerOperatorDogfoodClosure`.
- MCP call can run the default `binding-consumer` closure through fake runtime.
- `runtimeProvider != fake` returns a clear guard error and no mutation authority.
- Prompt/audit docs describe the new surface and its boundaries.
- Review evidence and status boards reflect the completed slice.

## Completion Notes

Completed on 2026-06-22.

Review evidence:

- `review/operator-dogfood-closure-mcp-surface-2026-06-22.md`

Implemented:

- `src/mcp/tools.py` exposes
  `GovernanceTools.scheduler_operator_dogfood_closure()`.
- `src/mcp/server.py` registers and routes
  `schedulerOperatorDogfoodClosure`.
- `tests/test_mcp_admission.py` covers list/routing, default
  binding-consumer success, and live-provider rejection.
- Scheduler MCP smoke prompts and
  `design_docs/tooling/MCP Tool Surface Audit.md` document the new surface.

Validation:

```text
py_compile passed
MCP closure focused tests: 2 passed, 19 deselected
MCP adjacent operator/bundle tests: 7 passed, 14 deselected
Runtime closure focused tests: 2 passed, 278 deselected
CLI closure focused tests: 2 passed, 54 deselected
Scheduler prompt tests: 2 passed, 18 deselected
git diff --check passed with Windows line-ending warnings only
analyze_changes: no impact nodes; one expected MCP tools/server registration coupling alert covered by server schema/routing and focused route tests
```
