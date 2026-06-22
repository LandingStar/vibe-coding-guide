# Planning Gate - Supervisor Storage Binding Artifact Publish Surface

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/live-qoder-runtime-provider-dogfood-followup-direction-analysis.md`
recommends returning to scheduler/orchestration work that does not depend on a
live Qoder provider.

The current storage binding chain already has:

```text
SupervisorAgentStorageBinding
SupervisorStorageBindingEvidence
SupervisorStorageBindingEvidenceSummary
supervisor_storage_binding_evidence_summary_to_artifact()
JsonArtifactVersionStore
validate_supervisor_storage_binding_artifact_refs()
```

However, the compact supervisor storage binding artifact is currently easy to
produce in tests and fixtures, but not available as a general operator surface
over a real durable evidence file.

## Problem

Downstream scheduler tasks can declare:

```text
ExchangeReference(
    ref_kind="supervisor_storage_binding_artifact",
    ref_id="<binding artifact id>",
    version="<exact version>",
)
```

But an operator has no direct CLI/MCP product that reads one durable
`supervisor_storage_binding_evidence` JSON file, projects the compact binding
artifact, and records that exact artifact version in the local
ExchangeArtifact store.

That leaves an avoidable gap between supervisor storage binding evidence and
normal scheduler admission candidates.

## Scope

### Slice 1 - Runtime Publish Helper

Add a small runtime helper that:

1. reads `SupervisorStorageBindingEvidenceSummary` from an evidence path;
2. projects it with `supervisor_storage_binding_evidence_summary_to_artifact()`;
3. writes it to `JsonArtifactVersionStore`;
4. returns a compact result with artifact id/version, evidence id/path,
   replace-existing status, and authority split.

### Slice 2 - CLI Surface

Add:

```text
doc-based-coding scheduler publish-storage-binding-artifact
```

Required option:

```text
--evidence-path PATH
```

Optional bounded options:

```text
--artifact-store-path PATH
--artifact-id ID
--version VERSION
--producer ID
--audience A[,B]
--created-at TIMESTAMP
--replace-existing
```

### Slice 3 - MCP Surface

Expose the same product as:

```text
schedulerStorageBindingArtifactPublish
```

The MCP tool is an operator mutation surface over the ExchangeArtifact store
only. It must preserve the same boundary as the CLI helper.

## Non-Goals

This gate does not:

1. create agent home directories;
2. create scratch directories;
3. write scratch manifests;
4. approve or reject home registrations;
5. run scheduler tasks or providers;
6. admit scheduler submissions;
7. mark artifacts consumed;
8. refresh scheduler projection;
9. read or expose raw `binding` payload content beyond the existing compact
   evidence summary;
10. mutate agent-owned Local Work Trajectory;
11. alter the existing binding-consumer dogfood fixture.

## Acceptance Criteria

The gate may close only when:

1. runtime code can publish a compact supervisor storage binding artifact from
   a durable evidence summary into an exact-version local ExchangeArtifact
   store;
2. duplicate exact artifact/version writes fail unless `replace_existing` is
   explicitly enabled;
3. CLI help and behavior document the authority split;
4. MCP exposes the same surface with the same required inputs and mutation
   boundary;
5. focused runtime, CLI, and MCP tests pass;
6. prompt / tool audit docs mention the new surface where scheduler operator
   MCP usage is documented.

## Residual Risk After Close

This only publishes compact binding artifacts. It still does not implement real
agent home directory creation, scratch manifest lifecycle, retention review, or
secret scanning. Those remain separate storage lifecycle gates.

## Implementation Notes

### 2026-06-22 - Publish Surface

Implemented:

1. Runtime helper
   `publish_supervisor_storage_binding_artifact_from_evidence()` and result
   `SupervisorStorageBindingArtifactPublishResult`.
2. CLI surface:

   ```text
   doc-based-coding scheduler publish-storage-binding-artifact
   ```

3. MCP surface:

   ```text
   schedulerStorageBindingArtifactPublish
   ```

4. Prompt and MCP tool audit entries explaining when to use the publish
   surface versus binding-ref inspection, supervisor dogfood workflow, and
   exact admission.

Boundary preserved:

1. The helper reads compact durable evidence summary and writes only the local
   ExchangeArtifact store.
2. Duplicate exact artifact/version writes fail unless `replace_existing` /
   `--replace-existing` / `replaceExisting` is explicitly enabled.
3. The compact ExchangeArtifact does not embed the raw `binding` payload.
4. The surface does not admit scheduler tasks, run providers, create agent
   home or scratch directories, write scratch manifests, refresh projection, or
   mutate Local Work Trajectory.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py src/runtime/orchestration/supervisor_storage_binding_evidence.py src/runtime/orchestration/__init__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "publish_supervisor_storage_binding_artifact or supervisor_storage_binding_evidence_artifact"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "publish_storage_binding_artifact or scheduler_help_includes_exchange_artifact_admission"
3 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "storage_binding_artifact_publish"
1 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "binding or operator_workflow or operator_dogfood_closure or supervisor_dogfood_workflow or publish_storage_binding_artifact"
17 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "binding or operator_workflow or operator_dogfood_closure or storage_binding_artifact_publish"
9 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "binding or operator_workflow or operator_dogfood_closure or supervisor_dogfood_workflow"
33 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke"
1 passed
```

`analyze_changes` reported the expected MCP registration coupling alert for
`src/mcp/tools.py`. It is satisfied by `src/mcp/server.py` list-tools schema /
route updates and the focused MCP route test above.
