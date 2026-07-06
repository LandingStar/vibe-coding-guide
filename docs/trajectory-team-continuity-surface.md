# Trajectory Team Continuity Surface

## Purpose

Trajectory Team Continuity is the leader/operator control surface for keeping a
worker identity continuous across later nodes in the same Local Work Trajectory.

It exposes the runtime bridge through one shared dispatcher:

- CLI: `doc-based-coding scheduler trajectory-team <action>`
- MCP: `trajectoryTeamContinuity`
- Runtime: `run_trajectory_team_continuity_surface()`

The CLI and MCP surfaces are thin wrappers over the same dispatcher. They must
not duplicate mapping, permission, readback, or authority-split logic.

## Actions

Supported actions:

- `inspect`: read trajectory team rows from binding, ownership, lease, and team
  event evidence.
- `resolve`: resolve the current lane worker continuity and optionally append a
  team-resolution audit event.
- `assign`: assign a lane to a continuous worker binding and claim lane
  ownership.
- `activate`: activate a claimed ownership after successful delivery evidence.
- `suspend`: pause an ownership without releasing it.
- `resume`: resume a suspended ownership.
- `transfer`: transfer lane ownership to a replacement binding.
- `fork`: fork an existing binding and transfer ownership to the fork.
- `release`: release lane ownership without deleting binding history.
- `noContinuity`: record an explicit no-continuity fallback reason.

Read-only actions are `inspect` and `resolve`. `resolve` is read-like from a
provider/scheduler perspective, but it can append a team audit event when
requested through the lower bridge.

Mutating actions are `assign`, `activate`, `suspend`, `resume`, `transfer`,
`fork`, `release`, and `noContinuity`.

## Authority Boundary

Mutating actions require `callerRole` to be one of:

- `leader`
- `main`
- `supervisor`
- `guide`

Worker-style roles are rejected:

- `worker`
- `subagent`
- `lane_worker`
- `bounded_worker`

Rejected workers must write requested status or trajectory/team suggestions in
`Subagent Report.trajectory_update`. The fixed procedure is:

- `docs/worker-trajectory-update-reporting.md`

This surface does not give workers direct Local Work or team-roster mutation
authority.

## Evidence Products

The surface reads or writes these project-owned products:

- continuous worker binding ledger:
  `.dbc/runtime/continuous-worker-bindings.json`
- continuous worker binding event log:
  `.dbc/runtime/continuous-worker-binding-events.jsonl`
- lane ownership ledger:
  `.dbc/runtime/continuous-worker-lane-ownerships.json`
- lane ownership event log:
  `.dbc/runtime/continuous-worker-lane-ownership-events.jsonl`
- delivery lease ledger readback:
  `.dbc/runtime/continuous-worker-delivery-leases.json`
- trajectory team event log:
  `.dbc/runtime/trajectory-team-continuity-events.jsonl`
- optional scheduler event log for audit-only continuity events.

Scheduler continuity events are audit-only. They must not change scheduler task
replay semantics.

## Readback Shape

Every result returns a JSON object with:

- `ok`
- `action`
- `status`
- `message`
- `trajectory_id`
- `lane_id`
- `rows`
- `bridge_result`
- `paths`
- `errors`
- `authority_split`
- `worker_report_procedure`

Each row contains:

- `trajectory_id`
- `lane_id`
- `leader_id`
- `worker_id`
- `runtime_provider`
- `binding_id`
- `binding_status`
- `ownership_id`
- `ownership_status`
- `compact_context_ref`
- `mailbox_cursor_ref`
- `worker_report_refs`
- `audit_refs`
- `active_lease_id`
- `active_lease_status`
- `last_team_event_kind`
- `last_team_event_id`
- `no_continuity_reason`

## Authority Split

The surface always reports:

- `provider_executed=false`
- `scheduler_state_mutated=false`
- `delivery_state_mutated=false`
- `local_work_trajectory_mutated=false`
- `worker_direct_mutation_allowed=false`
- `raw_transcript_persisted=false`
- `secret_value_persisted=false`

`bridge_mutated` is true only when the lower bridge wrote team/binding/ownership
evidence for the requested action.

## CLI Examples

Assign one lane:

```text
doc-based-coding scheduler trajectory-team assign ^
  --trajectory-id local-work:feature ^
  --lane-id lane:server ^
  --leader-id agent:guide ^
  --worker-id worker:server ^
  --runtime-provider opencode ^
  --session-id session-server ^
  --compact-context-ref dbc://context/server ^
  --mailbox-cursor-ref dbc://mailbox/server@1
```

Inspect one lane:

```text
doc-based-coding scheduler trajectory-team inspect ^
  --trajectory-id local-work:feature ^
  --lane-id lane:server
```

Rejecting a worker mutation:

```text
doc-based-coding scheduler trajectory-team assign ^
  --caller-role worker ^
  --trajectory-id local-work:feature ^
  --lane-id lane:server ^
  --worker-id worker:server
```

The result is `ok=false`, `status=caller_role_rejected`, and points to
`docs/worker-trajectory-update-reporting.md`.

## MCP Example

```json
{
  "action": "assign",
  "trajectoryId": "local-work:feature",
  "laneId": "lane:server",
  "leaderId": "agent:guide",
  "workerId": "worker:server",
  "runtimeProvider": "opencode",
  "sessionId": "session-server",
  "compactContextRef": "dbc://context/server",
  "mailboxCursorRef": "dbc://mailbox/server@1"
}
```

MCP uses the same dispatcher and result shape as the CLI.

## Non-Goals

This surface does not:

- run Codex, Qoder, OpenCode, or any other provider;
- start workers;
- consume delivery;
- mutate scheduler task state;
- mutate agent-owned Local Work Trajectory;
- decide automatic worker assignment policy;
- create persistent agent home/private folders;
- implement `llm-auto` compact;
- replace monitoring UI.
