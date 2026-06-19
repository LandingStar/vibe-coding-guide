# Review - Full Release Electron Smoke Evidence Run

> Date: 2026-06-20
> Planning Gate: `design_docs/stages/planning-gate/2026-06-20-full-release-electron-smoke-evidence-run.md`

## Summary

Reviewed the first full release run after promoting Electron smoke into the
default release checklist.

The release path is now proven end-to-end with the pre-provisioned VS Code
`1.93.1` executable: wheel build, full pytest, VSIX packaging, Electron smoke
release gate, and release zip packaging all completed successfully.

## Changed Files

- `.codex/pack-lock.json`
- `.codex/checkpoints/latest.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `release/doc-based-coding-0.2.1.vsix`
- `release/doc_based_coding_runtime-0.9.8-py3-none-any.whl`
- `release/doc_loop_vibe_coding-0.9.8-py3-none-any.whl`
- `release/RELEASE_NOTE.md`
- `release/COMMIT_MESSAGE_CN.md`
- `release/COMMIT_MESSAGE_EN.md`
- `design_docs/stages/planning-gate/2026-06-20-full-release-electron-smoke-evidence-run.md`

## Evidence

The first full release attempt failed during full pytest because
`doc-loop-vibe-coding` had a stale integrity lock. The lock expected:

```text
sha256:22bdd58ffa315a31313f3ff718ec74d59a9d1824b498a1702213fb5f6ddf613f
```

The current official instance content produced:

```text
sha256:6ef818671ce52695b1a7f81528ab0a2a395a5761c4ee9e986f3c9e4ba2913755
```

After refreshing the official instance lock through the existing `pack_lock`
MCP tool, focused validation passed:

```text
pack_verify(pack_name="doc-loop-vibe-coding")
ok=1, mismatch=0, missing_lock=0, missing_pack=0
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_error_recovery.py::TestPipelineInitResilience::test_no_warnings_when_all_packs_valid -q
1 passed
```

The full release command then passed:

```text
.\.venv\Scripts\python.exe scripts/release.py --no-isolation
1754 passed, 3 skipped
Electron smoke: PASSED
Zip: release\doc-based-coding-v0.9.8.zip
```

Electron smoke summary:

```json
{
  "ok": true,
  "panelVisible": true,
  "hasSchedulerTrajectoryRoot": true,
  "hasSchedulerTrajectoryPayload": true,
  "lanes": 4,
  "events": 6,
  "relations": 12
}
```

Refreshed local artifacts:

| Artifact | Size |
|---|---:|
| `release/doc-based-coding-v0.9.8.zip` | 715499 bytes |
| `release/doc_based_coding_runtime-0.9.8-py3-none-any.whl` | 368837 bytes |
| `release/doc_loop_vibe_coding-0.9.8-py3-none-any.whl` | 67940 bytes |
| `release/doc-based-coding-0.2.1.vsix` | 244713 bytes |
| `vscode-extension/doc-based-coding-0.2.1.vsix` | 244713 bytes |

After release notes and commit-message drafts were updated, the release package
was regenerated with:

```text
.\.venv\Scripts\python.exe scripts/release.py --no-isolation --skip-tests
Electron smoke: PASSED
Zip: release\doc-based-coding-v0.9.8.zip
```

The regenerated zip includes `RELEASE_NOTE.md` with the Electron smoke release
gate section and the full-run validation count.

## Boundary Checks

- No version bump was performed.
- The release script still requires pre-provisioned VS Code `1.93.1`.
- No implicit VS Code download path was added to release validation.
- `output/electron/`, `output/playwright/`, local executable support files,
  node modules, and local Codex config remain outside the intended commit.
- The tracked release wheel and VSIX artifacts were refreshed; the release zip
  remains an ignored local artifact.

## Residual Risk

The release gate is proven locally, but CI-managed pinned VS Code cache and
offline executable provenance remain deferred. The terminal also printed
non-fatal VS Code host noise after the smoke run; the release script exit code
was `0`, and summary assertions passed.
