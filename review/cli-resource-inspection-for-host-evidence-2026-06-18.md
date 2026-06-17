# CLI Resource Inspection For Host Evidence Review — 2026-06-18

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-18-cli-resource-inspection-for-host-evidence.md`.

Verdict: ready for close.

The slice adds an operator-facing CLI inspection surface over existing MCP
resources:

```text
doc-based-coding resources list
doc-based-coding resources read <uri>
```

It reuses `GovernanceTools.list_resources()` and `GovernanceTools.read_resource()`.
It does not add an execution tool, does not execute fake or real providers,
does not initialize scheduler state, and does not change the
`dbc://host-evidence/bundle` resource contract.

## Implementation Evidence

Changed:

- `src/__main__.py`
  - added `cmd_resources()`
  - registered `resources` in `_COMMANDS`
  - updated top-level help text
- `tests/test_doc_loop_prompts.py`
  - added CLI list/read success coverage
  - added missing-resource non-zero error coverage
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - added CLI fallback guidance
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - mirrored CLI fallback guidance

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| `resources list` exists and includes the host evidence resource. | `test_cli_resources_list_and_read_host_evidence_bundle`; manual CLI list output includes `dbc://host-evidence/bundle`. | Met |
| `resources read dbc://host-evidence/bundle` prints compact JSON. | `test_cli_resources_list_and_read_host_evidence_bundle`; manual CLI read returned `evidence_count=0` and `summaries=[]`. | Met |
| Missing resources return clear non-zero errors. | `test_cli_resources_read_missing_resource_returns_clear_error`; manual CLI read of `dbc://missing` returned exit code 1 and a clear stderr message. | Met |
| Prompt guidance includes CLI fallback. | Scheduler smoke prompt test covers the prompt surface; both prompt copies were updated. | Met |
| No new execution surface. | Implementation only instantiates `GovernanceTools` and calls resource list/read methods. | Met |

## Validation

```text
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "cli_resources or host_evidence_bundle or scheduler_mcp_smoke_prompt"
4 passed, 7 deselected

.\.venv\Scripts\python.exe -m src resources list
listed dbc://host-evidence/bundle

.\.venv\Scripts\python.exe -m src resources read dbc://host-evidence/bundle
returned compact bundle JSON with evidence_count=0 and summaries=[]

.\.venv\Scripts\python.exe -m src resources read dbc://missing
returned exit code 1 and "Resource not found: dbc://missing"
```

Change impact check:

```text
mcp analyze_changes over src/__main__.py, prompt copies, tests, and gate docs
impact direct=[], transitive=[], coupling alerts=[]
```

## Residual Risk

1. The VS Code preview UI is not bound to host evidence yet.
2. Credentialed live Qoder success evidence still depends on external SDK/auth.
3. Malformed evidence JSON still fails through the strict resource reader rather
   than becoming per-file isolated error summaries.
4. The CLI currently prints the full resource list; a future UX slice may add
   filters, but that is not required for this inspection contract.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

`Resource Error Isolation For Host Evidence` should be the next clean slice. It
will make host evidence consumption safer for future UI binding without mixing
into the currently dirty VS Code UI branch or requiring live Qoder credentials.
