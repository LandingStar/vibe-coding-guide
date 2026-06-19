# Review - Electron Smoke VS Code Executable Provisioning Policy

> Date: 2026-06-20
> Planning Gate: `design_docs/stages/planning-gate/2026-06-20-electron-smoke-vscode-executable-provisioning-policy.md`

## Summary

Reviewed the first provisioning policy for a stable VS Code executable used by
Electron smoke validation.

The policy keeps the current slice manual and local. It defines where a stable
`Code.exe` should be placed, what metadata must accompany it, how to rerun the
existing smoke, and what evidence is required before Electron smoke can become
release-grade validation.

## Policy Artifact

- `design_docs/electron-smoke-vscode-executable-provisioning-policy.md`

## Key Decisions

- Canonical executable path:

  ```text
  output/electron/vscode-executable/Code.exe
  ```

- Sidecar metadata path:

  ```text
  output/electron/vscode-executable/manifest.json
  ```

- Highest priority temporary override:

  ```text
  VSCODE_ELECTRON_SMOKE_EXECUTABLE=<absolute-path-to-Code.exe>
  ```

- Neither executable nor manifest should be committed.

## Validation

```text
rg -n "output/electron/vscode-executable|VSCODE_ELECTRON_SMOKE_EXECUTABLE|Code.exe" design_docs docs vscode-extension/scripts/run-electron-webview-smoke.mjs
```

The search confirms the runner, policy, prior review evidence, and follow-up
documents consistently name the executable override and repo-local path.

No Electron rerun was required because this slice does not provision an
executable.

## Boundary Checks

- No VS Code download was added.
- No `Code.exe` was created or committed.
- No CI cache provisioning was added.
- No release packaging was changed.
- No Electron smoke release promotion was made.
- No runner behavior was changed in this slice.

## Residual Risk

Rendered Electron evidence is still missing. The next validation requires an
actual stable VS Code executable supplied manually or by a future automation
slice.
