# Controlled Real Qoder Wrapper Spike Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-17-controlled-real-qoder-wrapper-spike.md`
has reached `COMPLETED`.

The current boundary now proves:

1. `QoderSDKQueryClient` is a host-owned optional Python wrapper behind
   `QoderQueryClient`.
2. The real SDK is dynamically imported only when the host constructs the
   wrapper; `qoder-agent-sdk` is not a hard runtime dependency.
3. Missing SDK, missing auth, malformed stream, SDK auth failures, and
   permission callback requests map to deterministic project-owned outcomes.
4. `run_host_runtime_dogfood_harness()` calls `validate_host_ready()` before
   scheduler execution when a real-wrapper client exposes it.
5. Missing SDK/auth fail before evidence JSON, scheduler projection, or
   scheduler snapshot mutation.
6. MCP `schedulerRunOnceAndProject` remains fake-only.
7. Prompt guidance documents credential hygiene, negative paths, and the
   authority split.

Evidence review:

- `review/controlled-real-qoder-wrapper-spike-2026-06-17.md`

## Candidate A — Host-Owned Qoder Smoke Runner Helper

Do what:

1. Add a repeatable host-owned helper that constructs:
   - minimal Qoder smoke scheduler snapshot;
   - `QoderSDKQueryClient`;
   - `RuntimeHostInvocation(surface="host-authorized-adapter")`;
   - `RuntimeProviderPermissionGrant(provider="qoder", allow_sdk_client=True)`.
2. Run the existing `run_host_runtime_dogfood_harness()` path.
3. Write the same compact `HostSchedulerRunEvidence` and scheduler-derived
   trajectory projection.
4. Support both:
   - live success when host SDK/auth are available;
   - deterministic SDK/auth fail-closed behavior when they are absent.
5. Keep MCP fake-only and keep Local Work Trajectory agent-owned.

Why first:

The wrapper exists, but a live or negative smoke currently requires callers to
manually assemble several host-owned products. A helper makes the next real
runtime check repeatable without prematurely adding daemon or UI behavior.

## Candidate B — Credentialed Live Qoder Smoke

Do what:

1. Install/confirm `qoder-agent-sdk` in the host runtime.
2. Provide `QODER_PERSONAL_ACCESS_TOKEN` through host environment.
3. Run one bounded Qoder smoke task.
4. Inspect compact evidence and projection.

Why not first:

This is valuable, but it should use a stable helper rather than hand-assembled
host wiring. Otherwise the evidence proves local operator skill as much as it
proves the product seam.

## Candidate C — Host Evidence Consumer / UX Surface

Do what:

1. Display host-run evidence JSON in a read-only host panel.
2. Surface provider, host invocation, stop reason, output refs, and authority
   split.

Why not first:

Evidence volume is still thin. The product needs a repeatable smoke runner
before UI consumption becomes meaningful.

## Candidate D — Scheduler Daemon Preparation

Do what:

1. Define polling, retry, cancellation, timeout, queue ownership, and event-log
   rotation.
2. Promote one-shot scheduler execution toward a durable loop.

Why not first:

The one-shot real-provider path has not yet been exercised through a repeatable
host smoke helper. A daemon would multiply failure modes before the single-run
surface is comfortable.

## Candidate E — Real Sandbox Provider Contract Expansion

Do what:

1. Select a real isolation candidate such as git-worktree, Docker, or remote VM.
2. Bind sandbox allocation to edit leases and scratch paths.

Why not first:

Sandboxing is important before larger agent groups, but the real-provider smoke
path should first prove its host SDK/auth and evidence loop.

## Current Recommendation

Recommended next gate:

```text
Host-Owned Qoder Smoke Runner Helper
```

The next slice should stay narrow:

1. Add a host-owned helper around the existing Qoder wrapper and dogfood
   harness.
2. Add deterministic tests using an injected mock Qoder client.
3. Add deterministic fail-closed tests for absent auth/SDK.
4. Update scheduler smoke prompt guidance.
5. Do not expose Qoder through MCP.
6. Do not add daemon behavior, UI evidence consumption, real sandboxing, or
   multi-agent scheduling policy.
