# Review - Scheduler Loop Evidence Presentation Polish

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-scheduler-loop-evidence-presentation-polish.md`

## Scope Reviewed

This slice improved the read-only host evidence presentation surface for
`scheduler_loop_evidence`.

Implemented:

1. Scheduler-loop presentation card facts for runtime provider, host surface,
   host invocation, tick/run/event counts, and final queue counts.
2. Projection-aware presentation clues when evidence metadata or authority
   split provides scheduler projection path/role/refreshed state.
3. Compatibility with legacy scheduler-loop evidence that does not contain
   projection metadata.
4. Prompt guidance and bootstrap prompt copy updates.
5. Tests covering direct presentation construction and MCP/CLI resource
   readback shape.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "scheduler_loop_evidence_presentation or host_evidence_presentation or host_evidence_bundle_isolates"
6 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke_prompt or host_evidence_resources_read_scheduler_loop_evidence"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
287 passed, 1 skipped
```

Change analysis:

```text
impact.direct=[]
impact.transitive=[]
coupling.alerts=[]
```

## Behavioral Notes

Scheduler-loop evidence cards now surface host/runtime/projection clues through
the existing presentation shape:

1. `key_facts` includes runtime provider, host surface, host invocation,
   tick/run/event counts, and queue counts.
2. `refs` includes scheduler projection only when a projection path is known.
3. `authority_clues` includes scheduler projection refreshed state and local
   trajectory mutation state.
4. `metadata` preserves raw evidence metadata and extracted projection fields.

`metadata.surface` is treated as evidence generation metadata. It does not
override card `host_surface`; only `runtime_host_surface` does that. Older
evidence without projection metadata still renders with
`host_surface="scheduler-daemon-loop"` and no scheduler projection ref.

## Authority Boundary

The surface remains read-only:

1. It reads evidence JSON.
2. It does not execute providers.
3. It does not refresh scheduler projection.
4. It does not mutate scheduler state, ExchangeArtifact state, admission
   ledger state, or Local Work Trajectory.
5. It does not bind to VS Code/UI.

## Explicit Non-Goals Preserved

This slice did not add:

1. `scheduler_loop_evidence` schema changes.
2. Provider execution or real-provider CLI/MCP surfaces.
3. Scheduler projection refresh.
4. Scheduler state mutation.
5. ExchangeArtifact or admission ledger mutation.
6. Local Work Trajectory mutation.
7. VS Code/UI binding.
8. Background daemon service lifecycle.

## Follow-Up

Presentation can now show projection clues when evidence contains them. The
next narrow backend improvement is to make the host loop projection workflow
write projection path/summary metadata into its `scheduler_loop_evidence`, so
the read-only presentation has durable projection clues after a composed host
workflow run.
