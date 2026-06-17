# Planning Gate — Controlled Real Qoder Wrapper Spike

> Date: 2026-06-17
> Status: READY-FOR-CLOSE-REVIEW

## Trigger

`design_docs/stages/planning-gate/2026-06-17-controlled-host-runtime-dogfood-harness.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/controlled-host-runtime-dogfood-harness-followup-direction-analysis.md`

This gate fixes the first real-provider spike after the host-runtime dogfood
harness. It deliberately stays on the host-authorized one-shot path and does not
expand into daemon scheduling, UI consumption, real sandboxing, or MCP
real-provider exposure.

## Problem

The current orchestration runtime has:

```text
QoderQueryClient
QoderAgentRuntimeAdapter
RuntimeProviderPermissionGrant
RuntimeHostInvocation(surface="host-authorized-adapter")
run_host_runtime_dogfood_harness()
HostSchedulerRunEvidence
```

The system can prove fake and mock-Qoder host-authorized runs, but it still has
no controlled wrapper around the real Qoder SDK / CLI SDK. Without a narrow
wrapper spike, the next real-runtime attempt would mix SDK import, credentials,
permission callbacks, scheduler execution, transcript handling, and dogfood
evidence in one large and hard-to-review step.

## Current External SDK Reading

Qoder CLI SDK documentation now exposes both TypeScript and Python SDK surfaces.
The Python SDK is especially relevant to this repository because the current
orchestration runtime is Python.

Reference entry points:

- `https://docs.qoder.com/en/cli/sdk/python/quick-start`
- `https://docs.qoder.com/en/cli/sdk/python/authentication`
- `https://docs.qoder.com/en/cli/sdk/python/references`
- `https://docs.qoder.com/en/cli/sdk/python/permissions`
- `https://docs.qoder.com/en/cli/sdk/quick-start`
- `https://docs.qoder.com/en/cli/sdk/authentication`
- `https://docs.qoder.com/en/cli/sdk/permissions`

The relevant shape for this gate is:

1. `query({ prompt, options })` returns an async iterable of messages.
2. Python `query(prompt=..., options=QoderAgentOptions(...))` returns an
   async stream of messages.
3. `QoderSDKClient` is available for multi-turn sessions; this gate should
   prefer `query()` unless one-shot execution cannot produce required evidence.
4. `options.auth` / `QoderAgentOptions.auth` is required for SDK use.
5. The documented personal access token path is
   `process.env.QODER_PERSONAL_ACCESS_TOKEN`.
6. Python docs also expose `access_token_from_env()`, `access_token()`, and
   `qodercli_auth()`.
7. SDK options include host-facing controls such as working directory,
   max turns, allowed tools, permission mode, MCP servers, hooks, and
   permission callbacks.
8. Permission decision callbacks are part of the SDK-facing option surface, so
   the wrapper must normalize tool / shell / network / file permission events
   instead of approving them internally.

The implementation must re-check the official Qoder documentation before coding
because this is an external, versioned surface.

## Authority Inputs

