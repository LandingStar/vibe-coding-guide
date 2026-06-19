# Planning Gate: Electron Smoke VS Code Provisioning Automation

> Date: 2026-06-20
> Status: COMPLETED

## Context

Completed policy:

- `design_docs/stages/planning-gate/2026-06-20-electron-smoke-vscode-executable-provisioning-policy.md`
- `design_docs/electron-smoke-vscode-executable-provisioning-policy.md`

Follow-up:

- `design_docs/electron-smoke-vscode-executable-provisioning-followup-direction-analysis.md`

Manual discovery found no existing isolated executable. The next step is to
make provisioning repeatable without making ordinary tests or release flow
implicitly download VS Code.

## Scope

Implement an explicit opt-in provisioning script for Electron smoke:

1. Add a script under `vscode-extension/scripts/` that can provision a pinned
   VS Code executable using `@vscode/test-electron`.
2. Require explicit invocation; no build, unit test, package, or smoke command
   should auto-download VS Code.
3. Require or default a version pin and write it to manifest metadata.
4. Populate `output/electron/vscode-executable/Code.exe` on Windows.
5. Write `output/electron/vscode-executable/manifest.json`.
6. Include SHA-256 and acquisition/source metadata.
7. Add static tests for opt-in behavior, manifest fields, and command exposure.

## Acceptance

1. `package.json` exposes a clearly named provisioning script.
2. The provisioning script uses `downloadAndUnzipVSCode` only inside that
   opt-in script.
3. Normal `npm run build`, `npm test`, and `npm run test:electron:smoke` do not
   call `downloadAndUnzipVSCode`.
4. Static tests verify the script contract.
5. The policy/review/checkpoint/status docs are updated at close.
6. This slice does not need to execute the network download.

## Non-Goals

- Do not run the download in this slice unless explicitly requested later.
- Do not commit downloaded executable or manifest.
- Do not add CI cache provisioning.
- Do not promote Electron smoke to release validation.
- Do not change Scheduler/Host Evidence/Local Work Trajectory schemas.

## Validation Plan

```powershell
npm run build --prefix vscode-extension
node --test vscode-extension/dist/test/electronProvisioning.test.js
node --test vscode-extension/dist/test/electronWebviewRunner.test.js
```

Optional smoke after a provisioned executable exists:

```powershell
npm run test:electron:smoke --prefix vscode-extension
```

## Close Summary

Implemented an explicit opt-in provisioning script:

- `vscode-extension/scripts/provision-electron-vscode.mjs`
- `npm run provision:electron:vscode --prefix vscode-extension -- dry-run <exact-version>`
- `npm run provision:electron:vscode --prefix vscode-extension -- provision <exact-version>`

The script:

1. uses `@vscode/test-electron` `downloadAndUnzipVSCode`;
2. requires an exact VS Code version;
3. rejects floating `stable` / `insiders` for reproducible evidence;
4. supports dry-run without download;
5. only downloads or reuses cache through the explicit `provision` action;
6. writes the executable under `output/electron/vscode-executable`;
7. writes `manifest.json` with version/platform/source/path/timestamp/SHA-256.

Normal build, unit tests, and Electron smoke still do not download VS Code.

## Validation Result

Passed:

```text
npm run build --prefix vscode-extension
build complete
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
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
11 passed
```

Dry-run passed without download:

```text
npm run provision:electron:vscode --prefix vscode-extension -- dry-run 1.93.1
```

Output includes version, platform, cache path, target path, and the explicit
`provision <version>` next command.

## Close Decision

This planning gate is closed. The next step to obtain rendered Electron
evidence is to explicitly run provisioning for a chosen exact VS Code version,
then run:

```powershell
npm run test:electron:smoke --prefix vscode-extension
```

Release-grade promotion remains deferred until rendered evidence exists.
