# Electron Smoke VS Code Executable Provisioning Follow-Up Direction Analysis

> Date: 2026-06-20
> Status: direction analysis

## Context

Completed planning gate:

- `design_docs/stages/planning-gate/2026-06-20-electron-smoke-vscode-executable-provisioning-policy.md`

Policy:

- `design_docs/electron-smoke-vscode-executable-provisioning-policy.md`

Review evidence:

- `review/electron-smoke-vscode-executable-provisioning-policy-2026-06-20.md`

## Current Position

The runner can use an isolated executable and the project now has a manual
provisioning policy. No isolated executable is currently present in the
workspace, and no automatic download/cache behavior exists.

## Candidate A - Manual Executable Placement And Evidence Run

### Shape

Manually place a stable `Code.exe` and sidecar `manifest.json` under:

```text
output/electron/vscode-executable/
```

Then run:

```powershell
npm run test:electron:smoke --prefix vscode-extension
```

### Pros

1. Fastest path to the missing rendered Electron evidence.
2. Exercises the exact runner and policy already in place.
3. Avoids download/cache implementation before proving the smoke is otherwise
   sound.

### Risks

1. Requires an external executable to be supplied.
2. Still manual and not reproducible across machines.

### Fit

Highest if the immediate goal is evidence.

## Candidate B - Provisioning Automation Slice

### Shape

Implement a tool or script that downloads or locates a pinned VS Code archive,
verifies checksum, populates `output/electron/vscode-executable/`, writes
`manifest.json`, and then runs the existing smoke.

### Pros

1. Moves the smoke toward reproducible release validation.
2. Reduces manual setup burden.

### Risks

1. Requires network/download policy and checksum source of truth.
2. Can become CI/toolchain work.
3. Should not be mixed with release promotion.

### Fit

Good after the manual path proves the runner can produce evidence.

## Candidate C - Release Validation Promotion

### Shape

Add Electron smoke to release validation once rendered evidence exists from an
isolated executable.

### Pros

1. Strengthens release confidence for VS Code Host UX.
2. Catches real extension activation and webview assignment issues.

### Risks

1. Premature promotion can block releases on executable provisioning.
2. Needs explicit skip/fallback policy.

### Fit

Later.

## Recommendation

Prefer Candidate A next if a stable executable can be supplied. If not, the
next implementation slice should be Candidate B, but only after choosing a
download/version/checksum policy.
