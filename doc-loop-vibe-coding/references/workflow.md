# Document Workflow

## Purpose

Use this reference when you need the full operating model behind this instance pack. The goal is to reduce context drift by moving critical decisions out of chat memory and into a small set of authoritative documents.

This workflow operates on the platform defined in `docs/`. It relies on the platform's governance flow (`docs/governance-flow.md`), review state machine (`docs/review-state-machine.md`), and project adoption model (`docs/project-adoption.md`). The instance does not redefine these platform-level concepts; it consumes them.

## Core Loop

The default loop is:

1. Rebuild context from existing docs.
2. Create or refresh one narrow planning document.
3. Implement only what that document declares.
4. Verify with tests, manual checks, and doc/help sync.
5. Write the outcome back into status docs, phase docs, and handoff docs.

If the task cannot fit into one narrow slice, stop and split it into multiple candidate docs before coding.

## Authoritative Doc Layers

Use the following layers and do not collapse them into one giant document. These layers implement the platform's three-tier adoption model: platform authority (`docs/`), official instance pack (`doc-loop-vibe-coding/`), and project-local overlay pack (`.codex/packs/project-local.pack.json`).

- `docs/`
  Platform-level authority. Defines core objects, gate semantics, review state machine, project adoption, and plugin model. Takes precedence when it disagrees with instance-level or project-local docs.

- `design_docs/Project Master Checklist.md`
  Use as the status board and coordination entrypoint.
- `design_docs/Global Phase Map and Current Position.md`
  Use to explain where the project is in the larger arc.
- `design_docs/stages/planning-gate/`
  Use for candidate slices and next-phase selection.
- `design_docs/stages/<stage>/`
  Use for approved slice docs, manual test guides, and acceptance context.
- `design_docs/tooling/`
  Use for long-lived workflow, authoring, handoff, and delegation standards.
- `.codex/handoffs/CURRENT.md`
  Use for safe-stop transfer only. It is not the highest truth source.
- `.codex/prompts/doc-loop/`
  Use for reusable prompt surfaces. Keep them synchronized with the workflow they implement.

## Read Order

On an existing project, read in this order:

1. `Project Master Checklist.md`
2. `Global Phase Map and Current Position.md`
3. the current planning or phase doc
4. only the relevant tooling standards
5. the current handoff only when session transfer matters

Do not start by reading every historical phase doc. Pull only the minimum context needed for the active slice.

## Planning Rules

Before implementation, ensure the active slice doc says:

- what is being proved or delivered
- what is explicitly out of scope
- what verification is required
- what docs or prompts must be updated before the slice can close
- which gate level (`inform`, `review`, or `approve`) applies to the expected outcome

If the slice touches an important design node, the planning doc should explicitly note that user review is required before the outcome can be applied. This aligns with the platform's review state machine: artifacts enter `proposed → waiting_review → approved` before write-back.

If the repo has no scaffold yet, bootstrap one first instead of improvising the document tree.

## Execution Rules

While implementing:

- treat the active slice doc as the contract
- capture new insights as open items or next-phase candidates
- avoid silently widening scope
- prefer changing docs when the truth changed, not only when the code changed

If the code reality invalidates the current plan, update the plan doc before continuing so the written contract stays truthful.

## Verification And Write-Back

The write-back step should always record:

- what changed
- what was verified
- what was not verified
- why the slice can stop here
- what the next narrow slice should be

Before write-back, confirm the artifact's review state. If the platform's governance flow requires `review` or `approve` for this type of change, the artifact must reach `approved` status before being written into the long-lived docs. Do not write unreviewed conclusions as settled fact.

The common sinks are:

- status board update
- phase doc update
- tooling protocol update when the workflow itself changed
- handoff update at safe stop

## Anti-Hallucination Guardrails

Use these rules to reduce made-up conclusions:

- Prefer document references over conversational recall.
- Mark unknowns and unverified claims explicitly.
- Separate current-slice facts from future ideas.
- Do not treat a subagent summary as authoritative until it has been integrated and verified.
- If two docs conflict, resolve the conflict instead of paraphrasing both.

## Prompt Pack Usage

The prompt pack under `.codex/prompts/doc-loop/` is for recurring moves:

- `01-planning-gate.md`
- `02-execute-by-doc.md`
- `03-writeback.md`
- `04-subagent-contract.md`

Use them as starting points, not immutable scripts. Keep them aligned with the workflow standard when the process evolves.
