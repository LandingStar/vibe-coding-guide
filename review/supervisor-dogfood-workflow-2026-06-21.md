# Review - Supervisor Dogfood Workflow

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-supervisor-dogfood-workflow.md`

## Scope Reviewed

This slice added a deterministic fake-runtime supervisor dogfood sequence over
the existing scheduler/operator primitives.

Implemented:

1. Shared workflow helper:
   - `tools.progress_graph.scheduler_supervisor_dogfood_workflow`
   - `SchedulerSupervisorDogfoodWorkflowRequest`
   - `SchedulerSupervisorDogfoodWorkflowResult`
   - `run_scheduler_supervisor_dogfood_workflow()`
2. CLI command:
   - `doc-based-coding scheduler supervisor-dogfood-workflow`
3. GovernanceTools/MCP method and tool:
   - `scheduler_supervisor_dogfood_workflow()`
   - `schedulerSupervisorDogfoodWorkflow`
4. Prompt/audit guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - `design_docs/tooling/MCP Tool Surface Audit.md`
5. Focused runtime, CLI, MCP, and prompt tests.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py tools/progress_graph/scheduler_supervisor_dogfood_workflow.py tools/progress_graph/__init__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_supervisor_dogfood_workflow"
2 passed, 249 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "supervisor_dogfood_workflow"
2 passed, 43 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_lifecycle or scheduler_supervisor or scheduler_daemon_supervisor"
5 passed, 8 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler"
2 passed, 18 deselected
```

Wider related validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_supervisor_dogfood_workflow or scheduler_daemon_supervisor or scheduler_daemon_harness or scheduler_daemon_lifecycle"
21 passed, 230 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
45 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
13 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py
86 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler"
2 passed, 18 deselected
```

Change analysis:

```text
analyze_changes:
- impact: no direct/transitive baseline nodes reported
- coupling: coupling-mcp-tools-registration triggered by src/mcp/tools.py
```

The coupling alert is satisfied by `src/mcp/server.py` list_tools schema and
call_tool routing updates, with `tests/test_mcp_admission.py` covering
registration and routing.

## Behavioral Notes

`schedulerSupervisorDogfoodWorkflow` and
`doc-based-coding scheduler supervisor-dogfood-workflow`:

1. seed a deterministic scheduler dogfood fixture;
2. admit the exact artifact/version into scheduler snapshot and event log;
3. start scheduler daemon lifecycle control explicitly;
4. run one fake-runtime host-managed supervisor step;
5. read final lifecycle and scheduler queue facts;
6. return ordered per-step status and authority facts.

The workflow remains a host/operator sequence. It does not replace the lower
level `schedulerDaemonSupervisorStep` primitive.

## Explicit Non-Goals Preserved

This slice did not:

1. change scheduler daemon supervisor, harness, policy, or lifecycle semantics;
2. run live Qoder or any real provider;
3. add Host UX binding;
4. start an OS service, watcher, timer, or unbounded daemon;
5. refresh scheduler projection automatically;
6. run or hide sandbox cleanup;
7. mark ExchangeArtifact candidates consumed beyond explicit scheduler
   admission;
8. mutate agent-owned Local Work Trajectory from scheduler runtime, CLI, MCP,
   or workflow code;
9. bind agent home, scratch retention, or context-session storage lifecycle.

## Follow-Up

The supervisor invocation sequence is now dogfooded end to end. The next narrow
backend slice should use the proven supervisor run identity as the input for
agent home / context-session binding, rather than adding Host UX first.
