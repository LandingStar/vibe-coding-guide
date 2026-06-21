# Backend Orchestration After Host UX Sandbox Branch Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/host-ux-evidence-aware-workflow-defaults-sandbox-receipt-workflow-followup-direction-analysis.md`
recommends pausing the Host UX sandbox receipt branch unless real receipt
evidence shows a concrete cleanup-diff weakness.

The project therefore needs to choose the next scheduler/orchestration backend
slice instead of continuing to add Host UX controls.

## Current Position

The orchestration backend already has these completed pieces:

1. provider-neutral runtime adapter objects with fake and Qoder seams;
2. scheduler state, dependency, edit lease, context scope, and sandbox profile
   objects;
3. durable scheduler snapshot and event-log replay / compaction;
4. bounded scheduler daemon tick and bounded daemon loop;
5. scheduler daemon lifecycle control file with start / heartbeat / pause /
   resume / cancel / shutdown / stale readback;
6. CLI and MCP lifecycle surfaces:
   `doc-based-coding scheduler lifecycle ...`,
   `schedulerLifecycleControl`, and `schedulerLifecycleRunOnce`;
7. explicit git-worktree sandbox opt-in, durable sandbox allocation receipt
   evidence, cleanup runner, and Host Evidence readback;
8. Host UX surfaces for manual sandbox receipt workflow selection and evidence
   prefill.

The important gap is not "create a scheduler." The gap is that the current
lifecycle surface is still run-once / bounded-loop driven by a caller. There is
no host-owned process harness that repeatedly observes the lifecycle control
file, heartbeats, executes bounded runs, handles shutdown/cancel, and writes
evidence in a deterministic local way.

## Candidate A - Host-Managed Scheduler Daemon Process Harness

### Goal

Add a small host-owned process harness around the existing lifecycle control
and bounded daemon loop.

This should be a local operator/dev harness, not an OS service.

### Narrow Scope

1. Reuse `SchedulerDaemonLifecycleControl` as lifecycle authority.
2. Add a harness request/result that can run a bounded number of polling
   cycles in tests.
3. On each cycle:
   - inspect lifecycle state;
   - write heartbeat while running;
   - call the existing lifecycle-gated run-once helper;
   - stop on pause, cancel, shutdown, stale, max cycles, or error threshold.
4. Write compact harness evidence / logs with process id, lifecycle path,
   heartbeat timestamps, cycle summaries, and stop reason.
5. Keep fake runtime only by default.
6. Keep scheduler projection refresh explicit and separate.

### Non-Goals

1. No Windows service, systemd unit, launch agent, file watcher, or install-time
   daemon registration.
2. No live Qoder or real provider expansion.
3. No automatic Local Work Trajectory mutation from daemon code.
4. No Host UX binding.
5. No hidden cleanup; sandbox receipt cleanup remains explicit.
6. No broad retry/deadline/cancellation redesign.

### Why It Fits Now

This is the missing layer between:

```text
operator manually calls lifecycle run-once
```

and:

```text
real multi-agent scheduler keeps making progress under host control
```

It also keeps with `docs/host-interaction-model.md`: lifecycle and scheduler
state stay in Portable Runtime, while process ownership remains host-managed.

## Candidate B - Retry / Deadline / Cancellation Policy Over Lifecycle

### Goal

Formalize retry, timeout, deadline, and cancellation semantics over the current
lifecycle and task states.

### Why Useful

The bounded loop already has max ticks, max runs per tick, runtime failure
limits, and lifecycle cancel. A policy layer would make long-running scheduling
safer before more realistic runtimes are attached.

### Why Not First

Policy semantics are easier to validate once there is a process harness that
can exercise repeated cycles and stop conditions. Without the harness, this
would mostly extend static contracts.

## Candidate C - Qoder Runtime Provider Dogfood Over Existing Host Loop

### Goal

Run a controlled Qoder-backed scheduler task through the existing host-owned
runtime wiring.

### Why Useful

It would validate that the runtime adapter boundary still works with a real
provider instead of fake/mock clients.

### Why Not First

`docs/qoder-host-provisioning-check-guide.md` keeps real Qoder host-owned and
credential-sensitive. The current Host UX branch has also just finished a
large operator surface run. The next backend slice should first make the
scheduler lifecycle more operationally coherent without depending on local
credentials or external SDK readiness.

## Candidate D - Agent Home / Context Session Binding

### Goal

Connect existing agent storage governance products to scheduler runtime
sessions so persistent agent home and temporary scratch space can become
operational resources.

### Why Useful

`design_docs/agent-home-and-scratch-space-design-record.md` and
`src/runtime/orchestration/agent_storage.py` already define the governance
product model. This is important before larger agent clusters.

### Why Not First

The current model still deliberately avoids committing to a default storage
path or actual directory lifecycle. It should follow a stable scheduler process
harness so storage allocation and cleanup can be tied to visible run cycles.

## Candidate E - Backend-Enriched Cleanup Diff Payload

### Goal

Expose a structured cleanup diff payload from Host Evidence presentation so
the UI no longer infers before/after semantics from generic receipt cards.

### Why Conditional

This remains the correct Host UX follow-up only if real sandbox receipt samples
show that the current presentation-derived cleanup diff is too weak. It should
not be the default next slice while there is no such evidence gap.

## Recommendation

Choose Candidate A next:

```text
Host-Managed Scheduler Daemon Process Harness
```

Reason:

1. the scheduler model, lifecycle control, CLI/MCP lifecycle surface, bounded
   loop, git-worktree opt-in, and receipt workflow already exist;
2. the highest-value missing backend capability is a host-owned process loop
   that uses those contracts repeatedly and visibly;
3. this advances toward real multi-agent orchestration without making Host UX
   the scheduler authority;
4. it does not require live Qoder credentials or a provider SDK to be ready;
5. it creates the right test bed for later retry/deadline/cancel policy and
   agent home/session binding.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-host-managed-scheduler-daemon-process-harness.md`

Suggested first slice:

1. define harness request/result/evidence objects around the existing lifecycle
   control path;
2. implement a deterministic bounded harness loop with injectable sleep/no-op
   clock behavior for tests;
3. cover lifecycle stop cases: paused, cancelled, shutdown, stale, max cycles,
   and loop failure threshold;
4. keep runtime provider fake-only and projection/cleanup explicit;
5. add focused runtime and CLI smoke tests before considering Host UX binding.

## Basis Documents

- `design_docs/agent-cluster-scheduling-and-isolation-investigation.md`
- `review/agent-runtime-adapter-and-scheduler-skeleton-2026-06-17.md`
- `design_docs/stages/planning-gate/2026-06-20-background-scheduler-daemon-lifecycle-protocol.md`
- `design_docs/stages/planning-gate/2026-06-20-scheduler-daemon-lifecycle-cli-mcp-surface.md`
- `design_docs/host-ux-evidence-aware-workflow-defaults-sandbox-receipt-workflow-followup-direction-analysis.md`
- `docs/host-interaction-model.md`
- `docs/subagent-management.md`
- `docs/qoder-host-provisioning-check-guide.md`
- `design_docs/agent-home-and-scratch-space-design-record.md`
