# Planning Gate - Active Lane Ownership Delivery Consumption Smoke

Date: 2026-07-01

Status: COMPLETED

## Purpose

Prove the newly closed promotion-to-lane-ownership loop is actually consumed by
subsequent OpenCode continuous-worker delivery selection.

The platform now supports explicit promotion from `server_api_created` session
to continuous worker binding, optional lane ownership claim, and explicit lane
ownership activation after successful delivery evidence. Existing delivery code
already checks lane ownership when resolving continuous worker bindings. This
gate adds the positive smoke evidence that an `active` lane ownership permits
the later delivery to use the promoted continuous worker binding.

## Scope

- Add focused runtime smoke coverage for:
  - server/API-created session promotion into a continuous worker binding;
  - lane ownership claim and activation for that promoted binding;
  - subsequent OpenCode delivery supervisor selection using that binding;
  - runtime invocation audit and delivery lease evidence showing the binding
    was consumed.
- Keep the implementation path provider-free by using the existing recording
  OpenCode client test double.
- Update docs, Checklist, and trajectory.

## Non-Goals

- Do not run OpenCode or any provider.
- Do not change scheduler readiness strategy.
- Do not change delivery selection policy beyond test coverage.
- Do not add automatic promotion or automatic lane ownership activation.
- Do not add MCP, doctor/self-check, UI, private storage allocation, auto
  compact, or `llm-auto`.
- Do not mutate Local Work Trajectory from worker processes.

## Acceptance Criteria

1. The smoke first promotes a `server_api_created` session into a continuous
   worker binding.
2. The smoke claims and activates lane ownership for the promoted binding.
3. The next OpenCode delivery uses the continuous worker binding host session.
4. Runtime invocation audit records `session_selector_source=
   continuous_worker_binding`.
5. Delivery lease and binding reuse evidence are recorded for the promoted
   binding.
6. Focused tests, `py_compile`, and `git diff --check` pass.

## Completion Notes

Implemented on 2026-07-01.

Added focused runtime smoke:

```text
test_opencode_delivery_supervisor_consumes_active_promoted_lane_ownership
```

The smoke:

1. promotes a server/API-created OpenCode session into a continuous worker
   binding;
2. claims lane ownership for the promoted binding;
3. activates that ownership using compact first-success delivery evidence;
4. runs the OpenCode delivery supervisor with continuous-worker lookup enabled
   and a recording OpenCode client;
5. proves the runtime request used the promoted binding's host session;
6. proves runtime invocation audit recorded
   `session_selector_source=continuous_worker_binding`;
7. proves binding reuse and delivery lease evidence were recorded for the
   promoted binding.

No provider process is executed. The test uses the existing
`_RecordingOpenCodeCliClient` seam.

Validation passed:

```text
python -m py_compile tests/test_runtime_orchestration.py

python -m pytest tests/test_runtime_orchestration.py -k "active_promoted_lane_ownership" -q
1 passed, 449 deselected

python -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor_uses_continuous_worker_binding or active_promoted_lane_ownership or suspended_lane_ownership or worker_binding_blocks_same_session or opencode_bounded_loop_reuses_same_continuous_worker" -q
5 passed, 445 deselected

python -m pytest tests/test_runtime_orchestration.py -k "lane_ownership or continuous_worker_binding or server_api_created_session_promotion" -q
26 passed, 424 deselected

git diff --check -- tests/test_runtime_orchestration.py docs/opencode-host-provisioning-check-guide.md "design_docs/Project Master Checklist.md" design_docs/stages/planning-gate/2026-07-01-active-lane-ownership-delivery-consumption-smoke.md .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` reported no whitespace errors. It only emitted Windows
LF/CRLF normalization warnings for already-edited tracked files. A separate
tailing-whitespace scan over this gate and the OpenCode provisioning guide
returned no matches.
