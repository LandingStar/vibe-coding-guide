# Planning Gate: Full Release Electron Smoke Evidence Run

> Date: 2026-06-20
> Status: COMPLETED

## Context

Direction analysis:

- `design_docs/electron-smoke-release-validation-promotion-direction-analysis.md`

Completed prerequisite gate:

- `design_docs/stages/planning-gate/2026-06-20-electron-smoke-release-checklist-preprovisioned-gate.md`

The release script now runs the Electron smoke gate by default after VSIX
packaging when a repo-local VS Code `1.93.1` executable has already been
provisioned. Focused tests and direct gate helpers have passed. The remaining
release confidence gap is proving the gate inside one full release run.

## Scope

1. Run the full release script with the existing canonical version:

   ```powershell
   .\.venv\Scripts\python.exe scripts/release.py --no-isolation
   ```

2. Confirm the release flow crosses:
   - wheel build;
   - full pytest;
   - VSIX packaging;
   - pre-provisioned Electron smoke release gate;
   - release zip packaging.
3. Record the resulting release artifacts and Electron smoke summary.
4. Update review/status documents with evidence.
5. Commit only intended project documents and release artifact changes.

## Non-Goals

- Do not increment package versions.
- Do not add CI-managed VS Code cache behavior.
- Do not add implicit VS Code download behavior to release validation.
- Do not commit `output/electron/`, `output/playwright/`, local executable
  support files, node modules, local config, or other machine-local state.
- Do not broaden Electron smoke assertions beyond the existing release gate.

## Acceptance

1. `scripts/release.py --no-isolation` exits successfully.
2. Release output reports `Electron smoke: PASSED`.
3. Electron smoke summary remains:
   - `ok=true`;
   - `panelVisible=true`;
   - scheduler root/payload present;
   - `lanes=4`;
   - `events=6`;
   - `relations=12`.
4. Current versioned wheel, VSIX, and release zip artifacts are refreshed or
   confirmed present.
5. Review/status docs record the release evidence and residual risk.

## Close Summary

The full release path was exercised with the existing canonical version
`0.9.8`.

The first run exposed a stale official-instance pack lock:

- expected:
  `sha256:22bdd58ffa315a31313f3ff718ec74d59a9d1824b498a1702213fb5f6ddf613f`
- actual:
  `sha256:6ef818671ce52695b1a7f81528ab0a2a395a5761c4ee9e986f3c9e4ba2913755`

That was corrected with the existing `pack_lock` MCP tool for
`doc-loop-vibe-coding`, then verified with `pack_verify` and the previously
failing focused test.

The follow-up full release run succeeded and crossed:

1. wheel build;
2. full pytest;
3. VSIX packaging;
4. pre-provisioned Electron smoke release gate;
5. release zip packaging.

## Validation Result

Passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_error_recovery.py::TestPipelineInitResilience::test_no_warnings_when_all_packs_valid -q
1 passed
```

```text
pack_verify(pack_name="doc-loop-vibe-coding")
ok=1, mismatch=0, missing_lock=0, missing_pack=0
```

```text
.\.venv\Scripts\python.exe scripts/release.py --no-isolation
```

The release run reported:

```text
1754 passed, 3 skipped
Electron smoke: PASSED
Zip: release\doc-based-coding-v0.9.8.zip
```

Electron smoke summary remained:

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

Artifact evidence:

- `dist/doc_based_coding_runtime-0.9.8-py3-none-any.whl`
- `dist/doc_loop_vibe_coding-0.9.8-py3-none-any.whl`
- `vscode-extension/doc-based-coding-0.2.1.vsix`
- `release/doc_based_coding_runtime-0.9.8-py3-none-any.whl`
- `release/doc_loop_vibe_coding-0.9.8-py3-none-any.whl`
- `release/doc-based-coding-0.2.1.vsix`
- `release/doc-based-coding-v0.9.8.zip`

## Boundary Checks

- Runtime, instance, and VSIX versions were not incremented.
- The release script still does not download VS Code.
- `output/electron/`, `output/playwright/`, local executable support files,
  node modules, local Codex config, and other machine-local state remain outside
  the intended commit.
- The Electron smoke release gate still depends on pre-provisioned VS Code
  `1.93.1`.

## Residual Risk

The release gate is now proven by a full local release run, but it remains a
local pre-provisioned gate. CI-managed cache, offline executable provenance, and
checksum source-of-truth remain deferred to the later promotion line in
`design_docs/electron-smoke-release-validation-promotion-direction-analysis.md`.
