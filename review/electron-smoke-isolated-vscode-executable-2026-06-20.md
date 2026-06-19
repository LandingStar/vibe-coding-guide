# Review - Electron Smoke Isolated VS Code Executable

> Date: 2026-06-20
> Planning Gate: `design_docs/stages/planning-gate/2026-06-20-electron-smoke-isolated-vscode-executable.md`

## Summary

Reviewed the Electron smoke runner hardening after repeated `vscode-updating`
mutex failures from the user-local VS Code install.

The runner now has a deterministic executable resolution order and prints a
compact diagnostic before launch. It can prefer an explicit isolated executable
or a repo-local isolated executable before falling back to the user-local
auto-updating install.

## Implemented Behavior

Executable resolution order:

1. `VSCODE_ELECTRON_SMOKE_EXECUTABLE`;
2. `output/electron/vscode-executable/Code.exe`;
3. default user-local VS Code install.

The runner now prints:

- selected executable source kind;
- selected source label;
- selected executable path;
- a user-local fallback warning when the selected executable may be affected by
  update locks.

If the user-local fallback fails, the error explains how to rerun with an
isolated executable.

## Changed Files

- `vscode-extension/scripts/run-electron-webview-smoke.mjs`
- `vscode-extension/src/test/electronWebviewRunner.test.ts`
- `design_docs/stages/planning-gate/2026-06-20-electron-smoke-isolated-vscode-executable.md`

## Validation

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

Current output confirms the user-local fallback was selected:

```text
[electron-smoke] VS Code executable resolution
[electron-smoke] source=user-local (default user VS Code install)
[electron-smoke] executable=C:\Users\16329\AppData\Local\Programs\Microsoft VS Code\Code.exe
[electron-smoke] using the user-local VS Code install; if it is updating, set VSCODE_ELECTRON_SMOKE_EXECUTABLE or place an isolated Code.exe under output/electron/vscode-executable/
```

It still fails on the known local update mutex:

```text
checkInnoSetupMutex: vscode-updating is held, waiting up to 30s for setup to finish...
checkInnoSetupMutex: vscode-updating still held after 31392ms, giving up
Error: Code is currently being updated. Please wait for the update to complete before launching.
```

The enriched error now provides the remediation path:

```text
Electron smoke used the user-local VS Code install. If startup reports `vscode-updating`, rerun with:
  VSCODE_ELECTRON_SMOKE_EXECUTABLE=<path-to-isolated-Code.exe>
or place an isolated executable at:
  E:\workspace\tool develop\vibe coding facilities\doc based coding\output\electron\vscode-executable\Code.exe
```

## Boundary Checks

- No VS Code download automation was added.
- No CI cache provisioning was added.
- No Electron smoke release promotion was made.
- No live provider execution was added.
- No scheduler/admission/evidence schema was changed.
- The existing deterministic fake workspace and evidence-file guard remain in
  place.

## Residual Risk

The runner is now clearer and more controllable, but rendered Electron evidence
still requires either:

- a local VS Code install with no update lock; or
- an isolated executable supplied through
  `VSCODE_ELECTRON_SMOKE_EXECUTABLE` or
  `output/electron/vscode-executable/Code.exe`.
