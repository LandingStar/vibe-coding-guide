# Electron Smoke Release Validation Promotion Direction Analysis

> Date: 2026-06-20
> Status: direction analysis

## Context

Recent completed evidence line:

- `design_docs/electron-smoke-vscode-provisioning-automation-followup-direction-analysis.md`
- `review/electron-smoke-vscode-provisioning-automation-2026-06-20.md`

The first rendered Electron smoke evidence now exists:

- pinned VS Code version: `1.93.1`
- executable source: `repo-local (output/electron/vscode-executable)`
- smoke command: `npm run test:electron:smoke --prefix vscode-extension`
- summary: `panelVisible=true`, scheduler root/payload present, `lanes=4`, `events=6`, `relations=12`
- screenshot sanity: `1600x1000`, `sampled_unique_colors=38`

The current question is not whether the smoke can run. It can. The question is
whether it should become release-grade validation, and which provisioning
policy owns that release gate.

## Candidate A - Keep Targeted Local Evidence Only

### Shape

Keep Electron smoke as an explicit local validation line:

```powershell
npm run provision:electron:vscode --prefix vscode-extension -- provision 1.93.1
npm run test:electron:smoke --prefix vscode-extension
```

Release checklist references the evidence as optional/manual confidence, but
does not fail releases when the local executable or network cache is missing.

### Pros

1. Lowest implementation cost.
2. Avoids making releases depend on a large binary download/cache.
3. Preserves current explicit opt-in boundary.

### Risks

1. Release confidence still relies mostly on unit/HTML tests.
2. A future webview regression could pass non-Electron tests.

### Fit

Good if releases remain developer-operated and the Electron runner is still
young.

## Candidate B - Release Checklist Gate With Pre-Provisioned Local Executable

### Shape

Promote Electron smoke into the release checklist, but require a pre-provisioned
local executable before release validation starts.

The release process checks:

1. `output/electron/vscode-executable/Code.exe` exists;
2. `manifest.json` exists and uses an accepted exact version;
3. smoke output summary matches the known assertions.

The release script does not download VS Code automatically. It fails with a
clear remediation command when provisioning is missing.

### Pros

1. Stronger release signal without hidden network mutation.
2. Keeps release validation reproducible around an exact VS Code version.
3. Failure mode is operator-actionable.

### Risks

1. Release operators must maintain local binary/cache state.
2. The large local executable remains outside git and outside release package
   provenance unless separately documented.

### Fit

Best immediate next step. It upgrades confidence while preserving the explicit
download boundary that the current policy already established.

## Candidate C - CI-Managed Pinned Cache Gate

### Shape

Promote Electron smoke to release validation and make CI/release automation
own the pinned VS Code executable cache.

The release system downloads or restores exact VS Code `1.93.1`, verifies
manifest/integrity expectations, runs Electron smoke, and archives summary plus
screenshot evidence.

### Pros

1. Strongest release reproducibility once mature.
2. Removes local operator drift.
3. Makes rendered webview evidence part of release artifacts.

### Risks

1. Requires cache lifecycle, offline behavior, and checksum source-of-truth
   decisions.
2. Adds CI/runtime cost and more moving parts.
3. Premature if local smoke still needs more operational hardening.

### Fit

Correct long-term direction, but too wide as the immediate next slice.

## Recommendation

Prefer Candidate B as the next narrow planning gate:

```text
Electron Smoke Release Checklist Pre-Provisioned Gate
```

The gate should:

1. keep provisioning explicit and outside normal build/test;
2. add a release validation preflight that checks executable/manifest presence;
3. run the existing Electron smoke only when the preflight passes;
4. record summary and screenshot artifact paths in release evidence;
5. fail with a clear remediation command when executable provisioning is
   missing;
6. avoid CI-managed cache/download behavior for now.

Candidate C should remain a later promotion after the pre-provisioned gate has
proven stable in real release runs.
