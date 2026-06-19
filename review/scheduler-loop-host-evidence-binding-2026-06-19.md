# Review - Scheduler Loop Host Evidence Binding

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-scheduler-loop-host-evidence-binding.md`

## Scope Reviewed

This slice added durable evidence for bounded scheduler daemon loop results and
made the existing scheduler evidence resources understand that new product type.

Implemented:

1. Runtime evidence contract:
   - `SchedulerLoopEvidence`
   - `SchedulerLoopEvidenceSummary`
   - `SchedulerLoopEvidenceWriteResult`
   - `build_scheduler_loop_evidence()`
   - `write_scheduler_loop_evidence()`
   - `read_scheduler_loop_evidence_summary()`
   - `default_scheduler_loop_evidence_path()`
2. CLI write surface:
   - `doc-based-coding scheduler daemon-loop --evidence-id ID`
   - optional `--evidence-path PATH`
3. Read-only resource/presentation integration:
   - `dbc://host-evidence/bundle` reads both `host_scheduler_run_evidence` and
     `scheduler_loop_evidence`;
   - `dbc://host-evidence/presentation` creates scheduler-loop presentation
     cards;
   - malformed evidence files remain isolated into `errors[]`.
4. Prompt guidance and bootstrap copy updates.
5. Tests for evidence write/read, CLI evidence output, resource readback,
   presentation cards, and prompt coverage.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_loop_evidence or scheduler_daemon_loop"
7 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_daemon_loop"
3 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence"
7 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
20 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
278 passed, 1 skipped
```

## Behavioral Notes

Evidence writing is explicit. `scheduler daemon-loop` does not write evidence
unless `--evidence-id` is provided. When present, the default path is:

```text
.codex/scheduler/evidence/<safe-id>.json
```

The evidence artifact includes a compact loop summary and embeds raw
`loop_result` for review/debugging. The read-only summary deliberately excludes
that raw `loop_result` so UI/resource consumers bind to the stable summary
surface.

The existing `dbc://host-evidence/*` resource names remain unchanged because
they already represent scheduler evidence stored under `.codex/scheduler/evidence`.
The bundle now supports a mixed directory containing host-run and scheduler-loop
evidence artifacts.

## Authority Boundary

The authority split remains:

1. Scheduler snapshot and scheduler event log are scheduler authority.
2. Scheduler loop evidence is a review/readback artifact, not replay authority.
3. Resource reads are read-only and do not run scheduler loops or providers.
4. Scheduler projection remains explicitly refreshed by
   `doc-based-coding scheduler project`.
5. Local Work Trajectory remains agent-owned.
6. ExchangeArtifact store and admission ledger are not touched by evidence
   writing or reading.

## Explicit Non-Goals Preserved

This slice did not add:

1. New MCP execution tool.
2. UI binding.
3. Real Qoder/provider execution.
4. Automatic scheduler projection refresh.
5. ExchangeArtifact lifecycle mutation.
6. Admission ledger mutation.
7. Local Work Trajectory mutation from scheduler code.
8. Background daemon/service lifecycle management.

## Follow-Up

The scheduler loop now has durable evidence and a read-only operator/resource
surface. The strongest next backend candidate is a host-injected runtime loop
slice with mock-Qoder validation, because provider authority can now be tested
while preserving evidence/readback boundaries.
