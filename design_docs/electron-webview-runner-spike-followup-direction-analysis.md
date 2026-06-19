# Electron Webview Runner Spike Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

Completed planning gate:

- `design_docs/stages/planning-gate/2026-06-19-electron-webview-runner-spike.md`

Review evidence:

- `review/electron-webview-runner-spike-2026-06-19.md`

## Current Position

The Electron webview runner spike implemented a narrow real VS Code runner seam:

- separate Electron extension-test bundle;
- deterministic fake workspace fixture;
- direct `Code.exe` launch with `shell: false`;
- inherited `ELECTRON_RUN_AS_NODE` / `VSCODE_DEV` removed;
- Progress Graph Preview opened through the real command surface;
- scheduler trajectory mount and `4 lanes / 6 events / 12 relations` checked
  through a test-mode-only host-side HTML snapshot command;
- evidence files required after process exit to avoid false positives.

Focused build/static/backend tests passed. The true Electron smoke is currently
blocked by the local VS Code install holding the `vscode-updating` mutex before
extension tests start.

## Candidate A - Rerun Same Electron Smoke After VS Code Update

### Shape

Rerun:

```text
npm run test:electron:smoke --prefix vscode-extension
```

after the local VS Code update finishes.

### Pros

1. Smallest possible next step.
2. Tests the runner exactly as implemented.
3. Separates host-environment readiness from code changes.

### Risks

1. Still depends on the user-local VS Code install state.
2. Does not yet prove CI portability.

### Fit

Highest. This should be the immediate next validation action.

## Candidate B - Isolated VS Code Executable For Smoke Validation

### Shape

Supply a downloaded, archived, or otherwise isolated VS Code executable through
`VSCODE_ELECTRON_SMOKE_EXECUTABLE` so the smoke does not depend on the user's
auto-updating VS Code install.

### Pros

1. Avoids the user install update mutex.
2. Makes the smoke closer to reproducible release validation.
3. Uses the existing runner path without changing the extension test contract.

### Risks

1. Requires toolchain policy for where the executable comes from and how it is
   cached.
2. Can become a CI/platform-management slice if expanded too far.

### Fit

Good if Candidate A remains blocked or proves flaky.

## Candidate C - Promote Electron Smoke To Release Validation

### Shape

After at least one successful rendered Electron evidence run, decide whether
`npm run test:electron:smoke --prefix vscode-extension` should become part of
release-grade validation.

### Pros

1. Raises confidence in real VS Code Host UX behavior.
2. Catches command registration, extension activation, and webview assignment
   issues that static tests cannot catch.

### Risks

1. Premature promotion can make releases hostage to local VS Code install
   state.
2. Needs explicit fallback or skip policy for environments without a stable
   Electron executable.

### Fit

Later. Do not promote until the runner has produced successful evidence in a
controlled environment.

## Recommendation

Prefer Candidate A next. The code seam exists and the current blocker is the
host VS Code update mutex, so the next useful evidence is a clean rerun with no
new implementation. If the same blocker or another install-state issue repeats,
move to Candidate B and keep that as a separate narrow environment-hardening
slice.
