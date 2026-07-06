# Planning Gate - User-Requested Lane Change Protocol

Date: 2026-07-03

Status: COMPLETED

## Purpose

Define how agents should respond when a user requests adding, splitting,
merging, or adjusting Local Work lanes.

The goal is to make user lane requests actionable without turning them into
blind commands. The agent should analyze the intended work boundary, accept good
lane suggestions, and propose a better mapping when the requested split does not
match the actual work structure.

## Scope

- Add a reusable user-requested lane change protocol under
  `design_docs/tooling/local-work-lane-splitting/`.
- Link it through the lane-splitting directory index.
- Ensure static instruction surfaces point to the shared standard instead of
  duplicating the protocol.
- Add focused tests proving the protocol is discoverable.

## Non-Goals

- Do not add runtime scheduling policy.
- Do not implement manual lane drag/reorder UI.
- Do not make user requests override Local Work Trajectory authority rules.
- Do not allow bounded workers to mutate Local Work Trajectory directly.

## Acceptance Criteria

1. `user-requested-lane-change.md` defines analysis steps, default behavior, and
   mutation guidance.
2. The top-level lane-splitting standard links both protocols.
3. Root and bootstrap instruction surfaces point agents to the standard when
   user-requested lane changes arise.
4. Focused tests pass.

## Completion Notes

Implemented on 2026-07-03.

Added:

- `design_docs/tooling/local-work-lane-splitting/user-requested-lane-change.md`
- bootstrap copy under
  `doc-loop-vibe-coding/assets/bootstrap/design_docs/tooling/local-work-lane-splitting/`

The protocol covers how agents should analyze user lane requests, accept
reasonable lane changes, propose better mappings when needed, and preserve
leader/main/supervisor authority over `localTrajectory` mutation.

Validation passed:

```text
python -m pytest tests/test_instructions_generator.py tests/test_doc_loop_prompts.py -q
60 passed

python -m compileall -q src tests

npm test -- --test-name-pattern "ai chat prompt|parseAssistantAction"
70 passed
```
