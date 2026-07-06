# Codex CLI Host Provisioning Check Guide

## Purpose

This guide defines the project-owned, credential-safe check for preparing a
host runtime to run worker tasks through Codex CLI.

It does not install Codex CLI, create credentials, persist tokens, or execute a
worker task. It only checks whether the current host can construct a later
host-owned `codex guide-worker-smoke` attempt.

## Authority Boundary

The real Codex CLI path is host-owned:

```text
CodexCliProcessClient
CodexCliClientConfig
CodexCliAgentRuntimeAdapter
run_host_owned_guide_worker_provider_execution()
doc-based-coding codex readiness
doc-based-coding codex guide-worker-smoke
```

MCP scheduler execution remains fake-only. Do not expose live Codex CLI
execution through `schedulerGuideWorkerLocalOrchestration` or generic scheduler
MCP tools.

## Readiness Command

Run:

```text
doc-based-coding codex readiness
```

Equivalent module form:

```text
python -m src codex readiness
```

Optional flag:

```text
--executable PATH
```

The readiness output reports only executable availability and resolved path. It
does not run `codex exec` and does not print or store credentials.

## Guide-Worker Smoke Command

Run only after reading readiness:

```text
doc-based-coding codex guide-worker-smoke
```

Useful bounded options:

```text
--executable codex
--cwd PATH
--model NAME
--sandbox read-only|workspace-write|danger-full-access
--ask-for-approval untrusted|on-request|never
--artifact-store-path .dbc/orchestration/exchange-artifacts.json
--admission-ledger-path .dbc/orchestration/exchange-artifact-admissions.json
--snapshot-path .dbc/scheduler/codex-guide-worker-provider-execution-state.json
--event-log-path .dbc/scheduler/codex-guide-worker-provider-execution-events.jsonl
--evidence-id codex-guide-worker-provider-execution
--evidence-path .dbc/scheduler/evidence/codex-guide-worker-provider-execution.json
--git-worktree-sandbox-root .dbc/sandboxes/codex-workers
--sandbox-allocation-evidence-id codex-worker-sandbox-allocation
--sandbox-allocation-evidence-path .dbc/scheduler/evidence/codex-worker-sandbox-allocation.json
--host-invocation-id host-owned-codex-guide-worker-provider-execution-cli
--reason "bounded host-owned Codex CLI guide-worker execution"
--guide-task-title "Build maze game"
--guide-task-summary "Split browser client and server API work."
--planner-lane lane:client=Client UI:browser controls and test hooks:client,web:git-worktree
--planner-lane lane:server=Server API:state API and port boundary:server,api:git-worktree
--max-parallel-lanes 2
--max-waves 1
--wave-execution-mode serial|threaded
--timestamp 2026-06-24T00:00:00+08:00
```

The command uses `RuntimeProviderPermissionGrant(provider="codex",
allow_process_spawn=True)` inside a host-owned wrapper. It is not an MCP
real-provider surface. On success it writes compact
`host_guide_worker_provider_execution_evidence` with planner metadata,
generated instructions, per-worker execution receipts, provider, lane, wave,
task state, output artifact, worker writeback receipts, optional sandbox
allocation receipt evidence path, review-only worker patch artifact refs for
git-worktree runs, and authority facts.

It does not persist raw transcripts, create persistent agent home directories,
refresh scheduler projection, auto-merge worker worktrees into the source
workspace, or mutate agent-owned Local Work Trajectory.

For git-worktree workers, the host wrapper reads the allocated worktree and
publishes `worker_patch_review_proposal` ExchangeArtifacts. These artifacts are
visible to the existing action-candidate readback as `merge_candidate` entries,
but acceptance is still a coordination product. To evaluate or use the patch,
run the explicit operator surface:

```text
doc-based-coding scheduler consume-worker-patch-review \
  --disposition-artifact-id ID \
  --disposition-version VERSION \
  --action check|apply|reject \
  --source-workspace-root PATH
```

`check` runs `git apply --check` without changing the source workspace.
`apply` runs `git apply --check` and then `git apply` against the explicitly
supplied source workspace. `reject` only marks the patch proposal rejected. The
command does not resolve scheduler merge gates or clean worker sandboxes;
sandbox cleanup remains the separate explicit `scheduler cleanup-receipts`
flow.

When multiple worker patch proposals must be evaluated together, run the
non-mutating composition preflight before applying any one patch:

```text
doc-based-coding scheduler preflight-worker-patch-composition \
  --patch-ref FIRST_PATCH_ARTIFACT_ID@VERSION \
  --patch-ref SECOND_PATCH_ARTIFACT_ID@VERSION \
  --source-workspace-root PATH
```

The preflight reads exact `worker_patch_review_proposal` artifacts, copies the
source workspace into a temporary workspace, then runs `git apply --check` and
`git apply` only inside that temporary copy in caller order. It reports the
first failed patch and touched-path collisions. It does not mutate the source
workspace, write dispositions, choose an order, resolve conflicts, clean
sandboxes, or run Codex/Qoder providers.

## Output Contract

Readiness returns JSON:

```json
{
  "executable": "codex",
  "executable_resolved": "...",
  "cli_available": true,
  "ready": true,
  "error_kind": "",
  "raw_error_type": "",
  "summary": ""
}
```

Missing CLI returns:

```json
{
  "executable": "codex",
  "executable_resolved": "",
  "cli_available": false,
  "ready": false,
  "error_kind": "cli_unavailable",
  "raw_error_type": "MissingExecutable",
  "summary": "Codex CLI executable is unavailable: codex"
}
```
