# Worker Report Readback Follow-up Direction Analysis

## Document Position

This direction analysis follows the completed worker report readback slice:

- `design_docs/stages/planning-gate/2026-07-09-worker-report-trajectory-suggestion-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-exchange-communication-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-runtime-invocation-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-08-scheduler-event-readback-envelope.md`
- `design_docs/tooling/Log-like Record Standard Draft.md`

It selects the next narrow log-like record alignment gate. It is not an
implementation gate and does not change runtime behavior by itself.

Date: 2026-07-09

## Current Baseline

The scheduler, runtime invocation, ExchangeArtifact communication, and worker
report / trajectory suggestion families now have read-only draft envelope
projections:

- `scheduler_event_to_readback_envelope()`
- `runtime_invocation_record_to_readback_envelope()`
- `exchange_artifact_record_to_readback_envelope()`
- `worker_report_to_readback_envelope()`
- shared `LogRecordRef`
- typed subject/input/output/evidence refs
- normalized summary/reason/next-hint fields
- explicit raw payload non-persistence declarations

This gives the current leader-worker loop a coherent readback story across
scheduling, runtime execution, communication, and worker-authored status
suggestions without changing mutation authority.

## Candidate 1 - Validation / Doctor / Self-check Receipt Envelope

### What It Would Do

Add a read-only draft envelope projection for validation, doctor, and
self-check receipts.

Expected fields:

- command/check identity, profile, workspace root, and host surface
- pass/warn/fail status and blocking severity
- remediation next hints
- machine-checked vs instruction-layer constraint refs
- relevant config/tool exposure refs
- explicit non-exposure of raw secret-bearing environment values

### Why It Is Valuable

Release, install, MCP exposure, workspace relay, and runtime provider
troubleshooting all currently depend on several receipt shapes. A compact
envelope would make these checks more readable and easier to surface in future
monitoring UI without changing validation semantics.

### Source Basis

- `docs/self-check-doctor-contract.md`
- `src/runtime/orchestration/self_check.py`
- `src/workflow/pipeline.py`
- `src/mcp/tools.py`
- `tests/test_cli.py`
- `tests/test_mcp_tools.py`

### Scope Boundary

This should not change validation rules, doctor profiles, install behavior,
provider readiness checks, or MCP exposure behavior.

## Candidate 2 - UI Screenshot / Host Evidence Envelope

### What It Would Do

Add readback envelopes for UI screenshot evidence and host/sandbox evidence
receipts.

### Why It Is Valuable

Visual validation and host evidence are important for release confidence and
debugging, especially after UI-related work.

### Scope Boundary

This should not start browsers, run screenshots, clean sandboxes, or mutate
host evidence. It should only project existing evidence products.

## Candidate 3 - Worker Report Readback CLI/MCP Inspection Surface

### What It Would Do

Expose the new worker report readback projection through CLI and/or MCP
inspection commands.

### Why It Is Valuable

The projection exists as a runtime helper, but operators may need a direct
inspection command for `.dbc/agent-output/report-*.json`.

### Scope Boundary

This should not consume `trajectory_update` or mutate Local Work Trajectory.

## Recommendation

Default next gate: **Validation / Doctor / Self-check Receipt Readback
Envelope**.

Reason:

- It is the highest-leverage remaining log-like family for install/release and
  workspace health.
- It has clear existing source products and tests.
- It can improve operational readability without changing validation behavior.

Worker report CLI/MCP inspection is useful, but it should follow only if there
is immediate pressure to expose this projection to operators before broader
receipt alignment.

## Proposed Next Gate

```text
Validation / Doctor / Self-check Receipt Readback Envelope
```

Acceptance outline:

- Add a read-only projection from existing validation/doctor/self-check result
  structures into the draft envelope.
- Cover ok, warning, blocking, and missing-tool/config cases.
- Preserve current validation semantics and doctor profile behavior.
- Do not expose raw environment values or secrets.
- Do not mutate workspace config, MCP registration, provider state, or Local
  Work Trajectory in this gate.
