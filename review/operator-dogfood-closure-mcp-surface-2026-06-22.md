# Operator Dogfood Closure MCP Surface Review

> Date: 2026-06-22
> Scope: `design_docs/stages/planning-gate/2026-06-22-operator-dogfood-closure-mcp-surface.md`
> Result: PASS

## Summary

This slice exposes the existing deterministic operator dogfood closure product
through the Codex-facing MCP surface as `schedulerOperatorDogfoodClosure`.

The new MCP tool is a thin wrapper over
`SchedulerOperatorDogfoodClosureRequest` /
`run_scheduler_operator_dogfood_closure()` and returns the same closure JSON
shape as runtime/CLI.

## Changes Reviewed

- Added `GovernanceTools.scheduler_operator_dogfood_closure()`.
- Registered MCP tool schema and `call_tool` routing in `src/mcp/server.py`.
- Added focused MCP tests for list/routing, binding-consumer success, and
  live-provider rejection.
- Updated scheduler MCP smoke prompts and bootstrap prompt copy.
- Updated `design_docs/tooling/MCP Tool Surface Audit.md`.

## Boundary Check

- No Host UX changes.
- No live Qoder or other real provider execution.
- No daemon service, timers, watchers, or background process.
- No cleanup runner behavior.
- No agent home or scratch directory creation.
- No runtime semantic changes beyond invoking the existing closure product.
- No Local Work Trajectory mutation from MCP/runtime/CLI closure code.

## Validation

Passed:

```text
python -m py_compile src/mcp/tools.py src/mcp/server.py tools/progress_graph/scheduler_operator_dogfood_closure.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
python -m pytest tests/test_mcp_admission.py -k "operator_dogfood_closure or OperatorDogfoodClosure"
python -m pytest tests/test_mcp_admission.py -k "scheduler_operator_workflow or scheduler_operator_dogfood_closure or exchange_artifacts_bundle"
python -m pytest tests/test_runtime_orchestration.py -k scheduler_operator_dogfood_closure
python -m pytest tests/test_cli.py -k operator_dogfood_closure
python -m pytest tests/test_doc_loop_prompts.py -k scheduler
git diff --check -- <touched files>
```

Observed results:

- MCP closure focused tests: `2 passed, 19 deselected`
- MCP adjacent operator/bundle tests: `7 passed, 14 deselected`
- Runtime closure focused tests: `2 passed, 278 deselected`
- CLI closure focused tests: `2 passed, 54 deselected`
- Scheduler prompt tests: `2 passed, 18 deselected`
- `git diff --check`: passed with Windows line-ending warnings only

## Change Analysis

`analyze_changes` reported:

- impact: `direct=[]`, `transitive=[]`
- coupling: one expected `coupling-mcp-tools-registration` alert because
  `src/mcp/tools.py` added an MCP method.

The coupling alert is satisfied by:

- `src/mcp/server.py` list_tools schema for `schedulerOperatorDogfoodClosure`
- `src/mcp/server.py` call_tool routing
- focused MCP route tests in `tests/test_mcp_admission.py`

## Residual Risk

The closure still remains fake-runtime-only. Live Qoder or other real-provider
dogfood remains intentionally outside this slice and should require a separate
planning gate with host permission and runtime isolation evidence.
