# Live Qoder Runtime Provider Dogfood Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-live-qoder-runtime-provider-dogfood.md`
closed with a host-owned Qoder smoke CLI available through:

```text
doc-based-coding qoder smoke
python -m src qoder smoke
```

Review evidence:

- `review/live-qoder-runtime-provider-dogfood-2026-06-22.md`

## Current Position

The current slice proved the host-owned invocation seam, not a credentialed
live success. The new CLI delegates to existing Qoder smoke helpers and keeps
the authority boundary explicit:

```text
QoderSDKQueryClientConfig
HostOwnedQoderSmokeRunConfig
RuntimeHostInvocation(surface="host-authorized-adapter")
RuntimeProviderPermissionGrant(provider="qoder", allow_sdk_client=True)
run_host_owned_qoder_smoke()
```

The command is credential-safe:

1. it does not accept raw token values;
2. missing SDK/auth fail before Host Evidence or scheduler projection writes;
3. scheduler CLI/MCP surfaces remain fake-runtime-only;
4. scheduler/runtime execution does not mutate agent-owned Local Work
   Trajectory.

Local host status at close remains readiness-negative:

```text
sdk_importable=false
token_present=false
ready=false
error_kind=authentication_failed
```

## Candidate A - Credentialed Live Qoder Success

### Goal

After the host installs `qoder-agent-sdk` and provides supported auth, rerun
the same `doc-based-coding qoder smoke` path and record a credentialed live
success or a more precise live failure class.

### Why Useful

The current CLI fixed repeatability and evidence hygiene, but did not prove
that a real Qoder-backed runtime task can complete. This is the shortest path
to validate the real provider adapter without widening scheduler/MCP authority.

### Boundary

This remains host-owned. It should not make MCP or scheduler operator commands
accept live providers. The gate should capture readiness, evidence paths,
credential redaction, and failure taxonomy only.

## Candidate B - Return To Scheduler Orchestration Without Live Provider

### Goal

Continue the orchestration backend on fake-runtime or host-managed surfaces
while leaving Qoder credential provisioning as an external host readiness task.

Likely next subareas:

1. supervisor/session storage lifecycle beyond readback products;
2. scheduler admission / operator workflow usability around existing durable
   evidence;
3. stricter lifecycle policy, retry, deadline, or cleanup contracts.

### Why Useful

The project can still advance orchestration structure without blocking on local
Qoder credentials. This is safer if the current environment remains
readiness-negative for a while.

### Boundary

Do not treat fake-runtime progress as live-provider proof. Any later live
provider expansion still needs a separate gate.

## Candidate C - Packaging / Release Refresh

### Goal

Regenerate the preview package if the immediate need is distribution of the
Qoder smoke CLI and recently completed scheduler operator closure surfaces.

### Why Useful

The host-owned smoke CLI is a user-facing operator surface. Packaging may be
useful before further backend work if manual dogfood should happen outside the
development workspace.

### Boundary

This should be a packaging-only gate unless new release validation exposes a
real packaging defect.

## Recommendation

My current preference is Candidate B unless the host is ready to provision
Qoder credentials immediately.

Reason:

1. the current Qoder gap is host environment readiness, not an unimplemented
   project surface;
2. the CLI already provides the repeatable path needed for later credentialed
   verification;
3. scheduler/orchestration still has useful fake-runtime-backed work that can
   reduce design risk without depending on a live provider;
4. if host provisioning becomes available, Candidate A can be run as a narrow
   evidence gate without revisiting the CLI design.

## Proposed Next Planning Gate

If host provisioning is available now:

```text
design_docs/stages/planning-gate/2026-06-22-credentialed-live-qoder-success.md
```

Otherwise, open the next scheduler/orchestration planning gate from the current
post-v1.0 candidate set, keeping live provider execution out of scheduler MCP
and Host UX until a dedicated live-provider gate passes.
