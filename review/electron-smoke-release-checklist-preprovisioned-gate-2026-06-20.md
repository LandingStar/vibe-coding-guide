# Review - Electron Smoke Release Checklist Pre-Provisioned Gate

> Date: 2026-06-20
> Planning Gate: `design_docs/stages/planning-gate/2026-06-20-electron-smoke-release-checklist-preprovisioned-gate.md`

## Summary

Reviewed the release-script promotion of Electron smoke into a pre-provisioned
release checklist gate.

The implementation keeps VS Code provisioning explicit and outside normal
build/test paths. A full release now runs Electron smoke by default after VSIX
packaging and before release zip packaging, but only after a local executable
and manifest preflight passes. Operators can explicitly bypass the gate with
`--skip-electron-smoke`.

## Changed Files

- `scripts/release.py`
- `tests/test_release_versioning.py`
- `design_docs/stages/planning-gate/2026-06-20-electron-smoke-release-checklist-preprovisioned-gate.md`

## Behavior

Default release flow now includes:

```text
Step 4: Running Electron smoke release gate...
```

The gate checks:

- `output/electron/vscode-executable/Code.exe`;
- `output/electron/vscode-executable/manifest.json`;
- manifest `version == 1.93.1`;
- manifest `target_executable` consistency when provided.

Then it runs:

```powershell
npm run test:electron:smoke --prefix vscode-extension
```

and asserts the smoke summary:

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

Dry-run reports the planned gate and the remediation command but does not
require the local executable to exist:

```powershell
npm run provision:electron:vscode --prefix vscode-extension -- provision 1.93.1
```

Explicit skip:

```powershell
python scripts/release.py --skip-electron-smoke
```

## Validation

```text
.\.venv\Scripts\python.exe -m pytest tests/test_release_versioning.py -q
26 passed
```

```text
node --test vscode-extension/dist/test/electronProvisioning.test.js
4 passed
```

```text
node --test vscode-extension/dist/test/electronWebviewRunner.test.js
3 passed
```

```text
.\.venv\Scripts\python.exe scripts/release.py --dry-run
```

Dry-run output includes the Electron smoke release gate, preflight paths,
`npm run test:electron:smoke --prefix vscode-extension`, and the provisioning
remediation command.

```text
.\.venv\Scripts\python.exe scripts/release.py --dry-run --skip-electron-smoke
```

Dry-run output includes the explicit skip step and does not include the smoke
command.

```text
.\.venv\Scripts\python.exe -c "... release._run_electron_smoke_release_gate(dry_run=True) ..."
```

Preflight output:

```text
Pre-provisioned VS Code executable ready: version=1.93.1, executable=output\electron\vscode-executable\Code.exe
```

```text
.\.venv\Scripts\python.exe -c "... release._run_electron_smoke_release_gate() ..."
```

The real gate returned exit code `0`.

```text
.\.venv\Scripts\python.exe -c "... release._assert_electron_smoke_summary() ..."
Electron smoke summary assertions passed: output\electron\webview-runner-smoke\electron-webview-smoke-summary.json
```

## Boundary Checks

- `scripts/release.py` does not call `provision-electron-vscode.mjs`.
- `scripts/release.py` does not reference `downloadAndUnzipVSCode`.
- Dry-run remains plan-only for Electron smoke preflight.
- Full release now fails closed when the pre-provisioned executable or manifest
  is missing, unless `--skip-electron-smoke` is explicitly supplied.
- `output/electron/` remains uncommitted local evidence/support state.

## Residual Risk

This is still a local pre-provisioned gate. CI-managed cache, offline archive
provenance, and checksum source-of-truth remain deferred to a later promotion
slice.
