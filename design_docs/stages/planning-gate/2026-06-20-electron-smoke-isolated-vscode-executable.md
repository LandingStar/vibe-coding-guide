# Planning Gate: Electron Smoke Isolated VS Code Executable

> Date: 2026-06-20
> Status: COMPLETED

## Context

Completed precursor:

- `design_docs/stages/planning-gate/2026-06-19-electron-webview-runner-spike.md`

Follow-up analysis:

- `design_docs/electron-webview-runner-spike-followup-direction-analysis.md`

The Electron Webview Runner Spike added a narrow real VS Code Electron runner,
but two consecutive local runs failed before extension-test startup because the
user-local VS Code install held the `vscode-updating` mutex:

```text
checkInnoSetupMutex: vscode-updating is held, waiting up to 30s for setup to finish...
checkInnoSetupMutex: vscode-updating still held after 31399ms, giving up
Error: Code is currently being updated. Please wait for the update to complete before launching.
```

The runner already accepts `VSCODE_ELECTRON_SMOKE_EXECUTABLE`, but the current
script still prefers the user install by default and does not give a structured
executable-source or update-lock diagnostic. This keeps release-grade Electron
evidence coupled to the user-local auto-updating install.

## Scope

Harden the existing Electron smoke runner so it can use an isolated VS Code
executable when one is available and can report why it did not.

1. Define an explicit executable resolution order:
   - `VSCODE_ELECTRON_SMOKE_EXECUTABLE`;
   - a repository-local isolated executable path under the existing output or
     tool cache convention;
   - the current user-local VS Code fallback.
2. Print a compact diagnostic before launch showing:
   - selected executable path;
   - source kind;
   - whether it came from an explicit environment variable, repo-local path, or
     user-local fallback.
3. Preserve direct `Code.exe` launch with `shell: false`.
4. Preserve removal of inherited `ELECTRON_RUN_AS_NODE` and `VSCODE_DEV`.
5. Keep evidence-file guard after process exit.
6. If the runner fails with the known `vscode-updating` startup path, surface a
   clear message that recommends `VSCODE_ELECTRON_SMOKE_EXECUTABLE` or a
   repo-local isolated executable.

## Acceptance

1. Existing focused Node tests and build still pass.
2. Electron runner keeps deterministic fake workspace behavior.
3. Electron runner does not download VS Code or add network behavior.
4. Electron runner does not introduce a broad CI/platform management flow.
5. Electron runner can be statically tested for executable resolution order and
   update-lock diagnostic wording.
6. Running without an isolated executable may still fail on this machine, but
   the failure must now explain that the user-local VS Code install is the
   selected source and recommend the isolated executable path option.
7. Planning gate, review evidence, checkpoint/status docs, and Local Work
   Trajectory are updated at close.

## Non-Goals

- Do not download VS Code.
- Do not add CI cache provisioning.
- Do not promote Electron smoke into release-grade validation in this slice.
- Do not run live Qoder or credentialed provider execution.
- Do not start background daemon behavior.
- Do not change scheduler/admission/evidence schemas.
- Do not mutate agent-owned Local Work Trajectory from scheduler workflow code.
- Do not redesign the Progress Graph Preview UI.

## Validation Plan

Expected validation:

```powershell
npm run build --prefix vscode-extension
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
node --test vscode-extension/dist/test/extensionManifest.test.js
```

Focused runner attempt:

```powershell
npm run test:electron:smoke --prefix vscode-extension
```

If no isolated executable exists locally, this command is allowed to fail on
the known user-local VS Code update mutex, but the diagnostic must clearly
identify the selected executable source and remediation path.

## Close Summary

The runner now resolves VS Code executable sources in a deterministic order:

1. `VSCODE_ELECTRON_SMOKE_EXECUTABLE`;
2. repo-local `output/electron/vscode-executable/Code.exe`;
3. user-local VS Code install fallback.

Before launch it prints the selected source and executable path. When it falls
back to the user-local install, it explicitly warns that an updating user
install can block startup and names both isolated-executable remediation paths.

The runner still does not download VS Code, manage CI caches, or promote the
Electron smoke into release-grade validation.

## Validation Result

Passed:

```text
npm run build --prefix vscode-extension
build complete
```

```text
node --test vscode-extension/dist/test/electronWebviewRunner.test.js
3 passed
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
11 passed
```

```text
node --test vscode-extension/dist/test/extensionManifest.test.js
1 passed
```

Focused runner attempt:

```text
npm run test:electron:smoke --prefix vscode-extension
```

The runner still failed because the current machine selected the user-local VS
Code install and that install still holds the `vscode-updating` mutex, but the
diagnostic now identifies the selected source and remediation path:

```text
[electron-smoke] VS Code executable resolution
[electron-smoke] source=user-local (default user VS Code install)
[electron-smoke] executable=C:\Users\16329\AppData\Local\Programs\Microsoft VS Code\Code.exe
[electron-smoke] using the user-local VS Code install; if it is updating, set VSCODE_ELECTRON_SMOKE_EXECUTABLE or place an isolated Code.exe under output/electron/vscode-executable/
```

The enriched failure also reports:

```text
Electron smoke used the user-local VS Code install. If startup reports `vscode-updating`, rerun with:
  VSCODE_ELECTRON_SMOKE_EXECUTABLE=<path-to-isolated-Code.exe>
or place an isolated executable at:
  E:\workspace\tool develop\vibe coding facilities\doc based coding\output\electron\vscode-executable\Code.exe
```

## Close Decision

This planning gate is closed. The current remaining blocker is no longer
ambiguous runner behavior; it is the absence of an isolated VS Code executable
or a cleared user-local VS Code update lock. The next step should be a
validation rerun with an explicit isolated executable path, not more runner
surface changes.
