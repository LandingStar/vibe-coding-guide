# Subagent Delegation

## Purpose

Use this reference when the main agent needs help from one or more subagents without losing control of scope, documentation, or verification.

## Ownership Model

Keep ownership explicit:

- The main agent owns the authoritative docs, scope decisions, integration, and final write-back.
- A subagent owns only the slice described in its contract.
- Shared status documents stay with the main agent unless the delegation explicitly says otherwise.

This prevents multiple agents from inventing competing truths.

## Delegation Contract

Every subagent assignment should include:

- one clear task statement
- the files or directories the subagent may edit
- the authoritative docs the subagent must read
- the acceptance target
- the verification the subagent should run
- a statement of what is out of scope

If any of these are missing, tighten the contract before delegating.

## Recommended Flow

1. The main agent writes or refreshes the active planning doc.
2. The main agent extracts a narrow slice from that doc.
3. The subagent receives only the slice-relevant files and refs.
4. The subagent returns a diff-oriented report:
   - what changed
   - what was verified
   - what remains open
5. The main agent reviews, integrates, and updates the canonical docs.

## Safe Defaults

Use these defaults unless the task demands otherwise:

- One subagent per disjoint write set.
- No subagent writes `Project Master Checklist.md`, `Global Phase Map and Current Position.md`, or `.codex/handoffs/CURRENT.md`.
- No subagent expands phase scope on its own.
- No subagent claims completion without verification evidence.

## Handoff Discipline

Subagents should report facts, not replace the doc system. Ask for:

- changed files
- test commands run
- pass/fail results
- assumptions made
- blockers or open questions

The main agent decides what becomes part of the long-lived docs.

## Escalation Conditions

Pull work back to the main agent when:

- the subagent discovers the task is larger than the assigned slice
- the required docs conflict with the workspace
- integration crosses multiple write scopes
- the user decision boundary changed

In these cases, update the plan doc before sending work back out.
