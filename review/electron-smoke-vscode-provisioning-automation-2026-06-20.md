# Review - Electron Smoke VS Code Provisioning Automation

> Date: 2026-06-20
> Planning Gate: `design_docs/stages/planning-gate/2026-06-20-electron-smoke-vscode-provisioning-automation.md`

## Summary

Reviewed the explicit opt-in provisioning automation for Electron smoke VS Code
executables.

The implementation adds a provisioning script and npm entry point, but does not
make build/test/smoke download VS Code implicitly. The script requires an exact
VS Code version and supports dry-run before any download/cache mutation.

## Changed Files

- `vscode-extension/scripts/provision-electron-vscode.mjs`
- `vscode-extension/package.json`
- `vscode-extension/src/test/electronProvisioning.test.ts`
- `design_docs/electron-smoke-vscode-executable-provisioning-policy.md`
- `design_docs/stages/planning-gate/2026-06-20-electron-smoke-vscode-provisioning-automation.md`

## Behavior

Dry-run:

```powershell
npm run provision:electron:vscode --prefix vscode-extension -- dry-run 1.93.1
```

Provision:

```powershell
npm run provision:electron:vscode --prefix vscode-extension -- provision 1.93.1
```

The `provision` action uses `@vscode/test-electron` `downloadAndUnzipVSCode`,
copies the downloaded executable directory to
`output/electron/vscode-executable`, and writes `manifest.json` with:

- product;
- executable;
- exact version;
- platform;
- source;
- cache path;
- source executable path;
- target executable path;
- acquisition timestamp;
- SHA-256;
- local non-commit notes.

## Validation

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

Dry-run validation:

```text
npm run provision:electron:vscode --prefix vscode-extension -- dry-run 1.93.1
```

The dry-run printed version, platform, cache path, target path, and the explicit
`provision <version>` next command. No download was executed.

Follow-up rendered evidence validation:

```text
npm run provision:electron:vscode --prefix vscode-extension -- provision 1.93.1
```

Result:

- provisioned isolated VS Code executable at
  `output/electron/vscode-executable/Code.exe`;
- wrote `output/electron/vscode-executable/manifest.json`;
- manifest version: `1.93.1`;
- manifest platform: `win32-x64-archive`;
- manifest SHA-256:
  `29fce3e07e9c682d7f4bca35cfc7ad69409101cc026010db7f0369792009cf4c`.

```text
npm run test:electron:smoke --prefix vscode-extension
```

Result:

- build completed;
- runner selected `repo-local (output/electron/vscode-executable)`;
- smoke exited with code `0`;
- wrote `output/electron/webview-runner-smoke/electron-webview-smoke-summary.json`;
- wrote `output/electron/webview-runner-smoke/rendered-progress-graph-preview.html`.

Summary assertions:

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

Screenshot-style validation:

```text
.\node_modules\.bin\playwright.cmd screenshot --viewport-size=1600,1000 "file:///E:/workspace/tool%20develop/vibe%20coding%20facilities/doc%20based%20coding/output/electron/webview-runner-smoke/rendered-progress-graph-preview.html" "output/playwright/electron-webview-smoke/rendered-progress-graph-preview.png"
```

The screenshot artifact was created at
`output/playwright/electron-webview-smoke/rendered-progress-graph-preview.png`.
Sanity check reported `width=1600 height=1000` and
`sampled_unique_colors=38`, so the evidence is not a blank page.

## Boundary Checks

- No VS Code executable was downloaded during the original implementation
  slice; the follow-up evidence run used the explicit opt-in provisioning
  command.
- No executable or manifest was committed.
- No CI cache provisioning was added.
- `npm run build`, `npm test`, and `npm run test:electron:smoke` do not call
  `downloadAndUnzipVSCode`.
- Electron smoke was not promoted to release validation.

## Residual Risk

Rendered Electron evidence now exists for the pinned local VS Code `1.93.1`
executable. Release-grade promotion remains a separate decision: the smoke is
still a targeted validation line until the release checklist explicitly adopts
it and defines cache/offline behavior.
