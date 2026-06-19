# Electron Smoke VS Code Provisioning Automation Follow-Up Direction Analysis

> Date: 2026-06-20
> Status: completed evidence follow-up

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

Follow-up evidence run completed with exact VS Code version `1.93.1`:

```powershell
npm run provision:electron:vscode --prefix vscode-extension -- provision 1.93.1
npm run test:electron:smoke --prefix vscode-extension
```

The runner selected the repo-local executable:

```text
[electron-smoke] source=repo-local (output/electron/vscode-executable)
```

Rendered evidence exists at:

```text
output/electron/webview-runner-smoke/electron-webview-smoke-summary.json
output/electron/webview-runner-smoke/rendered-progress-graph-preview.html
output/playwright/electron-webview-smoke/rendered-progress-graph-preview.png
```

The summary confirmed:

- `panelVisible=true`;
- scheduler trajectory root present;
- scheduler trajectory payload present;
- `lanes=4`;
- `events=6`;
- `relations=12`.

The screenshot artifact passed a light non-blank sanity check:
`width=1600 height=1000`, `sampled_unique_colors=38`.

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

Completed. This produced the missing rendered Electron evidence.

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

Now eligible for a separate decision, but still deferred from this document.
Promotion should define whether the release checklist requires a pre-provisioned
local executable, a pinned cache, or a CI-managed cache.

## Recommendation

Candidate A is complete. The next narrow decision should be whether to promote
Electron smoke into release-grade validation, and if so which executable/cache
policy the release checklist will own.
