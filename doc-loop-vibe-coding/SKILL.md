---
name: doc-loop-vibe-coding
description: 文档驱动 vibe coding 的官方实例原型。以规划文档、阶段文档、write-back 和 handoff 为核心，展示协议/治理驱动工作流平台上的一个 pack 可能如何组织规则、模板、提示词和校验。Use when Codex needs to inspect, evolve, or eventually run the doc-driven coding instance of the broader workflow-driver platform.
---

# Doc Loop Vibe Coding

## Overview

This directory holds the prototype form of the official `doc-driven vibe coding` instance — one pack running on the broader protocol/governance-driven workflow platform. The platform-level authority lives in the root `docs/` directory; this instance should be understood as a concrete pack shape adopted through the platform's `Project Adoption` model (see `docs/project-adoption.md`).

Key platform concepts this instance relies on:

- **Pack**: an instance is delivered as a pack (`pack-manifest.json`) that declares document types, intents, gates, prompts, validators, and scripts.
- **Adoption**: a real repo adopts this instance through a project-local overlay pack (`.codex/packs/project-local.pack.json`) that binds the instance to the repo's actual document paths and rules.
- **Review State Machine**: high-impact actions follow the platform's `proposed → waiting_review → approved / rejected / revised → applied` state flow (see `docs/review-state-machine.md`).
- **Gate levels**: every action is gated at one of three levels — `inform`, `review`, or `approve` — determined by the platform's governance flow (see `docs/governance-flow.md`).

Use this instance to study one concrete pack shape: documents act as the control surface for implementation, the main agent operates the documents, humans review through the agent, and subagents receive narrow written contracts.

## Quick Start

If you are evaluating or evolving this instance, first read the platform docs at the repository root:

1. `docs/platform-positioning.md`
2. `docs/core-model.md`
3. `docs/plugin-model.md`
4. `docs/official-instance-doc-loop.md`
5. `docs/project-adoption.md`
6. `docs/current-prototype-status.md`

Only after that should you inspect this instance-specific scaffold.

If the target repo does not yet have a doc loop scaffold and you intentionally want to try this prototype shape, bootstrap it first:

```bash
python doc-loop-vibe-coding/scripts/bootstrap_doc_loop.py --target <repo> --project-name "<name>"
```

Then validate the scaffold:

```bash
python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target <repo>
```

If the repo already has the scaffold, start by reading:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. The active planning or phase doc under `design_docs/stages/`
4. The relevant long-lived rules under `design_docs/tooling/`
5. `.codex/handoffs/CURRENT.md` only when session transfer matters

## Instance Workflow

The workflow below operates within the platform's governance flow. Every step that produces a high-impact artifact (e.g., phase-close proposals, design conclusions, scope changes) should pass through the platform's review state machine at the appropriate gate level (`inform`, `review`, or `approve`). Important design nodes must reach `approved` before the next major step begins.

### 1. Restore Context From Docs

Treat docs as more authoritative than conversation memory. If docs and workspace disagree, resolve the mismatch before expanding scope.

Read [references/workflow.md](references/workflow.md) for the full loop. Use [references/subagent-delegation.md](references/subagent-delegation.md) when the task requires parallel work or handoff discipline.

### 2. Plan In A Narrow Slice Before Coding

Before making non-trivial changes, ensure there is one narrow planning or phase document that defines:

- the phase name
- what this slice does
- what it explicitly does not do
- acceptance and verification
- which docs and prompts must be updated on write-back

If no such document exists, create one from the templates in `assets/bootstrap/design_docs/stages/_templates/`.

### 3. Execute Only The Declared Slice

Use the planning doc as the implementation contract. Do not silently absorb neighboring backlog items just because they are nearby in the codebase.

When implementation reveals a new problem:

- add it to open items, or
- spin it into the next planning-gate candidate

Do not retroactively widen the current slice unless the user explicitly changes scope.

### 4. Pass The Verification Gate

Before declaring completion, run the verification described by the active phase doc:

- targeted tests for the changed area
- broader regression when risk warrants it
- manual verification when UX, CLI, transport, or orchestration changed
- doc/help/prompt sync for any new surface

Capture what was verified and what was not verified. Do not write unverified conclusions as settled fact.

When the slice reaches a design node that the platform's governance flow classifies as `review` or `approve`, the artifact must enter the review state machine (`proposed → waiting_review → approved`) before the slice can proceed or close.

### 5. Write Back Into The Doc System

Update the docs that carry long-lived truth:

- `Project Master Checklist.md` for current status and open items
- `Global Phase Map and Current Position.md` for the phase interpretation
- the active planning or phase doc for scope, outcome, and next-step contract
- `design_docs/tooling/` docs when the workflow or protocol itself changed
- `.codex/handoffs/CURRENT.md` only at a safe-stop boundary

## Instance Delegation Rules

The main agent owns the authoritative docs, integration, and final write-back. Subagents own only the narrow slice explicitly assigned to them.

When delegating:

- give each subagent a written scope, output file ownership, and acceptance target
- pass the minimum docs needed for that slice
- keep shared status docs and handoff docs under the main agent unless explicitly delegated
- require the subagent to report facts, diffs, verification, and open questions rather than free-form summaries

Use the prompt template in `assets/bootstrap/.codex/prompts/doc-loop/04-subagent-contract.md` as the default contract.

## Resources

- `pack-manifest.json`
  Prototype manifest for this official instance pack.
- `scripts/bootstrap_doc_loop.py`
  Bootstrap the current prototype version of the `design_docs/`, `.codex/prompts/`, and handoff scaffold into a target repo.
- `scripts/validate_doc_loop.py`
  Validate the target repo scaffold, required headings, and project-local pack wiring.
- `scripts/validate_instance_pack.py`
  Validate the instance manifest plus consistency between the example and bootstrap project-local packs.
- `references/workflow.md`
  Read for the document taxonomy, read order, anti-hallucination guardrails, and write-back rules.
- `references/subagent-delegation.md`
  Read for delegation boundaries, contract shape, and handoff discipline.
- `examples/`
  Concrete prototype JSON examples for project-local pack manifests plus `Subagent Contract`, `Subagent Report`, and `Handoff`.
- `assets/bootstrap/`
  Copy-ready project scaffold, prompt pack, markdown templates, `.codex/contracts/` schema templates, and `.codex/packs/project-local.pack.json` for this instance prototype.
