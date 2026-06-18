# Host Evidence Presentation Contract Review — 2026-06-18

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-18-host-evidence-presentation-contract.md`.

Verdict: ready for close.

The slice adds a pure presentation contract over `HostEvidenceBundle`.
Downstream host UI or operator surfaces can now consume stable presentation
cards and error rows instead of binding directly to low-level evidence summary
fields.

The existing MCP resource and CLI bundle payload remain unchanged.

## Implementation Evidence

Changed:

- `tools/progress_graph/host_evidence.py`
  - added `HostEvidencePresentation`
  - added `HostEvidencePresentationCard`
  - added `HostEvidencePresentationErrorRow`
  - added `HostEvidencePresentationFact`
  - added `HostEvidencePresentationRef`
  - added `build_host_evidence_presentation()`
  - added card and bundle status derivation helpers
- `tools/progress_graph/__init__.py`
  - exported the new presentation types and builder
- `tests/test_progress_graph_trajectory.py`
  - added empty bundle presentation coverage
  - added completed-card refs / authority coverage
  - added permission-review / failed / partial status coverage
  - added error-only and mixed error-row coverage

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Presentation model builds from `HostEvidenceBundle`. | `build_host_evidence_presentation()` accepts a bundle and returns serializable presentation JSON. | Met |
| Empty bundle has stable empty status and message. | `test_host_evidence_bundle_missing_directory_is_empty` now asserts `status="empty"` and empty message. | Met |
| Successful summary becomes a completed card. | `test_host_evidence_presentation_builds_completed_card_with_refs_and_authority` checks provider, invocation, output ref, and authority clues. | Met |
| Permission-review / failed / partial states are distinct. | `test_host_evidence_presentation_derives_non_completed_statuses` covers all three status derivations. | Met |
| Isolated errors become error rows without hiding valid cards. | `test_host_evidence_bundle_isolates_malformed_artifacts` checks mixed valid card + two error rows. | Met |
| Existing MCP resource and CLI bundle behavior remain stable. | Existing prompt/resource focused tests pass unchanged. | Met |

## Validation

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence"
6 passed, 54 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "host_evidence_bundle or cli_resources or scheduler_mcp_smoke_prompt" tests/test_mcp_prompts_resources.py -k "host_evidence_bundle or resources"
27 passed, 8 deselected
```

## Residual Risk

1. No VS Code UI binding yet.
2. No new MCP resource URI for presentation JSON yet.
3. Presentation status labels are intentionally conservative; future UI may
   need display-specific wording without changing these machine-facing values.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

1. Choose a narrow host evidence UI binding after the unrelated VS Code dirty
   branch is clean, or
2. Run a credentialed live Qoder smoke after SDK/auth provisioning.
