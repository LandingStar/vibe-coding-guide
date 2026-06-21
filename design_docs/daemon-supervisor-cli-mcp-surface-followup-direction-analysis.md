# Daemon Supervisor CLI/MCP Surface Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-daemon-supervisor-cli-mcp-surface.md`
closed with CLI and MCP surfaces for one host-managed daemon supervisor step.

Review evidence:

- `review/daemon-supervisor-cli-mcp-surface-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. lifecycle control file and lifecycle-gated run-once;
2. bounded host-managed harness;
3. deterministic retry/deadline/cancellation policy over harness attempts;
4. runtime supervisor contract with host/session/run identity and status
   readback;
5. CLI and MCP surfaces for both policy harness and supervisor step.

Codex can now invoke the supervisor layer directly through
`schedulerDaemonSupervisorStep` while preserving fake-runtime-only and bounded
execution.

## Candidate A - Supervisor Dogfood Workflow

### Goal

Create a deterministic dogfood workflow that seeds scheduler work, starts
lifecycle control, invokes the supervisor step through CLI/MCP-style surfaces,
and reads back scheduler/supervisor status.

### Why Useful

The supervisor is now callable, but the project has not yet proven the complete
operator workflow as one repeatable smoke. A dogfood workflow would validate
the intended sequence before storage lifecycle or real-provider work depends on
it.

### Boundary

Keep fake runtime, explicit paths, no Host UX, no projection refresh unless
called as an explicit separate step, no cleanup, and no Local Work Trajectory
mutation from scheduler code.

## Candidate B - Agent Home / Context Session Binding Over Supervisor Runs

### Goal

Bind agent home, temporary scratch, and context-session lifecycle to supervisor
run identity and harness attempts.

### Why Useful

Larger agent orchestration needs persistent/private agent storage and temporary
scratch ownership. The supervisor surface can now carry identity fields needed
for that lifecycle.

### Boundary

Do not introduce storage mutation before the supervisor invocation workflow is
dogfooded end to end.

## Candidate C - Host UX Readback For Supervisor Status

### Goal

Expose supervisor status/result readback in Host UX.

### Why Useful

Operator visibility would help later daemon management, but the backend
workflow should stabilize first.

### Boundary

Do not add UI before the backend dogfood workflow proves the result shape and
expected sequence.

## Recommendation

My current preference is Candidate A:

```text
Supervisor Dogfood Workflow
```

Reason:

1. CLI/MCP invocation is now available, so the next risk is sequence quality,
   not individual API reachability;
2. a deterministic dogfood workflow will produce reusable evidence for later
   agent-home/session binding;
3. Host UX is premature until the backend workflow is stable;
4. storage lifecycle binding should consume proven supervisor run identity
   rather than define it implicitly.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-supervisor-dogfood-workflow.md`

Suggested first slice:

1. define a deterministic fake-runtime supervisor dogfood workflow;
2. seed one small scheduler task or reuse a deterministic fixture;
3. start lifecycle control explicitly;
4. invoke the supervisor step through the same mapping used by CLI/MCP;
5. read back scheduler state and supervisor result facts;
6. add focused tests and prompt guidance;
7. preserve no Host UX, no live provider, no automatic projection refresh, no
   cleanup, and no Local Work Trajectory mutation from scheduler code.
