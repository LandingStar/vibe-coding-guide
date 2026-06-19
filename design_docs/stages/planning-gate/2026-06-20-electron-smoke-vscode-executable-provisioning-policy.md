# Planning Gate: Electron Smoke VS Code Executable Provisioning Policy

> Date: 2026-06-20
> Status: COMPLETED

## Context

Completed precursor:

- `design_docs/stages/planning-gate/2026-06-20-electron-smoke-isolated-vscode-executable.md`

Follow-up analysis:

- `design_docs/electron-smoke-isolated-vscode-executable-followup-direction-analysis.md`

The Electron smoke runner can now prefer an explicit or repo-local isolated VS
Code executable before falling back to the user-local install. A local discovery
check found:

- `VSCODE_ELECTRON_SMOKE_EXECUTABLE` is not set;
- `output/electron/vscode-executable/Code.exe` does not exist;
- `output/electron` currently only contains the prior
  `webview-runner-smoke` workspace.

Therefore the remaining blocker is not runner ambiguity; it is the absence of a
stable isolated VS Code executable provisioning policy.

## Scope

Define the first provisioning policy for Electron smoke executable evidence:

1. Canonical local path for manually supplied executable.
2. Version pin metadata required next to the executable.
3. Minimum integrity fields for a supplied executable.
4. Validation command sequence after placement.
5. Boundary between manual supply now and future automated download/cache.
6. Release-grade promotion preconditions.

## Acceptance

1. A policy document exists and names the canonical path used by the runner.
2. The policy explains how to manually supply `Code.exe` without committing it.
3. The policy defines metadata that must be recorded for a supplied executable.
4. The policy defines validation steps to rerun Electron smoke with that
   executable.
5. The policy explicitly keeps download automation and CI cache provisioning out
   of this slice.
6. Checklist, Phase Map, checkpoint, review evidence, and Local Work Trajectory
   are updated at close.

## Non-Goals

- Do not download VS Code.
- Do not create or commit `Code.exe`.
- Do not add CI cache provisioning.
- Do not modify release packaging.
- Do not promote Electron smoke into release-grade validation before rendered
  Electron evidence exists.
- Do not change the runner beyond documentation-driven clarifications unless a
  small static test is needed.

## Validation Plan

Docs-only validation:

```powershell
rg -n "output/electron/vscode-executable|VSCODE_ELECTRON_SMOKE_EXECUTABLE|Code.exe" design_docs docs vscode-extension/scripts/run-electron-webview-smoke.mjs
```

No Electron rerun is required in this slice because no isolated executable is
being provisioned here.

## Close Summary

Created the first manual provisioning policy:

- `design_docs/electron-smoke-vscode-executable-provisioning-policy.md`

The policy defines:

1. canonical repo-local executable path;
2. sidecar manifest path and required fields;
3. environment override behavior;
4. integrity expectations;
5. release-evidence boundary;
6. future automation boundary.

This slice does not download VS Code, create `Code.exe`, add CI cache behavior,
or promote Electron smoke into release validation.

## Validation Result

Passed:

```text
rg -n "output/electron/vscode-executable|VSCODE_ELECTRON_SMOKE_EXECUTABLE|Code.exe" design_docs docs vscode-extension/scripts/run-electron-webview-smoke.mjs
```

The search confirms the runner, policy, prior review evidence, and follow-up
documents consistently name the executable override and repo-local path.

## Close Decision

This planning gate is closed as a docs/policy slice. The next real validation
step is still to supply an isolated executable and run:

```powershell
npm run test:electron:smoke --prefix vscode-extension
```

If the project wants that executable to be acquired automatically, it should be
a separate provisioning automation gate.
