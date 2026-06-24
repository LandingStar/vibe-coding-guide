# Planning Gate - Evidence Publish To Consumer Closure

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/supervisor-storage-binding-artifact-publish-surface-followup-direction-analysis.md`
recommends proving that durable supervisor storage binding evidence can enter a
downstream scheduler consumer closure through the new publish surface.

## Problem

The current system has both:

1. a publish surface that writes compact supervisor storage binding artifacts
   from durable evidence summaries; and
2. a `binding-consumer` operator closure that can consume compact binding
   artifacts.

However, the existing `binding-consumer` fixture writes its compact binding
artifact directly. That validates downstream consumption, but does not prove
the new durable evidence publish path is part of the same operational closure.

## Scope

Add a narrow backend/CLI dogfood closure that composes existing products:

```text
build storage binding evidence
-> write durable evidence JSON
-> publish it as exact-version supervisor_storage_binding_artifact
-> write a consuming scheduler submission that references that exact artifact
-> run binding-ref inspection, exact admission, consume, bounded fake loop,
   projection refresh, and Host Evidence readback
```

## Non-Goals

This gate does not:

1. create real agent home directories;
2. create scratch directories;
3. write scratch manifests;
4. approve persistent home registrations;
5. run cleanup or retention review;
6. run live Qoder or any real provider;
7. add Host UX controls;
8. add or mutate agent-owned Local Work Trajectory from runtime/CLI code;
9. replace `schedulerOperatorDogfoodClosure`;
10. change scheduler admission semantics beyond reusing existing explicit
    operator workflow steps.

## Acceptance Criteria

The gate may close when:

1. backend helper returns a compact closure result that separates durable
   evidence, published artifact, consuming submission, operator workflow,
   final candidate summary, and authority split;
2. CLI exposes the closure with fake-runtime-only guard and explicit path/id
   options;
3. tests prove the consuming submission references the published artifact
   id/version, not a directly seeded fixture artifact;
4. tests prove no real home/scratch directories, scratch manifests, cleanup,
   live providers, or Local Work Trajectory mutation occur;
5. focused runtime and CLI tests pass.

## Implemented Surface

Runtime/helper:

- `tools.progress_graph.evidence_publish_to_consumer_closure`
- `run_evidence_publish_to_consumer_closure()`
- `EvidencePublishToConsumerClosureRequest`
- `EvidencePublishToConsumerClosureResult`

CLI:

- `doc-based-coding scheduler evidence-publish-consumer-closure`

The closure writes durable supervisor storage binding evidence, publishes it
through the compact supervisor storage binding artifact surface, seeds a
consumer scheduler submission that references the published artifact
id/version, and then reuses the existing operator workflow for binding-ref
inspection, exact admission, fake bounded loop execution, projection refresh,
and Host Evidence readback.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_cli.py -k "evidence_publish_to_consumer_closure or evidence_publish_consumer_closure" -q
```

Observed result:

```text
4 passed, 363 deselected
```

This closure was also covered by the later combined validation for the
guide-worker/provider wrapper commit set:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py tools/progress_graph/guide_worker_provider_execution.py tools/progress_graph/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py tests/test_doc_loop_prompts.py
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

## Residual Risk After Close

The closure still uses fake runtime and still does not create real private
storage resources. Real storage lifecycle remains a separate gate with path
governance, secret scanning, retention, quota, and cleanup responsibilities.
