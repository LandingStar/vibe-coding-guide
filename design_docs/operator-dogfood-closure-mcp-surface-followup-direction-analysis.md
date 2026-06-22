# Operator Dogfood Closure MCP Surface Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-operator-dogfood-closure-mcp-surface.md`
closed with `schedulerOperatorDogfoodClosure` exposed on the Codex-facing MCP
surface.

Review evidence:

- `review/operator-dogfood-closure-mcp-surface-2026-06-22.md`

## Current Position

The deterministic operator closure is now reachable through all three expected
non-UI surfaces:

```text
runtime: run_scheduler_operator_dogfood_closure()
CLI:     doc-based-coding scheduler operator-dogfood-closure
MCP:     schedulerOperatorDogfoodClosure
```

The default `binding-consumer` fixture now proves this bounded fake-runtime
sequence through the primary Codex agent surface:

```text
seed fixture
-> binding-ref inspection
-> exact admission
-> consumed lifecycle marking
-> bounded fake loop evidence
-> scheduler projection refresh
-> Host Evidence readback
```

The remaining gaps are now consumer-side convenience and live-runtime proof,
not the closure contract itself.

## Candidate A - Host UX Operator Dogfood Closure Control

### Goal

Add one Host UX control that invokes the shared closure product and displays the
compact closure summary / authority split.

### Why Useful

Manual operator dogfood currently has to use CLI or MCP. A Host UX control would
make the completed closure visible to the VS Code / Copilot Host UX layer
without re-encoding the workflow sequence in frontend code.

### Boundary

Presentation and invocation only. The UI must call the shared closure product.
It must not implement its own seed/admit/run/project sequence. Screenshot
validation is required.

## Candidate B - Live Qoder Runtime Provider Dogfood

### Goal

Run one controlled scheduler task through a real Qoder-backed runtime provider
under explicit host permission and isolation policy.

### Why Useful

The fake-runtime closure is now reachable from Codex/MCP. The next backend risk
is whether a real runtime provider can execute a bounded scheduler task while
preserving evidence, authority split, and failure readback.

### Boundary

Requires a separate live-runtime planning gate. Do not extend
`schedulerOperatorDogfoodClosure` to run live providers directly; keep the
closure fake-runtime-only unless a later contract explicitly redefines it.

## Candidate C - Closure Evidence Readback Hardening

### Goal

Improve compact readback around closure evidence IDs, projection paths, and
Host Evidence cards if repeated dogfood reveals ambiguity.

### Why Useful

This is a low-risk hardening path, but current validation already provides a
usable evidence product. It should be driven by concrete dogfood findings, not
implemented speculatively.

## Recommendation

My current preference is Candidate A if the next work stays product-facing:

```text
Host UX Operator Dogfood Closure Control
```

Reason:

1. runtime, CLI, and MCP are now aligned;
2. Host UX can consume the stable product instead of duplicating workflow logic;
3. screenshot validation can catch presentation issues without touching the
   backend closure contract;
4. live Qoder is important but should wait for an explicit credential/runtime
   readiness gate.

If the next priority is backend orchestration rather than Host UX, Candidate B
should become the next planning-gate instead.

## Proposed Next Planning Gate

Product-facing path:

```text
design_docs/stages/planning-gate/2026-06-22-host-ux-operator-dogfood-closure-control.md
```

Backend-runtime path:

```text
design_docs/stages/planning-gate/2026-06-22-live-qoder-runtime-provider-dogfood.md
```
