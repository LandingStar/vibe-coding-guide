# Electron Smoke Isolated VS Code Executable Follow-Up Direction Analysis

> Date: 2026-06-20
> Status: direction analysis

## Context

Completed planning gate:

- `design_docs/stages/planning-gate/2026-06-20-electron-smoke-isolated-vscode-executable.md`

Review evidence:

- `review/electron-smoke-isolated-vscode-executable-2026-06-20.md`

## Current Position

The Electron smoke runner can now explain and control its VS Code executable
source:

- explicit `VSCODE_ELECTRON_SMOKE_EXECUTABLE`;
- repo-local `output/electron/vscode-executable/Code.exe`;
- user-local fallback.

The runner still fails on this machine because no isolated executable is
present and the selected user-local VS Code install is blocked by the
`vscode-updating` mutex. The failure is now diagnostic rather than ambiguous.

## Candidate A - Rerun With Explicit Isolated Executable

### Shape

Provide a known stable VS Code executable path and rerun:

```text
VSCODE_ELECTRON_SMOKE_EXECUTABLE=<path-to-Code.exe> npm run test:electron:smoke --prefix vscode-extension
```

or place `Code.exe` at:

```text
output/electron/vscode-executable/Code.exe
```

then rerun the existing script.

### Pros

1. Uses the exact runner that is already implemented.
2. Avoids the user-local auto-update mutex.
3. Produces the missing rendered Electron evidence if the extension path is
   otherwise sound.

### Risks

1. Requires a stable executable to be supplied by the environment or user.
2. Does not define how the executable is obtained or updated.

### Fit

Highest. This is the next validation action.

## Candidate B - VS Code Executable Provisioning Policy

### Shape

Define where an isolated VS Code executable should come from, how it should be
cached, and when it should be refreshed.

### Pros

1. Moves the smoke toward reproducible release validation.
2. Avoids ad hoc local executable placement.

### Risks

1. Can quickly become CI/toolchain management.
2. Requires download, version pinning, and cache policy decisions.

### Fit

Good after Candidate A proves the isolated executable path works.

## Candidate C - Release-Grade Electron Smoke Promotion

### Shape

Promote `npm run test:electron:smoke --prefix vscode-extension` into the
release validation checklist after successful rendered Electron evidence exists.

### Pros

1. Raises confidence in VS Code Host UX behavior.
2. Catches command activation and webview assignment failures beyond static
   tests.

### Risks

1. Premature promotion can make releases depend on local executable
   availability.
2. Needs a skip/fallback rule for environments without an isolated executable.

### Fit

Later. Promotion should follow at least one successful isolated-executable
evidence run.

## Recommendation

Prefer Candidate A next. The runner has been hardened enough; the remaining
missing proof is rendered Electron evidence from a stable executable. Only if
Candidate A succeeds should provisioning policy or release promotion be
designed.
