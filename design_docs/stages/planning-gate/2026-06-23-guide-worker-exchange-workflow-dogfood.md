# Planning Gate - Guide Worker Exchange Workflow Dogfood

> Date: 2026-06-23
> Status: COMPLETED

## Trigger

`review/agent-communication-product-closure-2026-06-22.md` closed the first
agent communication product layer:

1. `ExchangeArtifact` shell and local store foundation.
2. Per-agent mailbox and compact exchange-history read models.
3. Reply and lifecycle transition helpers.
4. Action-candidate detection and disposition products.
5. Accepted-candidate consumers for scheduler, review, handoff, merge, and
   blocker follow-up.

The next missing proof is not another standalone surface. The next proof is a
deterministic guide/worker workflow that uses these surfaces in sequence.

## Problem

The current system has the pieces needed for agent-to-agent coordination, but
no narrow dogfood workflow proves that a guide agent and a worker agent can use
them without falling back to prose-only coordination or raw shared chat history.

The desired first proof is:

```text
guide creates/addresses a coordination product
worker reads it through mailbox
worker replies or produces a candidate product
guide reads history/candidates
guide records a disposition
the accepted disposition is consumed through an explicit owner surface
```

## Scope

### Slice 1 - Deterministic Scenario Contract

Define one fake-runtime-safe dogfood scenario with stable artifact ids and
local paths.

The scenario should include:

1. a guide agent id;
2. a worker agent id;
3. one source coordination artifact addressed to the worker;
4. worker mailbox readback;
5. one worker reply artifact;
6. one action candidate artifact;
7. guide-side action-candidate readback;
8. one disposition artifact;
9. one accepted-candidate consumer invocation;
10. compact final readback.

The first scenario should prefer the smallest candidate type that proves a
real owner mutation without requiring live providers. `review_candidate` or
`scheduler_submission_candidate` are acceptable initial choices; the chosen
type must be explicit in the implementation gate notes before coding starts.

### Slice 2 - Runtime Helper

Add one runtime/helper product that composes existing surfaces instead of
duplicating their logic.

The helper should:

1. seed only the scenario artifacts it owns;
2. call the existing mailbox/history/candidate/disposition/consumer helpers;
3. return a compact `guide_worker_exchange_dogfood` result;
4. report an `authority_split` for every mutation class;
5. keep all exact artifact ids/versions visible in the result.

### Slice 3 - Operator Surface

Expose the helper through the narrowest operator surface needed for dogfood.

Preferred first surface:

```text
doc-based-coding scheduler guide-worker-exchange-dogfood
```

MCP exposure can be included only if it remains a thin wrapper over the same
helper and does not expand the scenario scope. Otherwise, it should be a
follow-up gate.

### Slice 4 - Prompt And Audit Discovery

Update the scheduler MCP smoke prompt and MCP Tool Surface Audit only for
surfaces that actually exist after implementation.

Do not document planned MCP tools as available.

## Non-Goals

This gate does not:

1. run real Qoder, opencode, Codex, or other live providers;
2. implement multi-agent scheduling policy;
3. implement autonomous guide-agent planning;
4. add raw transcript persistence;
5. add UI binding;
6. implement history compaction;
7. infer merge gates or blocked tasks from generic relations;
8. create real agent home or scratch directories;
9. run cleanup or sandbox providers;
10. mutate Local Work Trajectory from runtime/CLI/MCP code.

## Acceptance Criteria

This gate may close only when:

1. the scenario is documented with exact product sequence and owner surfaces;
2. runtime code composes existing agent exchange helpers rather than
   reimplementing mailbox/history/candidate/disposition/consumer semantics;
3. worker mailbox readback proves the source artifact is addressed to the
   worker;
4. exchange history readback proves reply causality/log clues;
5. action-candidate readback proves the worker product is recognized as the
   expected candidate type;
6. disposition readback proves `accept` is only a decision product;
7. accepted-candidate consumption proves the explicit owner surface performs
   the actual mutation;
8. authority split reports no raw transcript, no live provider execution, and
   no Local Work Trajectory mutation from runtime/CLI/MCP code;
9. focused runtime and CLI tests pass;
10. prompt/audit docs are updated only for implemented surfaces;
11. `git diff --check` and `mcp__doc_based_coding.analyze_changes` are clean
    or have documented, covered coupling alerts.

## Residual Risk Expected After Close

Even after this gate closes, the project will still need separate gates for:

1. guide-agent policy for when to create worker lines or candidates;
2. real runtime-provider execution over the same exchange products;
3. UI readback of guide/worker exchange state;
4. history compaction and retention;
5. multi-agent scheduling and isolation policy.

## Initial Implementation Recommendation

Start with a fake-runtime-only runtime helper and CLI dogfood product.

The first implementation should use the already completed product closure as
its source of truth:

