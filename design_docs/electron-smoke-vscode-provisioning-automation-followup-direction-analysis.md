# Electron Smoke VS Code Provisioning Automation Follow-Up Direction Analysis

> Date: 2026-06-20
> Status: direction analysis

## Context

Completed planning gate:

- `design_docs/stages/planning-gate/2026-06-20-electron-smoke-vscode-provisioning-automation.md`

Review evidence:

- `review/electron-smoke-vscode-provisioning-automation-2026-06-20.md`

## Current Position

Electron smoke provisioning is now explicit and repeatable:

```powershell
npm run provision:electron:vscode --prefix vscode-extension -- dry-run <exact-version>
npm run provision:electron:vscode --prefix vscode-extension -- provision <exact-version>
```

No download has been executed yet. Rendered Electron evidence is still missing.

## Candidate A - Provision Exact VS Code Version And Run Smoke

### Shape

Choose an exact VS Code version, run provisioning, then run Electron smoke:

```powershell
npm run provision:electron:vscode --prefix vscode-extension -- provision <exact-version>
npm run test:electron:smoke --prefix vscode-extension
```

### Pros

1. Directly targets the missing rendered Electron evidence.
2. Uses the existing runner and provisioning tool.
3. Produces executable manifest metadata for review evidence.

### Risks

1. Requires network access if the version is not cached.
2. Requires a version pin decision.

### Fit

Highest. This is the evidence-producing next step.

## Candidate B - Version Pin Decision Only

### Shape

Decide which exact VS Code version should be used before running provisioning.

### Pros

1. Avoids accidental floating version selection.
2. Lets release policy choose a stable baseline.

### Risks

1. Still does not produce rendered evidence.

### Fit

Useful if the version pin is not obvious.

## Candidate C - Release Validation Promotion

### Shape

Promote Electron smoke only after provisioning and rendered evidence pass.

### Fit

Deferred.

## Recommendation

Prefer Candidate A after selecting an exact version. If no version is chosen,
use Candidate B as a short decision step, then run Candidate A.
