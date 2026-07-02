# Planning Gate - Continuous Worker Context Carry-Over Smoke

Date: 2026-07-01

Status: COMPLETED

## Purpose

Prove that a reused OpenCode continuous worker binding carries the compact
continuity context into delivery, not only the provider session selector.

The previous gates proved promotion, lane ownership activation, and later
OpenCode delivery selection. This gate checks the next narrow contract: when a
binding has compacted context state, mailbox cursor state, and worker report
refs, the delivery host session and compact runtime invocation audit expose
those references for the runtime layer and later review.

## Scope

- Add provider-free smoke coverage for OpenCode delivery using a continuous
  worker binding after compaction.
- Carry these binding fields into the OpenCode host session selector:
  - `compact_context_ref`
  - `mailbox_cursor_ref`
  - `worker_report_refs`
  - `audit_refs`
- Carry the same compact continuity clues into runtime invocation audit
  metadata.
- Update the OpenCode provisioning guide, Checklist, and Local Work Trajectory.

## Non-Goals

- Do not run OpenCode or any provider.
- Do not change delivery selection precedence.
- Do not add automatic compact, `llm-auto`, mailbox consumption, report
  consumption, private worker storage, MCP tools, doctor checks, UI, or
  scheduler strategy changes.
- Do not persist raw transcript text or secret values.
- Do not let worker processes mutate Local Work Trajectory.

## Acceptance Criteria

1. A focused runtime smoke compacts an existing continuous worker binding with
   `compact_context_ref`, `mailbox_cursor_ref`, and `worker_report_refs`.
2. The next OpenCode delivery resolves that binding before the legacy
   OpenCode session ledger.
3. The OpenCode request's `host_session` carries all compact continuity refs.
4. `host_session.to_metadata()` includes all compact continuity refs.
5. Runtime invocation audit metadata records the same compact continuity refs.
6. Focused tests, `py_compile`, and `git diff --check` pass.

## Completion Notes

Implemented on 2026-07-01.

Added compact continuity carry-over to `OpenCodeHostSessionSelector`:

- `mailbox_cursor_ref`
- `worker_report_refs`

The existing continuous-worker binding lookup now copies these fields from the
resolved binding into the host session selector alongside
`compact_context_ref` and `audit_refs`. Runtime invocation audit now records:

```text
continuous_worker_compact_context_ref
continuous_worker_mailbox_cursor_ref
continuous_worker_report_refs
continuous_worker_audit_refs
```

Added focused runtime smoke:

```text
test_opencode_delivery_supervisor_carries_continuous_worker_context_refs
```

The smoke:

1. claims an OpenCode continuous worker binding;
2. compacts that binding with a new compact context ref, mailbox cursor, worker
   report refs, and audit ref;
3. runs one OpenCode delivery supervisor pass with the recording OpenCode
   client seam;
4. proves the outgoing OpenCode request host session carries the compacted refs;
5. proves `host_session.to_metadata()` includes the compacted refs;
6. proves compact runtime invocation audit records the same refs.

No provider process is executed. The test uses the existing
`_RecordingOpenCodeCliClient` seam.

Validation passed:

```text
python -m py_compile src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/leader_worker_codex_delivery.py tests/test_runtime_orchestration.py

python -m pytest tests/test_runtime_orchestration.py -k "carries_continuous_worker_context_refs" -q
1 passed, 450 deselected

python -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor_uses_continuous_worker_binding or active_promoted_lane_ownership" -q
2 passed, 449 deselected

python -m pytest tests/test_runtime_orchestration.py -k "continuous_worker_binding or lane_ownership or server_api_created_session_promotion" -q
26 passed, 425 deselected

python -m pytest tests/test_runtime_orchestration.py -k "carries_continuous_worker_context_refs or opencode_delivery_supervisor_uses_continuous_worker_binding or active_promoted_lane_ownership" -q
3 passed, 448 deselected

Select-String -Path 'design_docs/stages/planning-gate/2026-07-01-continuous-worker-context-carry-over-smoke.md','docs/opencode-host-provisioning-check-guide.md' -Pattern '[ \t]+$'

git diff --check -- src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/leader_worker_codex_delivery.py tests/test_runtime_orchestration.py docs/opencode-host-provisioning-check-guide.md "design_docs/Project Master Checklist.md" design_docs/stages/planning-gate/2026-07-01-continuous-worker-context-carry-over-smoke.md .codex/progress-graph/local-work-trajectory.json
```

The tailing-whitespace scan returned no matches. `git diff --check` reported
no whitespace errors; it only emitted Windows LF/CRLF normalization warnings
for already-edited tracked files.
