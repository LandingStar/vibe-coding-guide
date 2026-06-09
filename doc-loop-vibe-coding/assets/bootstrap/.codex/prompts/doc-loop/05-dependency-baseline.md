# Dependency Baseline Prompt

Use this prompt only when the current task explicitly includes dependency
baseline creation, refresh, or maintenance.

`baseline_graph.json` is an optional workspace-local snapshot for dependency
impact propagation. It is not the knowledge graph engine, not the progress
graph, and not a required bootstrap artifact.

Runtime behavior:

- If `tools/dependency_graph/baseline_graph.json` is missing, `impact_analysis`
  and the impact section of `analyze_changes` should degrade gracefully and
  report that dependency propagation is unavailable.
- Missing baseline must not block ordinary implementation work by itself.
- `coupling_check` can still run independently from
  `coupling_annotations.json`.

Creation rules:

- Do not hand-write or fabricate `baseline_graph.json`.
- Create it only through a reproducible workspace-local generator or an
  explicitly adopted dependency graph export.
- Before creating or adopting a generator, follow
  `docs/dependency-baseline-generator-contract.md` when that document exists in
  the workspace.
- If the workspace has no generator yet, first write a narrow planning-gate or
  requirements note that defines source coverage, node ids, edge kinds, output
  path, validation, and refresh triggers.
- The generator may be adapted to the target repository language and tooling;
  do not assume this repository's prototype `build_baseline.py` is portable.

Maintenance rules:

- Refresh the baseline when the task changes dependency-relevant structure:
  module layout, public interfaces, symbol ownership, dependency extraction
  rules, or the baseline generator itself.
- Do not refresh the baseline for unrelated edits just to silence a missing
  baseline message.
- When refreshing, record the command or generator used, changed coverage, and
  validation result in write-back.
- If the baseline is stale or absent and impact propagation matters for the
  current risk assessment, report that limitation explicitly before relying on
  the analysis.

Workspace initialization:

- Bootstrap should not create `tools/dependency_graph/baseline_graph.json` by
  default.
- A newly initialized workspace may start with no dependency baseline; that is a
  valid degraded state.
- The first baseline should be created only after the project decides what its
  dependency graph should cover and how it will be regenerated.
