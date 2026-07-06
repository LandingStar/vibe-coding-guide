# Planning Gate - Local Work Lane Split Preflight

Date: 2026-07-03

Status: COMPLETED

## Purpose

Make agents more proactive about splitting substantial Local Work into lanes
when a task has distinct context streams, while keeping static instruction
surfaces lightweight.

The immediate issue came from a test task that naturally separated into backend,
frontend, and validation streams but was still recorded as one serial lane.

## Scope

- Add a reusable Lane Split Preflight standard under `design_docs/tooling/`.
- Update `AGENTS.md`, bootstrap `AGENTS.md`, generated instruction text, and
  Host UX prompt text to point at the standard instead of embedding full lane
  split criteria.
- Preserve existing Local Work Trajectory mutation authority and worker report
  rules.
- Add focused tests proving the standard is discoverable and generated
  instructions use the lightweight pointer.

## Non-Goals

- Do not change scheduler runtime behavior.
- Do not implement new worker execution or lane ordering logic.
- Do not make every large task multi-lane by default.
- Do not move detailed criteria into `AGENTS.md`.

## Acceptance Criteria

1. `design_docs/tooling/local-work-lane-splitting/lane-split-preflight.md`
   defines trigger criteria, decision steps, and acceptance behavior.
2. `AGENTS.md` and generated instructions only contain a short pointer to the
   standard.
3. Bootstrap assets include the same pointer and standard documents.
4. Focused tests pass.

## Completion Notes

Implemented on 2026-07-03.

Added the reusable standard:

- `design_docs/tooling/local-work-lane-splitting/README.md`
- `design_docs/tooling/local-work-lane-splitting/lane-split-preflight.md`

Updated the root and bootstrap `AGENTS.md`, generated instruction text, and
Host UX AI chat prompt so they only point to the standard. The full split
criteria now live in the tooling standard instead of static instruction
surfaces.

Validation passed:

```text
python -m pytest tests/test_instructions_generator.py tests/test_doc_loop_prompts.py -q
60 passed

python -m compileall -q src tests

npm test -- --test-name-pattern "ai chat prompt|parseAssistantAction"
70 passed

git diff --check -- <touched lane-splitting files>
```

`git diff --check` reported no whitespace errors; it only emitted Windows
LF/CRLF normalization warnings for already-edited tracked files.
