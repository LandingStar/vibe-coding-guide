# Review - Scheduler Operator Unified Workflow Surface

> Date: 2026-06-19
> Planning Gate: `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-unified-workflow-surface.md`

## Summary

Implemented a shared scheduler operator workflow surface that lets Codex/MCP,
CLI, and future Host UX layers use the same explicit operator contract.

The new workflow:

1. inspects ExchangeArtifact scheduler-admission candidates;
2. optionally admits one exact artifact/version;
3. optionally runs a bounded fake scheduler loop and writes scheduler-loop
   evidence;
4. optionally refreshes scheduler-derived trajectory projection;
5. reads Host Evidence presentation.

Mutating steps remain opt-in and step-scoped. The workflow does not mutate
agent-owned Local Work Trajectory.

## Changed Files

- `tools/progress_graph/scheduler_operator_workflow.py`
- `tools/progress_graph/__init__.py`
- `src/mcp/tools.py`
- `src/mcp/server.py`
- `src/__main__.py`
- `tests/test_runtime_orchestration.py`
- `tests/test_cli.py`
- `tests/test_mcp_admission.py`
- `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-unified-workflow-surface.md`

## Validation

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

## Boundary Checks

- No live Qoder or real provider execution was added.
- No background daemon lifecycle was added.
- No automatic admission or automatic task execution occurs by default.
- No ExchangeArtifact consumed marking was added.
- No scheduler/admission/evidence schema was changed.
- No agent-owned `.codex/progress-graph/local-work-trajectory.json` mutation
  occurs from the workflow.
- No VS Code UI binding changed in this slice.

## Residual Risk

The workflow is still fake-runtime-only. Real-provider execution should remain
behind a host-owned runtime adapter gate with explicit credentials and
permission evidence.
