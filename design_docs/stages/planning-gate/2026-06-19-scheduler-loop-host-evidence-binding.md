# Planning Gate - Scheduler Loop Host Evidence Binding

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/scheduler-durable-daemon-loop-policy-followup-direction-analysis.md`
recommends creating a durable evidence product for bounded scheduler daemon
loop results before UI binding or host-injected runtime execution.

## Problem

The scheduler now has a bounded repeated loop contract:

```text
SchedulerDaemonLoopStopPolicy
SchedulerDaemonLoopRequest
SchedulerDaemonLoopIteration
SchedulerDaemonLoopResult
run_scheduler_daemon_loop()
doc-based-coding scheduler daemon-loop
```

The result is structured enough for operators and future UI surfaces, but it is
currently ephemeral unless copied from CLI stdout. The platform needs an
explicit evidence product that records loop outcomes in the existing scheduler
evidence area:

```text
.codex/scheduler/evidence/<evidence-id>.json
```

The evidence should be durable and inspectable, but reading it must remain
read-only.

## Scope

### Slice 1 - Evidence Contract

Define a scheduler-loop evidence product:

```text
SchedulerLoopEvidence
SchedulerLoopEvidenceSummary
build_scheduler_loop_evidence()
write_scheduler_loop_evidence()
read_scheduler_loop_evidence_summary()
```

Expected evidence fields:

1. `product_type = scheduler_loop_evidence`;
2. `schema_version = 1`;
3. `evidence_id`;
4. `timestamp`;
5. scheduler snapshot/event-log paths;
6. runtime provider and stop policy summary;
7. loop result summary:
   - `tick_count`;
   - `total_run_count`;
   - `stop_reason`;
   - `stop_detail`;
   - `scheduler_event_count`;
   - `final_queue_summary`;
   - iteration summaries;
8. `authority_split`;
9. optional metadata.

### Slice 2 - Write Surface

Add explicit evidence writing to the CLI loop surface:

```text
doc-based-coding scheduler daemon-loop --evidence-id ID [--evidence-path PATH]
```

Expected behavior:

1. Without `--evidence-id`, CLI behavior remains unchanged and does not write
   evidence.
2. With `--evidence-id`, the command writes one evidence JSON artifact after a
   successful loop run.
3. Default path uses `.codex/scheduler/evidence/<safe-evidence-id>.json`.
4. CLI JSON output reports `evidence_written`, `evidence_path`, and evidence
   authority clues.
5. Evidence writing must not refresh scheduler projection or mutate Local Work
   Trajectory.

### Slice 3 - Read Surface

Extend the existing read-only host evidence bundle/presentation to recognize
both evidence product types under `.codex/scheduler/evidence`:

1. `host_scheduler_run_evidence`;
2. `scheduler_loop_evidence`.

The existing resource URIs remain:

```text
dbc://host-evidence/bundle
dbc://host-evidence/presentation
```

They should remain read-only and must not run providers, run scheduler loops,
refresh projection, or mutate Local Work Trajectory.

## Non-Goals

This gate does not:

1. Add a new MCP execution tool.
2. Add UI binding.
3. Add real Qoder or other external provider execution.
4. Automatically refresh scheduler projection.
5. Mutate ExchangeArtifact lifecycle or admission ledger state.
6. Mutate `.codex/progress-graph/local-work-trajectory.json` from scheduler
   code.
7. Replace existing host scheduler run evidence.
8. Add background daemon/service lifecycle management.

## Acceptance Criteria

The gate may close when:

1. Scheduler-loop evidence contract is documented and implemented.
2. `scheduler daemon-loop --evidence-id` writes a durable evidence artifact to
   `.codex/scheduler/evidence` by default.
3. Existing host evidence bundle/presentation resources can read scheduler-loop
   evidence and isolate malformed files.
4. CLI/resource reads remain read-only.
5. Tests cover evidence write, summary read, mixed evidence bundle,
   presentation card generation, CLI evidence output, and non-goals.
6. Review/status docs record that MCP execution tools, UI binding, real
   provider execution, automatic projection refresh, ExchangeArtifact mutation,
   and Local Work Trajectory mutation remain deferred.

## Implementation Summary

Completed on 2026-06-19.

This slice added a durable scheduler-loop evidence product and connected it to
the existing read-only scheduler evidence bundle/presentation surface.

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
   - default write path `.codex/scheduler/evidence/<safe-id>.json`
   - stdout reports `evidence_written` and `evidence_path`.
3. Read-only resource/presentation support:
   - existing `dbc://host-evidence/bundle` can now read
     `scheduler_loop_evidence`;
   - existing `dbc://host-evidence/presentation` creates scheduler-loop cards;
   - malformed/unsupported local evidence files remain isolated into
     `errors[]`.
4. Prompt guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`;
   - bootstrap copy under `doc-loop-vibe-coding/assets/bootstrap/`.

## Validation

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

## Non-Goals Preserved

This slice did not add:

1. New MCP execution tool.
2. UI binding.
3. Real Qoder or other external provider execution.
4. Automatic scheduler projection refresh.
5. ExchangeArtifact lifecycle or admission ledger mutation.
6. Local Work Trajectory mutation from scheduler code.
7. Background daemon/service lifecycle management.
