# Host Evidence MCP Resource Exposure Review — 2026-06-18

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-18-host-evidence-mcp-resource-exposure.md`.

Verdict: ready for close.

The slice exposes host scheduler evidence summaries through the existing MCP
resource surface:

```text
dbc://host-evidence/bundle
```

It is read-only and reuses `tools.progress_graph.read_host_evidence_bundle()`.
It does not add an execution tool, does not expose real providers through MCP,
and does not mutate scheduler or Local Work Trajectory state.

## Implementation Evidence

Changed:

- `src/mcp/tools.py`
  - `HOST_EVIDENCE_BUNDLE_RESOURCE_URI`
  - `list_resources()` metadata for `dbc://host-evidence/bundle`
  - `read_resource()` branch returning compact JSON
- `tests/test_mcp_prompts_resources.py`
  - resource metadata coverage
  - missing-directory empty bundle coverage
  - compact summary coverage over a fake host evidence artifact

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Resource is listed. | `test_host_evidence_bundle_resource_is_listed` checks URI/name/MIME/description. | Met |
| Resource returns compact JSON. | `test_read_host_evidence_bundle_returns_compact_summary` parses JSON and checks summary fields. | Met |
| Missing directory is stable. | `test_read_host_evidence_bundle_missing_directory_is_empty_and_read_only` returns `evidence_count=0`. | Met |
| Read is non-mutating. | Missing-directory test asserts local trajectory and scheduler projection files are not created by the read. | Met |
| No raw writer artifact binding. | Compact-summary test asserts `host_result` is absent. | Met |
| No provider execution surface added. | Only `read_resource()` was extended; scheduler run tools remain unchanged and fake-only. | Met |

## Validation

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_prompts_resources.py -k "host_evidence_bundle or resources"
24 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle"
2 passed
```

## Residual Risk

1. No VS Code UI binding yet.
2. No credentialed live Qoder success evidence yet.
3. No daemon or durable queue loop yet.
4. Resource read currently returns strict reader errors if malformed evidence
   JSON exists; a later UI-facing slice may add per-file isolated error views.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

1. Either bind the read-only resource into a host-visible UI surface once the UI
   branch is clean, or
2. provision SDK/auth outside project commits and rerun credentialed live Qoder
   smoke, then inspect the generated evidence through this resource.
