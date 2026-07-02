# Planning Gate - Compact Context Hydration Smoke

Date: 2026-07-02

Status: COMPLETED

## Purpose

Prove that an OpenCode continuous-worker delivery can hydrate a project-owned
compact context bundle into the runtime request, not only carry the bundle ref
through audit metadata.

The previous carry-over smoke proved `compact_context_ref`,
`mailbox_cursor_ref`, and `worker_report_refs` reach OpenCode delivery
boundaries. This gate proves the runtime adapter can resolve a
`dbc://continuous-worker-context/...` ref and add a compact, clearly labelled
continuity block to the OpenCode worker instruction.

## Scope

- Add OpenCode adapter hydration for `dbc://continuous-worker-context/...`
  refs.
- Keep the compact bundle as project-owned context, not provider-owned session
  truth.
- Fail closed if the ref points to a missing or invalid compact bundle.
- Add provider-free smoke coverage using the recording OpenCode client seam.
- Update docs, Checklist, and Local Work Trajectory.

## Non-Goals

- Do not run OpenCode or any provider.
- Do not change compact bundle schema.
- Do not add `llm-auto` compact policy, mailbox consumption, report
  consumption, private storage, MCP tools, UI, or scheduler strategy changes.
- Do not persist raw transcript text or secret values.

## Acceptance Criteria

1. A focused runtime smoke builds a compact context bundle, compacts the
   continuous worker binding to that bundle ref, and runs one OpenCode delivery.
2. The outgoing `OpenCodeCliRequest.instruction` includes a labelled compact
   continuity context block with summary, key decisions, current state,
   artifact refs, mailbox cursor, and worker report refs.
3. Runtime invocation audit still records compact ref, mailbox cursor, worker
   report refs, and audit refs.
4. Missing/unsupported compact context refs fail closed before provider success.
5. Focused tests, `py_compile`, and `git diff --check` pass.

## Completion Notes

Implemented on 2026-07-02.

OpenCode continuous-worker delivery now hydrates project-owned compact context
bundles when the selected binding has a `compact_context_ref` beginning with:

```text
dbc://continuous-worker-context/
```

The OpenCode runtime adapter resolves the ref under
`.codex/runtime/continuous-worker-contexts/` by default, reads the compact
bundle, and appends a labelled `Continuous worker compact context:` block to
the outgoing `OpenCodeCliRequest.instruction`. The block can include summary,
current state, key decisions, artifact refs, mailbox cursor, worker report
refs, and the compact context ref. Missing or invalid bundle refs fail closed
before the OpenCode client seam is invoked.

Added focused runtime smokes:

```text
test_opencode_delivery_supervisor_hydrates_compact_context_bundle
test_opencode_delivery_supervisor_fails_closed_on_missing_compact_context_bundle
```

Validation passed:

```text
python -m py_compile src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/runtime_wiring.py src/runtime/orchestration/leader_worker_codex_delivery.py tests/test_runtime_orchestration.py

python -m pytest tests/test_runtime_orchestration.py -k "hydrates_compact_context_bundle or fails_closed_on_missing_compact_context_bundle or carries_continuous_worker_context_refs" -q
3 passed, 450 deselected

python -m pytest tests/test_runtime_orchestration.py -k "continuous_worker_binding or lane_ownership or server_api_created_session_promotion" -q
26 passed, 427 deselected

python -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor_uses_continuous_worker_binding or active_promoted_lane_ownership or hydrates_compact_context_bundle or fails_closed_on_missing_compact_context_bundle" -q
4 passed, 449 deselected

python -m pytest -k smoke -q --color=no
52 passed, 1 skipped, 2236 deselected

git diff --check -- pyproject.toml src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/runtime_wiring.py src/runtime/orchestration/leader_worker_codex_delivery.py src/mcp/tools.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py docs/opencode-host-provisioning-check-guide.md "design_docs/Project Master Checklist.md" design_docs/stages/planning-gate/2026-07-02-pytest-collection-hygiene.md design_docs/stages/planning-gate/2026-07-02-compact-context-hydration-smoke.md design_docs/stages/planning-gate/2026-07-02-next-action-state-source-sync.md .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` reported no whitespace errors; it only emitted Windows
LF/CRLF normalization warnings for already-edited tracked files.
