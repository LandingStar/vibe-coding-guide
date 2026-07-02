# Planning Gate - OpenCode Server/API Stage Live Smoke Closure

Date: 2026-06-30

## Context

The OpenCode direct server/API adapter stage has completed:

- direct client and readiness helper;
- once supervisor transport binding;
- loop/E2E transport parity;
- session ledger / continuous worker binding policy alignment;
- doctor/provisioning alignment.

The remaining stage-level requirement is closure evidence for server/API
transport. The current development host has OpenCode CLI installed, but no
default `opencode serve` endpoint is reachable at `127.0.0.1:4096`.

## Goal

Close the OpenCode direct server/API adapter stage with durable evidence from
automated local HTTP fixture smoke plus explicit manual live-smoke instructions
for a real host-owned `opencode serve` endpoint.

## Scope

This slice includes:

1. Run focused automated smoke against local HTTP fixtures:
   - once supervisor server/API transport;
   - E2E smoke server/API transport;
   - bounded loop server/API transport;
   - doctor server/API readiness with injected opener.
2. Record host readiness fact from `doctor --profile opencode`.
3. Add manual smoke guidance for a real host-owned endpoint:
   - readiness command;
   - once supervisor command;
   - E2E smoke command;
   - bounded loop command;
   - audit artifacts to inspect.
4. Update Checklist and completion notes.

## Non-Goals

- Do not start, stop, restart, or supervise `opencode serve`.
- Do not run a live provider task if no host-owned server/API endpoint is
  already available.
- Do not expose live OpenCode provider execution through MCP.
- Do not persist raw transcript or secret values.
- Do not implement full continuous worker lifecycle.

## Acceptance Criteria

1. Automated local fixture tests prove server/API transport for once, E2E, and
   loop surfaces.
2. Doctor output proves current host state and distinguishes CLI readiness from
   missing server/API endpoint.
3. Manual smoke guide identifies concrete commands and expected audit evidence
   for a real host-owned `opencode serve`.
4. Checklist records stage closure and remaining next-stage boundary:
   continuous worker session/lane ownership policy.
5. Focused tests, `py_compile`, and `git diff --check` pass for touched files.

## Completion Notes

Implemented on 2026-06-30.

Host readiness observed:

- `python -m src doctor --profile opencode`
  returned exit code `0`.
- `opencode.cli_readiness` was `ok`; executable resolved to
  `C:\Users\16329\AppData\Roaming\npm\opencode.CMD`.
- `opencode.server_api_readiness` was `skipped`; the default endpoint
  `http://127.0.0.1:4096/global/health` was unreachable.

Automated fixture evidence:

- Focused CLI server/API transport tests passed for once, E2E smoke, and
  bounded loop through local HTTP fixtures:
  `22 passed, 148 deselected`.
- Focused runtime server/API/session/binding tests passed:
  `22 passed, 391 deselected`.
- Focused doctor/server/API readiness tests passed:
  `9 passed, 161 deselected` for CLI and `8 passed, 407 deselected` for
  runtime tests.

Manual live smoke is documented in
`docs/opencode-host-provisioning-check-guide.md`. The live-smoke requirement is
closed as automated fixture plus manual-host guidance because this repository
must not manage `opencode serve` lifecycle.

Stage boundary at closure:

- Complete: runtime transport foundation for selecting OpenCode `cli` or
  `server-api` on bounded delivery surfaces.
- Not complete by design: full continuous worker lifecycle, durable
  server/API-created session promotion, and session/lane ownership policy.
- Recommended next stage: continuous worker session/lane ownership policy for
  long-lived OpenCode worker contexts.
