---
name: project-handoff-generate
description: Generate a draft canonical handoff file for this project at a verified safe stop. Use when the current task either explicitly requests handoff generation or has reached a real `stage-close` or `phase-close` boundary where the next session should inherit structured context. Read the project handoff protocol, choose `stage-close` or `phase-close`, collect authoritative refs, detect conditional blocks, write a `draft` file under `.codex/handoffs/history/`, and validate it. Do not use for interrupted work, partial progress, or to refresh `CURRENT.md`.
---

# Project Handoff Generate

## Overview

Generate a project-local canonical handoff draft for the current safe stop and leave it in `.codex/handoffs/history/`.
Treat the protocol docs as the source of truth, allow model-driven entry only at verified safe stops, and never promote or mirror the handoff in this skill.

## Invocation Contract

Use this skill when one of the following is true:

- the current request explicitly asks to generate a handoff, including explicit slash requests such as `/project-handoff-generate`
- the client routes the request through the slash prompt and attaches this file as `prompt:SKILL.md`
- the current task has already reached a verified safe stop and generating a canonical handoff is the next required handoff step

Do not treat vague handoff mentions as sufficient trigger when safe stop, `kind`, or `scope_key` are still unclear.

Before generating anything, require these two inputs to be explicit in the current request or immediately derivable from recent safe-stop context:

- `kind`: `stage-close` or `phase-close`
- `scope_key`

If either one is unclear, stop and ask for clarification instead of guessing.

## Required Reads

Always read these first:

- `references/protocol-map.md`
- `references/generation-rules.md`
- `references/block-detection.md`

Then read only the additional project docs needed for the specific `kind` and changed surface.

## Workflow

Follow this order exactly:

1. Confirm the current task actually requires handoff generation, either from an explicit request or because the verified safe stop makes it the next required step.
2. Confirm the current work is at a real safe stop.
3. Confirm the `kind` and `scope_key`.
4. Load the required protocol docs and the minimum authoritative project refs.
5. Detect `conditional_blocks` using `references/block-detection.md`.
6. Run `scripts/prepare_handoff_draft.py` to create a canonical `draft` file in `.codex/handoffs/history/`.
7. Fill the generated draft with concrete content from the current project state.
8. Run `scripts/validate_handoff.py` on the completed draft.
9. If validation passes, leave the file in `draft` state and report its path.
10. Do not edit `.codex/handoffs/CURRENT.md`.

If generation succeeds without returning `blocked`, the model may continue into the next directly relevant handoff step. Do not stop only because the original entry was model-driven rather than slash-driven.

## External Skill Interaction Contract

The shared top-level contract for this skill is:

- model-initiated entry is allowed when the governing workflow says this skill is the next required step.
- explicit slash routing is valid but is not the only invocation surface.
- blocked is the only automatic stop signal.
- if the result is not blocked, the model may continue to the next directly relevant step.
- this skill does not widen authority, write scope, or control ownership on its own.

## Draft Creation

Use:

```bash
python scripts/prepare_handoff_draft.py --kind <stage-close|phase-close> --scope-key <scope-key> [--supersedes <handoff-id>] [--conditional-block <block-key>]...
```

The script creates the destination file, pre-fills frontmatter, and expands the conditional block skeletons.

After that, replace all placeholders with real content before validation.

## Validation

Use:

```bash
python scripts/validate_handoff.py <path-to-handoff>
```

Validation must pass before you report the draft as ready.

If validation fails, fix the draft or stop and report the blocking issues. Do not silently leave a broken draft behind.

## Hard Constraints

- Refuse interrupted or partial-progress handoff requests.
- Refuse to infer `kind` when the safe stop is ambiguous.
- Refuse to use `Other` unless it is genuinely unavoidable after checking core fields and current conditional blocks.
- Refuse to promote `draft -> active`.
- Refuse to refresh `.codex/handoffs/CURRENT.md`.
- Refuse to treat handoff content as higher priority than current workspace reality.

## Resources

- `references/protocol-map.md`
- `references/generation-rules.md`
- `references/block-detection.md`
- `scripts/prepare_handoff_draft.py`
- `scripts/validate_handoff.py`
