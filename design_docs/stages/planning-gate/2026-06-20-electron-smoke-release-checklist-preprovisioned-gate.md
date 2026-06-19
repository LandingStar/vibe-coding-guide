# Planning Gate: Electron Smoke Release Checklist Pre-Provisioned Gate

> Date: 2026-06-20
> Status: COMPLETED

## Context

Direction analysis:

- `design_docs/electron-smoke-release-validation-promotion-direction-analysis.md`

Rendered Electron evidence now exists for the current host surface:

- VS Code executable source: `repo-local (output/electron/vscode-executable)`
- VS Code version: `1.93.1`
- Electron smoke summary: `panelVisible=true`, scheduler root/payload present,
  `lanes=4`, `events=6`, `relations=12`
- screenshot sanity: `1600x1000`, `sampled_unique_colors=38`

This gate promotes the smoke from optional local evidence into the release
checklist, but only when the isolated VS Code executable has already been
provisioned. It must not introduce implicit downloads.

## Scope

1. Add a release validation preflight for:
   - `output/electron/vscode-executable/Code.exe`;
   - `output/electron/vscode-executable/manifest.json`;
   - exact accepted VS Code version;
   - manifest `target_executable` consistency when present.
2. Add an explicit release-script step that runs the existing Electron smoke
   after VSIX packaging and before release zip packaging.
3. Add an explicit release-script skip flag for emergency/operator use.
4. Add focused tests proving:
   - dry-run advertises the Electron smoke gate;
   - missing pre-provisioned executable/manifest fails with a remediation
     command;
   - the release script does not call provisioning/download automation;
   - preflight accepts a valid manifest/executable shape.
5. Update review/status documents at close.

## Non-Goals

- Do not download VS Code from release validation.
- Do not add CI-managed VS Code cache behavior.
- Do not add checksum source-of-truth verification beyond recording/printing
  manifest metadata.
- Do not change the existing Electron smoke runner fixture or webview payload.
- Do not commit `output/electron/` or screenshot artifacts.

## Acceptance

1. Full release flow runs Electron smoke by default after VSIX packaging when
   preflight passes.
2. `--skip-electron-smoke` is available and explicitly reported in dry-run and
   real release output.
3. Missing pre-provisioned executable/manifest returns a non-zero release
   failure with a remediation command:

   ```powershell
   npm run provision:electron:vscode --prefix vscode-extension -- provision 1.93.1
   ```

4. Ordinary `scripts/build.py`, `npm run build`, `npm test`, and
   `npm run test:electron:smoke` still do not call provisioning automation.
5. Focused tests pass.
6. If local pre-provisioned executable is present, the release Electron smoke
   validation step is exercised.

## Close Summary

Implemented the pre-provisioned Electron smoke release gate in
`scripts/release.py`.

The release script now:

1. pins the release Electron smoke executable expectation to VS Code `1.93.1`;
2. checks `output/electron/vscode-executable/Code.exe`;
3. checks `output/electron/vscode-executable/manifest.json`;
4. verifies manifest `version == 1.93.1`;
5. verifies `target_executable` consistency when the manifest provides it;
6. runs `npm run test:electron:smoke` after VSIX packaging and before release
   zip packaging;
7. asserts the smoke summary fields:
   - `ok=true`;
   - `panelVisible=true`;
   - scheduler trajectory root present;
   - scheduler trajectory payload present;
   - `lanes=4`;
   - `events=6`;
   - `relations=12`;
8. exposes `--skip-electron-smoke` as an explicit operator escape hatch.

Dry-run reports the planned gate and remediation command, but does not require
the executable/manifest to exist. Real release execution fails if the
pre-provisioned executable or manifest is missing.

## Validation Result

Passed:

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

The dry-run lists:

- `Run Electron smoke release gate with pre-provisioned VS Code 1.93.1`;
- preflight paths for `Code.exe` and `manifest.json`;
- `npm run test:electron:smoke --prefix vscode-extension`;
- remediation command
  `npm run provision:electron:vscode --prefix vscode-extension -- provision 1.93.1`.

```text
.\.venv\Scripts\python.exe scripts/release.py --dry-run --skip-electron-smoke
```

The dry-run lists `Skip Electron smoke release gate (--skip-electron-smoke)`.

```text
.\.venv\Scripts\python.exe -c "... release._run_electron_smoke_release_gate(dry_run=True) ..."
```

The gate preflight reported:

```text
Pre-provisioned VS Code executable ready: version=1.93.1, executable=output\electron\vscode-executable\Code.exe
```

```text
.\.venv\Scripts\python.exe -c "... release._run_electron_smoke_release_gate() ..."
```

The real gate returned exit code `0` using the existing pre-provisioned
repo-local executable. The produced summary was then checked with:

```text
.\.venv\Scripts\python.exe -c "... release._assert_electron_smoke_summary() ..."
Electron smoke summary assertions passed: output\electron\webview-runner-smoke\electron-webview-smoke-summary.json
```

## Boundary Checks

- No VS Code download path was added to `scripts/release.py`.
- `scripts/release.py` does not reference `downloadAndUnzipVSCode`.
- Normal `scripts/build.py`, `npm run build`, and `npm run test:electron:smoke`
  remain separate from provisioning automation.
- `output/electron/` and screenshot artifacts remain local evidence/support
  files and are not committed.
