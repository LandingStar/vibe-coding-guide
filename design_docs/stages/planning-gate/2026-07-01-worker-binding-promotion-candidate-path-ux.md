# Planning Gate - Worker-Binding Promotion Candidate Path UX

Date: 2026-07-01

Status: COMPLETED

## Purpose

Close the small usability gap found during post-completion validation of
`worker-binding inspect-promotion-candidates`: relative runtime invocation log
paths are project-root relative through the CLI root resolver, so operators need
clear guidance to run from the intended workspace or pass an absolute path.

## Scope

- Clarify CLI help for `worker-binding inspect-promotion-candidates`.
- Clarify the OpenCode provisioning guide.
- Add focused CLI regression coverage for relative path behavior.
- Keep the readback helper and promotion authority model unchanged.

## Non-Goals

- Do not change project-root discovery semantics.
- Do not add auto promotion.
- Do not mutate provider, scheduler, delivery, runtime invocation, or Local
  Work Trajectory state from readback.
- Do not add MCP, doctor/self-check, UI, private storage, or compact.

## Acceptance Criteria

1. CLI help states that relative `--runtime-invocation-log-path` values resolve
   against the detected project root/current workspace.
2. Docs tell operators to run from the intended workspace or pass an absolute
   audit path.
3. Focused CLI tests cover project-root relative path usage.
4. Focused tests, `py_compile`, and `git diff --check` pass.

## Completion Notes

Implemented on 2026-07-01.

Changes:

- `worker-binding inspect-promotion-candidates --help` now states that relative
  `--runtime-invocation-log-path` values resolve against the detected project
  root/current workspace.
- `docs/opencode-host-provisioning-check-guide.md` now tells operators to run
  from the intended workspace or pass an absolute audit path when inspecting
  another workspace.
- Focused CLI coverage now checks the help text and continues to validate
  project-root relative path usage through a workspace-local fixture.

Validation passed:

```text
python -m pytest tests/test_cli.py -k "inspect_promotion_candidates" -q
3 passed, 173 deselected

python -m py_compile src/__main__.py tests/test_cli.py

git diff --check -- src/__main__.py tests/test_cli.py docs/opencode-host-provisioning-check-guide.md "design_docs/Project Master Checklist.md" design_docs/stages/planning-gate/2026-07-01-worker-binding-server-api-promotion-readback-closure.md design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-candidate-path-ux.md .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` reported no whitespace errors. It only emitted Windows
LF/CRLF normalization warnings for already-edited tracked files.
