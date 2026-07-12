# Planning Gate - Installed Worker Report Contract And 0.9.9 Release

## Status

Completed on 2026-07-12. The local `0.9.9` release bundle is ready for user
publication. Host inversion remains unopened until another session updates this
workspace's installed runtime and the user explicitly authorizes the next node
and trajectory.

## Document Role

This gate closes the install-layout defect exposed by the 2026-07-11
Spirebound content-expansion test, then prepares the `0.9.9` patch release.
It is deliberately separate from the later scheduler/orchestration host
inversion.

## Current Problem

- `consumeWorkerTrajectoryReport` currently locates
  `docs/specs/subagent-report.schema.json` relative to the runtime module's
  source checkout. In an installed wheel this resolves inside
  `site-packages/docs/`, where the workspace-owned schema does not exist.
- The official instance bootstrap tells workers and leaders to use
  `docs/worker-trajectory-update-reporting.md` and the Subagent Report schema,
  but those two files are absent from the bootstrap scaffold.
- Source-layout tests pass because the repository checkout accidentally
  supplies the schema, so the release gate does not currently prove the
  installed layout.

## Authoritative Inputs

- `docs/worker-trajectory-update-reporting.md`
- `docs/specs/subagent-report.schema.json`
- `src/runtime/orchestration/worker_trajectory_report_consumer.py`
- `doc-loop-vibe-coding/scripts/bootstrap_doc_loop.py`
- `review/spirebound-content-expansion-full-test-acceptance-2026-07-11.md`
- User decision on 2026-07-12: publish this patch before beginning host
  inversion; record Direct/Managed mode enablement as backlog only.

## Slice Name

- `Installed Worker Report Contract And 0.9.9 Release`

## This Slice Only

- Resolve the worker-report schema from
  `<project_root>/docs/specs/subagent-report.schema.json`.
- Ensure a long-lived process cannot reuse one workspace's schema for another
  workspace.
- Bootstrap the worker-report procedure and schema into adopted workspaces.
- Add source, bootstrap, wheel-content, and installed-layout regression gates.
- Bump runtime and official instance packages to `0.9.9`, refresh release
  materials, build the release bundle, and commit the coherent release batch.
- Preserve and include the already reviewed Spirebound evidence and logical
  lane-split guidance changes.

## Explicitly Out Of Scope

- Do not invert ownership of scheduler/orchestration lifecycle relative to a
  Codex or VS Code host.
- Do not implement the Direct Assistant Mode / Managed Mode feature matrix.
- Do not add Managed Mode VS Code support. The accepted future boundary allows
  Managed Mode's user-facing main/leader session to run in Codex CLI only;
  OpenCode or other CLI hosts remain later adapters.
- Do not claim scheduler-owned parallel execution from logical Local Work lane
  records or worker reports alone.

## Acceptance And Validation Gates

- Focused runtime tests prove project-root schema resolution, missing-schema
  diagnostics, and isolation between two different project roots.
- Bootstrap tests prove the procedure and schema are copied and remain aligned
  with the authoritative root documents.
- The instance wheel content gate requires both bootstrap files.
- An installed-layout smoke installs both built wheels into an isolated target,
  bootstraps a temporary workspace, and consumes a valid worker report without
  importing runtime code from the source checkout.
- Full Python tests, release version consistency, secret scanning, VSIX
  packaging, and the existing Electron smoke release gate pass.
- `release/doc-based-coding-v0.9.9.zip` contains both `0.9.9` wheels, the
  unchanged independently versioned VSIX, the pinned graph-engine input, and
  current release documents.

## Documents To Synchronize

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `release/README.md`
- `release/RELEASE_NOTE.md`
- `release/INSTALL_GUIDE.md`
- `release/COMMIT_MESSAGE_CN.md`
- `release/COMMIT_MESSAGE_EN.md`

## Subagent Split

- None. This is one narrow release-integrity path touching one contract,
  bootstrap parity, tests, and packaging. Parallel edits would add integration
  overhead without creating an independent work context.

## Closure Boundary

This slice is complete when the install-layout defect is covered by an actual
installed-wheel smoke, the `0.9.9` bundle exists, release documents match the
artifacts, and the batch is committed locally. Stop there. Host inversion may
begin only after the user publishes the release, another session updates this
workspace's installed runtime, and the user explicitly authorizes the new
trajectory/node.

## Closure Evidence

- Worker-report consumption resolves the schema only from the target
  workspace. Focused coverage proves successful consumption, actionable
  missing-schema diagnostics, and different schema behavior in two project
  roots within one process.
- Bootstrap parity tests prove the worker procedure and schema are copied and
  content-aligned with the authoritative root documents.
- The build requires both bootstrap members in the instance wheel and installs
  both wheels into an isolated target. The smoke proved `src` and
  `doc_loop_vibe_coding` were imported from that target, then bootstrapped a
  temporary workspace and consumed a valid worker report through the installed
  CLI.
- The first full release attempt exposed three adjacent regressions: CLI and
  MCP test fixtures did not deploy the now-required workspace schema, and pack
  integrity hashing included the instance pack's generated root `build/`
  directory. The fixtures now model adopted workspaces, while pack hashing
  excludes only root build outputs (`build/` and `dist/`) and still detects
  nested pack-owned content and source changes.
- Related focused regression after remediation: `25 passed`.
- Final full release pipeline:
  - version consistency passed;
  - secret scan passed;
  - both `0.9.9` wheels built and passed content verification;
  - installed-layout worker-report smoke passed;
  - full Python suite: `2371 passed, 3 skipped`;
  - VSIX `0.2.1` packaged;
  - pre-provisioned VS Code `1.93.1` Electron smoke summary assertions passed;
  - `release/doc-based-coding-v0.9.9.zip` generated.
- The Direct Assistant / Managed Mode enablement matrix remains an explicit
  Checklist todo and was not implemented in this release.
