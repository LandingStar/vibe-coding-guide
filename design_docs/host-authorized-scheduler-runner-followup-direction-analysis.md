# Host-Authorized Scheduler Runner Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-17-host-authorized-scheduler-runner-adapter.md`
has reached `READY-FOR-CLOSE-REVIEW`.

The current boundary now proves:

1. A host-owned one-shot request/result contract exists:
   `HostSchedulerRunRequest` and `HostSchedulerRunResult`.
2. `HostSchedulerRunResult.to_json_dict()` exposes compact evidence for host
   UX, tests, and later adapters.
3. The host runner can execute the persisted scheduler through fake runtime and
   injected mock-Qoder wiring.
4. The scheduler-derived projection can be refreshed through
   `run_host_authorized_scheduler_once_and_refresh_projection()`.
5. MCP remains fake-only for `schedulerRunOnceAndProject`.
6. Scheduler projection remains separate from the agent-owned Local Work
   Trajectory artifact.

Evidence review:

- `review/host-authorized-scheduler-runner-adapter-2026-06-17.md`

The next question is no longer whether a host seam can exist. It is which
narrow slice should make that seam useful for controlled runtime dogfood while
preserving the ownership boundary.

## Candidate A — Controlled Host-Runtime Dogfood Harness（推荐）

Do what:

1. Add a narrow host-side dogfood harness over
   `HostSchedulerRunRequest` and
   `run_host_authorized_scheduler_once_and_refresh_projection()`.
2. Use explicit scheduler snapshot / event-log paths and explicit runtime
   provider config.
3. Support two first dogfood modes:
   - deterministic fake runtime
   - mock-Qoder or wrapper-injected qoder client, depending on host readiness
4. Persist a compact host-run evidence JSON for review:
   - snapshot path
   - event-log path
   - projection path
   - runtime providers
   - host invocation metadata
   - run count / stop reason
   - output artifact refs
   - permission-review tasks
   - history summary
   - authority split flags
5. Keep qoder execution out of MCP. The harness is a host / CLI / local Python
   surface, not a new MCP real-provider tool.

Why first:

1. It directly exercises the just-added host runner contract.
2. It gives a realistic place to accumulate dogfood evidence before a daemon.
3. It keeps the real-provider boundary explicit and auditable.
4. It can start with fake and mock-Qoder, then admit a real wrapper later
   without changing scheduler authority.
5. It gives later VS Code / Codex host adapters a concrete result shape to
   consume.

Main risk:

The harness could accidentally become a second scheduler surface. Keep it thin:
it should construct a request, call the existing host runner, write compact
evidence, and report paths.

Suggested first gate:

```text
Controlled Host Runtime Dogfood Harness
```

Suggested first slice:

1. Define the evidence JSON shape.
2. Add a local Python entry/helper that runs fake runtime through the host
   runner and writes evidence.
3. Add a mock-Qoder mode that proves host authorization and injected client
   behavior through the same harness.
4. Add prompt guidance for agents maintaining dogfood evidence.
5. Keep MCP fake-only and unchanged.

Non-goals:

1. No real Qoder SDK import unless a later explicit gate authorizes it.
2. No scheduler daemon.
3. No process isolation beyond existing shared-process metadata.
4. No Local Work Trajectory mutation from scheduler state.
5. No runtime subagents as project-level lanes.

## Candidate B — Real QoderQueryClient Wrapper

Do what:

1. Implement a real Qoder SDK wrapper behind the existing
   `QoderQueryClient` protocol.
2. Normalize SDK response into `QoderQueryResult`.
3. Surface permission requests without approving them.
4. Reference transcript material instead of copying raw transcripts into
   scheduler authority.

Why not first:

The host-runner seam exists, but the project still lacks a repeatable dogfood
harness and evidence artifact. A real SDK wrapper before that harness would mix
credential, host invocation, and runtime behavior into one slice.

Use after Candidate A has a repeatable evidence path.

## Candidate C — Scheduler Daemon Loop

Do what:

1. Add a long-running queue loop over persisted scheduler state.
2. Handle periodic recovery, cancellation, timeout, retry, and event-log
   rotation policy.

Why not first:

The one-shot host runner has not yet been dogfooded through a stable host
harness. Daemon behavior would multiply lifecycle and recovery cases before the
single-run evidence path is mature.

## Candidate D — Real Sandbox Provider

Do what:

1. Implement git-worktree, Docker, or remote-VM sandbox providers.
2. Bind edit leases and mount policies to actual process / filesystem
   isolation.

Why not first:

Sandbox contracts are currently metadata-only. Real isolation should follow a
repeatable host-runtime dogfood path so the project can test which provider
constraints are actually needed.

## Candidate E — Scheduler Projection UI Enrichment

Do what:

1. Add richer UI affordances for scheduler-derived trajectory history.
2. Show compact scheduler event timelines, host-run details, and permission
   review markers.

Why not first:

The scheduler projection is visible, but the next bottleneck is execution
evidence and host runtime integration. UI enrichment should consume stable
host-run evidence rather than drive its schema.

## Current Recommendation

Choose Candidate A as the next planning gate:

```text
Controlled Host Runtime Dogfood Harness
```

This keeps the project contract-first and gives the later real Qoder wrapper,
daemon, sandbox, and UI work a stable host-run evidence artifact to wrap or
consume.

The next gate should explicitly preserve:

1. Scheduler state remains authoritative.
2. Local Work Trajectory remains agent-owned.
3. Scheduler-derived trajectory remains projection-only.
4. MCP scheduler execution remains fake-only.
5. Real providers require host authorization and injected clients.

## Acceptance Criteria For The Next Gate

The next gate should not close until:

1. A host-run evidence JSON shape exists and is documented.
2. A fake-runtime dogfood run can write that evidence JSON and scheduler
   projection.
3. A mock-Qoder host-authorized dogfood run can write the same evidence shape.
4. Evidence includes provider, host invocation, run count, stop reason, output
   artifact refs, permission-review tasks, history summary, and authority split
   flags.
5. MCP fake-only rejection remains covered.
6. Prompt / maintenance guidance explains how to run, inspect, and write back
   dogfood evidence without using `localTrajectory` as scheduler state.