- `design_docs/controlled-host-runtime-dogfood-harness-followup-direction-analysis.md`
- `design_docs/qoder-runtime-adapter-requirements.md`
- `design_docs/stages/planning-gate/2026-06-17-controlled-host-runtime-dogfood-harness.md`
- `review/controlled-host-runtime-dogfood-harness-2026-06-17.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

## Scope

This gate creates a minimal real Qoder wrapper spike behind the existing
`QoderQueryClient` protocol.

### Slice 1 — Wrapper Boundary And Host Construction

Add a host-owned wrapper surface that:

1. Implements the existing `QoderQueryClient` protocol from the orchestration
   side.
2. Keeps real SDK import / construction outside MCP tools.
3. Requires explicit host construction input, including:
   - auth source or token availability check;
   - working directory;
   - model / profile options when supported;
   - `maxTurns` / bounded run policy when supported.
4. Does not put raw credentials into scheduler state, evidence JSON, logs,
   Local Work Trajectory, or review docs.
5. Fails closed when the SDK package, auth token, or host grant is missing.

Implementation should prefer a Python SDK wrapper because it can implement
`QoderQueryClient` directly with fewer host-language boundaries. A narrow
TypeScript wrapper helper remains allowed only if the Python SDK proves
insufficient for the required evidence. Either way, the contract must stay
behind `QoderQueryClient`.

### Slice 2 — Permission And Failure Normalization

Map real SDK outcomes to existing runtime objects:

1. Success maps to `QoderQueryResult`.
2. SDK unavailable maps to `QoderRuntimeError(error_kind="sdk_unavailable")`.
3. Authentication / token failure maps to
   `QoderRuntimeError(error_kind="authentication_failed")`.
4. Permission denial maps to
   `QoderRuntimeError(error_kind="permission_denied")` or surfaced
   `PermissionRequest`, depending on SDK behavior.
5. Timeout / cancellation maps to stable error kinds when observable.
6. Invalid response shape maps to `QoderRuntimeError(error_kind="invalid_response")`.

Permission callbacks must not silently approve tool / shell / file / network
requests. If the SDK requests permission during this spike, the wrapper should
surface or deny it in a deterministic way that the scheduler can record.

### Slice 3 — Single Bounded Dogfood Run

Run one bounded scheduled task through:

```text
run_host_runtime_dogfood_harness(runtime_provider="qoder")
```

The run must:

1. Use `RuntimeHostInvocation(surface="host-authorized-adapter")`.
2. Use `RuntimeProviderPermissionGrant(provider="qoder", allow_sdk_client=true)`.
3. Keep MCP `schedulerRunOnceAndProject` fake-only.
4. Persist `HostSchedulerRunEvidence`.
5. Refresh scheduler-derived trajectory projection.
6. Keep scheduler state authority in snapshot + scheduler event log.
7. Keep Local Work Trajectory agent-owned and unmutated by scheduler execution.

If live Qoder credentials are not available, the gate may still close only if
the wrapper has deterministic negative-path tests and a documented live-run
procedure. A live success evidence artifact is preferred but not required for
the first spike unless credentials are intentionally supplied by the host.

### Slice 4 — Prompt / Maintenance Guidance

Update the scheduler smoke prompt or add a sibling prompt section explaining:

1. How to run the real wrapper spike when host auth is available.
2. How to inspect evidence JSON without treating it as scheduler state.
3. How to recognize expected auth / SDK-missing failures.
4. How to keep credentials out of committed files, decision logs, review docs,
   and Local Work Trajectory.
5. Why MCP remains fake-only for scheduler execution.

## Non-Goals

This gate does not:

1. Expose qoder execution through MCP.
2. Add opencode or another real runtime.
3. Add a scheduler daemon.
4. Add parallel execution.
5. Add Docker, remote VM, or git-worktree isolation.
6. Add UI evidence consumption.
7. Store raw transcripts in scheduler state, Local Work Trajectory, or evidence
   JSON.
8. Implement broad retry, cancellation, queue polling, or event-log rotation.
9. Promote Qoder internal subagents into project-level scheduler tasks or Local
   Work Trajectory lanes.

## Required Design Decisions

Before implementation, this gate must fix:

1. Whether the first wrapper can be a direct Python SDK wrapper. If not, record
   why a TypeScript helper or process shim is needed.
2. The minimum host input shape for auth, cwd, model/profile, max turns, and
   tool policy.
3. Whether live credentials are expected in the local developer environment, or
   whether this gate accepts negative-path evidence only.
4. Where transcript references are stored if the SDK exposes them.
5. How the wrapper reports permission callbacks without silently granting them.

## Acceptance Criteria

The gate may close only when:

1. The wrapper construction path is host-owned and outside MCP.
2. The wrapper implements or adapts to `QoderQueryClient`.
3. The wrapper requires explicit auth/token availability and does not log or
   commit secrets.
4. Missing SDK/package, missing auth/token, invalid response shape, and
   permission denial/request behavior have deterministic tests or documented
   local smoke evidence.
5. A host-authorized qoder dogfood path can call
   `run_host_runtime_dogfood_harness()` or, when live credentials are absent,
   can prove the same seam fails closed before scheduler state is polluted.
6. `HostSchedulerRunEvidence` remains compact and contains no raw transcript or
   credential material.
7. Scheduler snapshot + event log remain the scheduler authority.
8. Scheduler-derived trajectory projection remains read-only.
9. Agent-owned Local Work Trajectory is not mutated by scheduler execution.
10. MCP `schedulerRunOnceAndProject` still rejects non-fake runtime providers.
11. Prompt / maintenance guidance explains live and negative-path operation,
    credential hygiene, evidence inspection, and the authority split.
12. Focused tests cover the wrapper seam, auth/SDK failure, permission handling,
    dogfood harness integration or fail-closed behavior, and MCP fake-only
    behavior.

Credential, authorization, permission, and rollback checks are hard acceptance
criteria for this gate, not residual risk. The purpose of this spike is to make
real-provider failure modes reviewable before any broader scheduling feature
depends on them.

## Residual Risk After Close

The following may remain after this gate closes:

1. No long-running daemon.
2. No broad retry or timeout policy beyond wrapper-level normalization.
3. No production-grade sandbox.
4. No UI evidence consumer.
5. No multi-agent scheduling policy.
6. Limited real-run evidence if local credentials are intentionally absent.

## Recommended First Implementation Bias

Prefer a direct Python SDK wrapper so small that it can be deleted or replaced
without touching scheduler state, projection code, or MCP. The wrapper should
prove:

```text
host authorization -> QoderQueryClient -> QoderAgentRuntimeAdapter ->
run_host_runtime_dogfood_harness() -> evidence JSON + scheduler projection
```

Anything outside that chain belongs in a later gate.

## Implementation Notes

2026-06-17 implementation pass:

1. Added `src/runtime/orchestration/qoder_sdk_client.py` with
   `QoderSDKQueryClientConfig` and `QoderSDKQueryClient`.
2. The wrapper is a direct Python SDK wrapper behind `QoderQueryClient`; it uses
   dynamic import of `qoder_agent_sdk` and does not add `qoder-agent-sdk` as a
   hard package dependency.
3. Host-owned construction inputs now include auth env var / auth mode, cwd,
   model, max turns, allowed / disallowed tool policy, permission mode, and
   permission request policy.
4. The wrapper normalizes SDK async stream messages into `QoderQueryResult`,
   supports structured final response messages through
   `qoder_query_result_from_response()`, and keeps metadata compact.
5. Missing SDK, missing auth token, malformed stream, SDK auth failures, and
   permission callback behavior now map to deterministic `QoderRuntimeError`
   kinds.
6. Permission callback requests are denied by default. A host can choose
   `permission_request_policy="surface"` to return compact
   `PermissionRequest` evidence, but the wrapper still returns `False` to the
   SDK callback and does not approve the request internally.
7. `QoderSDKQueryClient.validate_host_ready()` provides a pre-scheduler
   fail-closed gate. `run_host_runtime_dogfood_harness()` calls it when present,
   so missing SDK/auth fails before evidence JSON, scheduler projection, or
   scheduler snapshot writes.
8. Prompt guidance was updated in `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   and the bootstrap copy.

Focused validation added:

1. Wrapper negative paths: missing SDK, missing auth, invalid stream, redacted
   SDK auth failure.
2. Wrapper success paths: text stream normalization and structured final
   response normalization.
3. Permission behavior: default deny and explicit surface-without-approval.
4. Host dogfood fail-closed path: real wrapper auth failure leaves evidence,
   scheduler projection, and scheduler snapshot unwritten / unchanged.
