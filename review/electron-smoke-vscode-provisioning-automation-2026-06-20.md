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

## Boundary Checks

- No VS Code executable was downloaded in this slice.
- No executable or manifest was committed.
- No CI cache provisioning was added.
- `npm run build`, `npm test`, and `npm run test:electron:smoke` do not call
  `downloadAndUnzipVSCode`.
- Electron smoke was not promoted to release validation.

## Residual Risk

Rendered Electron evidence still requires executing the opt-in provisioning
command for a selected exact VS Code version, then running the Electron smoke.