- `review/agent-communication-product-closure-2026-06-22.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/tooling/MCP Tool Surface Audit.md`

Do not begin implementation until the current Checklist recovery-surface
optimization task is complete or explicitly paused.

## Implementation Notes

Chosen first scenario:

- Candidate type: `scheduler_submission_candidate`
- Target consumer surface: `admitExchangeArtifact`
- Runtime provider: `fake`
- Operator surface:
  `doc-based-coding scheduler guide-worker-exchange-dogfood`
- Runtime helper:
  `run_guide_worker_exchange_dogfood()`
- Request/result types:
  `GuideWorkerExchangeDogfoodRequest` /
  `GuideWorkerExchangeDogfoodResult`

The scenario uses a deterministic guide/worker sequence:

1. guide writes one worker-addressed coordination artifact;
2. worker mailbox readback proves the source artifact is in the worker inbox;
3. worker creates one exact-version reply artifact via the existing reply
   helper;
4. worker writes one scheduler task submission artifact using
   `scheduler_task_submission_to_artifact()`;
5. guide reads compact history and scheduler action candidates;
6. guide writes one accepted action-candidate disposition;
7. the accepted disposition is consumed by
   `consume_accepted_scheduler_action_candidate()`;
8. scheduler snapshot/event-log state and the admission ledger are mutated only
   by the explicit accepted-candidate consumer.

The helper deliberately composes existing product surfaces. It does not
reimplement mailbox, history, candidate detection, disposition writing, or
scheduler admission semantics.

No MCP tool is added in this slice. MCP exposure remains a follow-up gate unless
there is a concrete caller need for a thin wrapper over the same runtime helper.

## Implemented Surface

Runtime:

- `src/runtime/orchestration/guide_worker_exchange_dogfood.py`
- `GuideWorkerExchangeDogfoodRequest`
- `GuideWorkerExchangeDogfoodResult`
- `run_guide_worker_exchange_dogfood()`

CLI:

- `doc-based-coding scheduler guide-worker-exchange-dogfood`

Tests:

- `tests/test_runtime_orchestration_agent_communication.py`
- `tests/test_cli.py`

Prompt / audit writeback:

- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `design_docs/tooling/MCP Tool Surface Audit.md`

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_exchange_dogfood.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py
```

Focused implementation validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py -k "guide_worker_exchange_dogfood" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "guide_worker_exchange_dogfood" -q
```

Observed result:

```text
1 passed, 26 deselected
1 passed, 75 deselected
```

Adjacent validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "guide_worker_exchange_dogfood or inspect_agent_mailbox or inspect_agent_history or inspect_agent_action_candidates or decide_agent_action_candidate or consume_accepted_scheduler_candidate" -q
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -q
```

Observed result:

```text
27 passed
6 passed, 70 deselected
21 passed
```

Doc-loop validation:

```text
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py --target .
```

Observed result:

```text
Validation passed
```

Diff and coupling checks:

```text
git diff --check -- <touched runtime/CLI/test/doc files>
mcp__doc_based_coding.analyze_changes
```

Observed result:

- `git diff --check`: no whitespace errors; Windows line-ending warnings only.
- `analyze_changes`: no impact nodes and no coupling alerts.

Manual CLI smoke:

```text
doc-based-coding scheduler guide-worker-exchange-dogfood --artifact-id-prefix gw-smoke --timestamp 2026-06-23T00:00:00Z
```

Observed result:

- `ok=true`
- `candidate_type=scheduler_submission_candidate`
- scheduler snapshot/event-log state written in a temporary project
- admission ledger record written in a temporary project
- `provider_executed=false`
- `scheduler_projection_refreshed=false`
- `local_work_trajectory_mutated=false`
- `raw_transcript_persisted=false`

The first manual smoke was accidentally run from the development repository
instead of the temporary project. It wrote only untracked `.codex/orchestration`
and `.codex/scheduler` dogfood artifacts, which were verified to be within the
workspace and removed before rerunning the smoke correctly in the temporary
project.

One broad combined pytest command timed out at 120 seconds when
`tests/test_runtime_orchestration_agent_communication.py`, `tests/test_cli.py`,
and `tests/test_doc_loop_prompts.py` were run together. The same validation was
then split into the focused and adjacent commands above and passed.

## Closure

This gate closes the first deterministic guide/worker exchange dogfood proof.
It proves that the completed agent communication product layer can be used as a
real workflow sequence without raw shared chat history and without treating a
text decision as scheduler mutation.

Remaining work should proceed through separate gates:

1. optional MCP thin wrapper for this same helper;
2. guide-agent policy for when to create worker artifacts or candidates;
3. real runtime-provider execution over the same exchange products;
4. UI/readback binding for guide/worker exchange state;
5. history compaction and retention.
