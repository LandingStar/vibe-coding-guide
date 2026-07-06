# Monitoring UI Backend API

> Status: first read-only snapshot API

## Purpose

This document describes the backend contract for a future orchestration
monitoring UI. The current implementation is frontend/backend separated:

- backend API/read model: implemented;
- frontend visual implementation: intentionally not implemented in this slice.

The frontend should consume the snapshot API instead of reading scheduler,
delivery, runtime, exchange, or smoke files directly.

## Command

```powershell
python -m src scheduler inspect-monitoring-snapshot `
  --snapshot-path .dbc/scheduler/live-codex-concurrent-worker-smoke-state.json `
  --event-log-path .dbc/scheduler/live-codex-concurrent-worker-smoke-events.jsonl `
  --delivery-state-path .dbc/scheduler/live-codex-concurrent-worker-smoke-delivery-state.json `
  --runtime-invocation-log-path .dbc/runtime/live-codex-concurrent-worker-smoke-invocations.jsonl `
  --artifact-store-path .dbc/orchestration/live-codex-concurrent-worker-smoke-exchange-artifacts.json `
  --live-codex-smoke-report-path .dbc/scheduler/live-codex-concurrent-worker-smoke-report.json
```

Required:

- `--snapshot-path`
- `--event-log-path`

Optional:

- `--delivery-state-path`
- `--runtime-invocation-log-path`
- `--artifact-store-path`
- `--live-codex-smoke-report-path`
- repeated `--target-task-id`
- `--latest-limit N`

## Runtime API

Python callers can use:

```python
from src.runtime.orchestration import (
    MonitoringSnapshotRequest,
    inspect_monitoring_snapshot,
)

snapshot = inspect_monitoring_snapshot(
    MonitoringSnapshotRequest(
        scheduler_snapshot_path=".dbc/scheduler/state.json",
        scheduler_event_log_path=".dbc/scheduler/events.jsonl",
    )
)
payload = snapshot.to_json_dict()
```

The API is read-only. It does not run providers, mutate scheduler/delivery
state, consume worker reports, write Local Work Trajectory, or expose raw
transcripts.

## Response Shape

Top-level fields:

- `schema_version`: currently `monitoring-snapshot.v1`
- `ok`: true when core status readback had no parse/recovery errors
- `next_action`: first suggested operator action
- `paths`: resolved artifact paths used by the snapshot
- `scheduler`: scheduler task state and target summary
- `delivery`: leader-worker delivery summary
- `runtimeInvocations`: compact runtime invocation counts, latest records, and concurrency summary
- `artifacts`: output/review/worker patch artifact refs
- `liveCodexSmoke`: optional C9 smoke report summary
- `workerReports`: worker report consumption contract hints
- `operatorSignals`: prioritized UI/operator notices
- `errors`: readback errors
- `authoritySplit`: read-only/no-raw-transcript/no-trajectory-mutation flags

## Frontend Notes

Poll the snapshot endpoint/command at a moderate interval, such as 2-5 seconds.
Treat `schema_version` as the compatibility key. Unknown fields should be
ignored.

Do not infer provider execution from the monitoring API call itself. The
snapshot read is non-mutating; execution status is represented by
`runtimeInvocations`, `delivery`, and `operatorSignals`.

The current backend is a CLI JSON surface. A later host adapter may expose the
same payload through HTTP, webview RPC, or MCP resource without changing the
frontend data model.

## Error Handling

Missing optional files should render as unavailable sections, not hard UI
failure. For example, when no live C9 smoke report exists:

- `liveCodexSmoke.exists` is false
- `liveCodexSmoke.verdict` is `unavailable`
- `operatorSignals` includes `live_codex_smoke_missing`

Missing or invalid scheduler snapshot/event log is a core error because those
paths define the primary work state.

## Authority Rules

The frontend must not add buttons that directly mutate scheduler or Local Work
Trajectory through this snapshot API. Mutating operations should remain
separate explicit commands/tools with their own authority docs.

Worker trajectory updates are intentionally represented as:

- procedure doc: `docs/worker-trajectory-update-reporting.md`
- schema: `docs/specs/subagent-report.schema.json`
- consumer command: `doc-based-coding scheduler consume-worker-trajectory-report`

The monitoring UI may link to those surfaces, but should not pretend the
snapshot consumed worker reports.
