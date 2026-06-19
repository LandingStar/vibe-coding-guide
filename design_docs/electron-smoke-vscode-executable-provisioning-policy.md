# Electron Smoke VS Code Executable Provisioning Policy

> Date: 2026-06-20
> Status: policy draft

## Purpose

The Electron webview smoke runner needs a stable VS Code executable to produce
rendered evidence. The user-local VS Code install is unsuitable as the only
source because auto-update locks can block startup before extension tests run.

This policy defines the first manual provisioning contract for an isolated VS
Code executable. It does not add download automation or CI cache provisioning.

## Canonical Paths

Primary manual placement path:

```text
output/electron/vscode-executable/Code.exe
```

Metadata path:

```text
output/electron/vscode-executable/manifest.json
```

The runner already checks the executable path after
`VSCODE_ELECTRON_SMOKE_EXECUTABLE` and before the user-local fallback.

## Manual Provisioning Contract

To supply an isolated executable manually:

1. Create the directory:

   ```text
   output/electron/vscode-executable/
   ```

2. Place a stable VS Code executable at:

   ```text
   output/electron/vscode-executable/Code.exe
   ```

3. Add a sidecar `manifest.json` with at least:

   ```json
   {
     "product": "Visual Studio Code",
     "executable": "Code.exe",
     "version": "<vscode-version>",
     "source": "<manual-source-description>",
     "acquired_at": "<ISO-8601 timestamp>",
     "sha256": "<sha256-of-Code.exe>",
     "notes": "Manual local provisioning for Electron smoke. Do not commit executable or manifest."
   }
   ```

4. Run:

   ```powershell
   npm run test:electron:smoke --prefix vscode-extension
   ```

The executable and manifest are local evidence/support files and must not be
committed.

## Environment Override

When testing a temporary executable without placing it under `output/electron`,
set:

```text
VSCODE_ELECTRON_SMOKE_EXECUTABLE=<absolute-path-to-Code.exe>
```

Then run:

```powershell
npm run test:electron:smoke --prefix vscode-extension
```

This override has highest priority and is appropriate for one-off local
validation.

## Integrity Expectations

For manual provisioning, the operator should record:

- VS Code version;
- executable path;
- acquisition source;
- acquisition timestamp;
- `Code.exe` SHA-256;
- whether the executable is known to be isolated from the user-local
  auto-updating install.

The first automated follow-up, if any, should validate these fields before
trusting the executable for release evidence.

## Release Evidence Boundary

Electron smoke can be considered for release-grade validation only after:

1. the runner uses `env` or `repo-local` executable source, not `user-local`;
2. `electron-webview-smoke-summary.json` is produced;
3. `rendered-progress-graph-preview.html` is produced;
4. the summary confirms:
   - `panelVisible=true`;
   - scheduler trajectory root present;
   - scheduler trajectory payload present;
   - `lanes=4`;
   - `events=6`;
   - `relations=12`;
5. the executable source and version are recorded in review evidence.

Until then, Electron smoke remains a targeted validation line, not a release
gate.

## Future Automation Boundary

A later provisioning automation slice may:

- download a pinned VS Code archive;
- verify checksum;
- unpack into a cache directory;
- refresh `output/electron/vscode-executable/Code.exe`;
- write `manifest.json`;
- run the existing Electron smoke.

That future slice must separately define:

- download source;
- version pin policy;
- checksum source of truth;
- cache invalidation rules;
- offline behavior;
- CI policy.

This policy intentionally does not implement those behaviors.
