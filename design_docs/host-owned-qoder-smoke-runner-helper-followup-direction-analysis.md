# Host-Owned Qoder Smoke Runner Helper Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-17-host-owned-qoder-smoke-runner-helper.md`
has reached `COMPLETED`.

The current boundary now proves:

1. `run_host_owned_qoder_smoke()` exists as a repeatable host-owned helper.
2. The helper can initialize a minimal Qoder smoke scheduler snapshot.
3. The helper constructs host invocation and qoder permission grant.
4. The helper reuses `QoderSDKQueryClient` or an injected `QoderQueryClient`.
5. The helper delegates execution to `run_host_runtime_dogfood_harness()`.
6. Deterministic injected-client tests prove evidence/projection writes.
7. Missing auth fails closed before evidence/projection writes or scheduler task
   mutation.
8. MCP `schedulerRunOnceAndProject` remains fake-only.

Evidence review:

- `review/host-owned-qoder-smoke-runner-helper-2026-06-17.md`

## Candidate A — Credentialed Live Qoder Smoke

Do what:

1. Check host readiness for `qoder-agent-sdk` and
   `QODER_PERSONAL_ACCESS_TOKEN` without printing or storing secret values.
2. If ready, run one bounded smoke task through `run_host_owned_qoder_smoke()`.
3. Persist compact `HostSchedulerRunEvidence` and scheduler-derived trajectory
   projection.
4. Inspect evidence for provider, host invocation, run count, stop reason,
   output refs, permission-review count, and authority split.
5. If not ready, record deterministic readiness evidence and keep the gate
   closed only if the failure occurs before scheduler mutation and without
   credential leakage.

Why first:

The wrapper and helper are now in place. A live or readiness-proven smoke is
the smallest next step that validates the path against the real host runtime
environment.

## Candidate B — Host Evidence Consumer / UX Surface

Do what:

1. Add a read-only consumer for host-run evidence JSON.
2. Surface host invocation, provider, stop reason, output refs, and authority
   split in the host UI.

Why not first:

The evidence product is stable enough, but a real readiness/live smoke should
come first so the consumer is not designed only around mocked evidence.

## Candidate C — Scheduler Daemon Preparation

Do what:

1. Define queue polling, retry, timeout, cancellation, and event-log rotation.
2. Promote the one-shot host runner toward a durable loop.

Why not first:

Daemon behavior should wait until the real one-shot Qoder path has at least
one live or readiness-proven smoke outcome.

## Candidate D — Real Sandbox Provider Contract Expansion

Do what:

1. Select git-worktree, Docker, or remote VM as the first real isolation path.
2. Bind sandbox allocation to edit leases, scratch paths, cleanup, and
   artifact recovery.

Why not first:

Real sandboxing is needed before larger-scale agent groups, but the current
runtime path still needs a live/readiness smoke first.

## Current Recommendation

Recommended next gate:

```text
Credentialed Live Qoder Smoke
```

The next slice should stay narrow:

1. Readiness check for SDK/auth without exposing credentials.
2. One bounded smoke run only when host readiness is satisfied.
3. Compact evidence/projection inspection.
4. Deterministic negative-path evidence when host readiness is absent.
5. No MCP real-provider exposure.
6. No daemon, UI consumer, real sandbox, or multi-agent scheduling policy.
