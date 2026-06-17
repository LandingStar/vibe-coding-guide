# Planning Gate — Credentialed Live Qoder Smoke

> Date: 2026-06-17
> Status: READY-FOR-CLOSE-REVIEW

## Trigger

`design_docs/stages/planning-gate/2026-06-17-host-owned-qoder-smoke-runner-helper.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/host-owned-qoder-smoke-runner-helper-followup-direction-analysis.md`

This gate attempts the first credentialed host-owned Qoder smoke through the
existing helper. It explicitly allows a readiness-negative outcome when the
local host does not have the SDK or auth token available, as long as the failure
is deterministic, pre-scheduler, and credential-safe.

## Problem

The project now has a repeatable helper:

```text
run_host_owned_qoder_smoke()
QoderSDKQueryClient
run_host_runtime_dogfood_harness()
HostSchedulerRunEvidence
```

The remaining unknown is whether the local host environment is ready for a real
credentialed Qoder smoke. Running this by hand would risk leaking credentials
or producing ad hoc evidence, so the live attempt needs a narrow gate.

## Authority Inputs

- `design_docs/host-owned-qoder-smoke-runner-helper-followup-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-06-17-host-owned-qoder-smoke-runner-helper.md`
- `review/host-owned-qoder-smoke-runner-helper-2026-06-17.md`
- `design_docs/stages/planning-gate/2026-06-17-controlled-real-qoder-wrapper-spike.md`
- `review/controlled-real-qoder-wrapper-spike-2026-06-17.md`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

## Scope

### Slice 1 — Readiness Check

Check host readiness without exposing secrets:

1. Determine whether `qoder-agent-sdk` can be imported in the active Python
   runtime.
2. Determine whether `QODER_PERSONAL_ACCESS_TOKEN` is present without printing
   or persisting its value.
3. Call wrapper readiness only through project-owned error objects.
4. Record a compact readiness result in review evidence.

### Slice 2 — Bounded Live Smoke When Ready

If readiness is satisfied:

1. Run `run_host_owned_qoder_smoke()` once.
2. Use max-turns / bounded policy.
3. Keep permissions denied or surfaced; do not silently approve tool requests.
4. Persist compact `HostSchedulerRunEvidence`.
5. Refresh scheduler-derived trajectory projection.
6. Inspect evidence for provider, host invocation, run count, stop reason,
   output refs, permission-review count, and authority split.

### Slice 3 — Deterministic Negative Outcome When Not Ready

If readiness is not satisfied:

1. Confirm no evidence JSON is written.
2. Confirm no scheduler projection is written.
3. Confirm scheduler snapshot task state remains `proposed` if the helper
   initialized the smoke snapshot.
4. Record the stable readiness failure kind without raw SDK logs or secrets.

## Non-Goals

This gate does not:

1. Expose Qoder through MCP.
2. Add a scheduler daemon.
3. Add UI evidence consumption.
4. Add real sandboxing.
5. Add retry, cancellation, queue polling, or event-log rotation.
6. Print, store, or commit raw credentials.
7. Store raw transcripts in evidence, scheduler state, Local Work Trajectory,
   prompts, or review docs.

## Acceptance Criteria

The gate may close only when:

1. Host readiness is checked without credential exposure.
2. Either:
   - a live smoke run succeeds and writes compact evidence/projection, or
   - a readiness-negative outcome is recorded before scheduler mutation.
3. Any generated evidence is compact and contains no raw credentials or raw
   transcripts.
4. MCP fake-only behavior remains unchanged.
5. Review evidence records exact commands and outcomes.
6. Focused validation / hygiene checks pass.

## Implementation Notes

### 2026-06-17 — Host Readiness Check

Executed a credential-safe readiness check in the active `.venv`:

```text
sdk_importable=False
token_present=False
ready=False
error_kind=authentication_failed
raw_error_type=MissingEnvironmentVariable
```

No token value was printed or persisted. The active host environment is not
ready for a credentialed live Qoder smoke because:

1. `qoder_agent_sdk` is not importable.
2. `QODER_PERSONAL_ACCESS_TOKEN` is not present in the process environment.

The wrapper fail-closed at readiness time with:

```text
QoderRuntimeError(error_kind="authentication_failed",
                  raw_error_type="MissingEnvironmentVariable")
```

Pre-scheduler artifact check:

```text
.codex/scheduler/qoder-smoke-state.json -> absent
.codex/scheduler/evidence/qoder-smoke.json -> absent
.codex/progress-graph/scheduler-work-trajectory.json -> absent
```

This is a readiness-negative outcome rather than a live success. It still
satisfies the negative branch of this gate because failure occurred before
scheduler execution and without credential exposure.

Close-review evidence:

- `review/credentialed-live-qoder-smoke-2026-06-17.md`
