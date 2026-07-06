# Advisory Product Pool Interface Design Record

> Date: 2026-07-05
> Status: design record / future planning input

## Context

After the first `trajectoryTeamContinuity` CLI/MCP surface, worker assignment
policy is still intentionally outside the mutation surface. The next abstraction
should not be a single automatic assignment command. It should be a higher-level
product interface that can support advisory, policy, and question-answering
roles under concurrent orchestration.

The motivating cases are:

1. A trajectory may use one dedicated assignment or policy agent for the whole
   work cluster. That role may receive multiple concurrent questions, requests,
   and status products.
2. A future workspace may attach advisor agents to relatively independent
   business blocks. Humans or agents can ask those advisors about local details,
   reducing the need for high-level leaders to inspect every low-level document
   or implementation detail.
3. Similar roles should share one product interface pattern instead of each
   role inventing a private request/result schema.

## Position

Use a pooled product interface above individual advisory calls.

The interface should define a product class, not a single hard-coded payload:

```text
AdvisoryProduct
- id
- product_class
- product_kind
- producer
- audience
- scope
- causality
- lifecycle_state
- priority
- created_at
- updated_at
- version
- validation_profile
- common
- payload
- logs
- decorators
```

`common` carries stable fields used by all roles. `payload` may contain
role-specific fields. `logs` and `decorators` carry audit, runtime, validation,
confidence, retention, and status decorations without hiding scheduler-relevant
facts in prose.

This is compatible with `ExchangeArtifact`. An `AdvisoryProduct` can be stored
as a structured payload part inside an `ExchangeArtifact`, or can reference
exact ExchangeArtifact versions for source material and results. The
ExchangeArtifact store remains the versioned coordination-product authority;
the advisory pool is a role-oriented input/output queue and validation layer.

## Pool Model

Each advisory role should have at least:

```text
AdvisoryInputPool
- pool_id
- owner_agent_id
- role_kind
- accepted_product_classes
- concurrency_policy
- validator_registry_ref
- queue_items
- audit_refs

AdvisoryOutputPool
- pool_id
- owner_agent_id
- role_kind
- emitted_product_classes
- validator_registry_ref
- result_items
- audit_refs
```

The pool design matters because a single dedicated advisor may service multiple
requests concurrently or in quick succession. Scheduling and activation can then
reason about pool pressure, item priority, causality, stale answers, and
validation failures without inspecting free-form chat.

## Validation Boundary

The code layer may allow role-specific payload fields, but runtime admission
must validate those fields before the product becomes authoritative.

Recommended boundary:

1. Common fields are always schema-validated.
2. `product_class` selects a validator family.
3. `validation_profile` selects the exact project/runtime profile.
4. Role-specific `payload` fields are accepted only after a registered
   validator returns structured success.
5. Validation failures become audit products, not silent prompt hints.

This gives implementation freedom while preserving application-level
correctness. A model may draft a flexible product, but the runtime decides
whether that product is usable for assignment, advisory readback, scheduler
admission, or user-facing answers.

## Initial Product Classes

Suggested first classes:

```text
assignment_advice
assignment_request
assignment_decision_support
business_block_question
business_block_answer
business_block_status_report
policy_review
escalation_request
```

These should stay as design names until a narrow planning gate chooses the first
runtime schema.

## Assignment Advisor Role

The assignment advisor is a specialized role that may recommend worker/lane
binding, lane ownership, provider choice, continuity use, or no-continuity
fallback. It should not directly mutate Local Work Trajectory, scheduler state,
delivery state, or continuous-worker bindings.

Its output should be consumed by a leader/main/supervisor/guide or by a future
policy consumer that has explicit authority.

This preserves the current `trajectoryTeamContinuity` authority split:
advice can be concurrent and specialized, but mutation remains owned by the
authorized surface.

## Business-Block Advisor Todo

Future work should support advisors attached to relatively independent business
blocks. A business-block advisor owns or is granted a scoped context bundle for
that block and can answer questions from humans, leaders, or other agents.

Expected behavior:

1. Answer questions from its scoped block context.
2. Produce compact upward reports.
3. Surface uncertainty, stale context, and required refreshes.
4. Reference exact source documents, artifacts, and relevant runtime history.
5. Avoid becoming the scheduler authority for the block.
6. Avoid storing private or sensitive raw transcript unless governed by the
   project retention policy.

This role is intended to reduce leader context load, not to replace leader
review authority.

## Current Skeleton

The first reusable skeleton is now implemented in:

- `src/runtime/orchestration/advisory_product_pool.py`
- `docs/advisory-product-pool.md`
- `design_docs/stages/planning-gate/2026-07-05-advisory-product-pool-schema-validator-skeleton.md`

Current coverage:

1. `AdvisoryProduct` common shape.
2. `AdvisoryProductValidatorRegistry` with default common validation and
   profile-specific validator dispatch.
3. `accept_advisory_input()` and `emit_advisory_output()` as in-memory pool
   validation/readback helpers.
4. `advisory_product_to_artifact()` and `advisory_product_from_artifact()` for
   exact structured payload bridging through `ExchangeArtifact`.

The skeleton does not yet implement persistent pools, advisor execution, MCP,
CLI, UI, assignment policy, or business-block advisors.

## Open Questions

1. Should the first implementation use `ExchangeArtifact` storage directly, or
   add a small pool index that references exact artifact versions?
2. Should validator profiles be Python callables, JSON Schema, Pydantic models,
   or a registry that can host several validator kinds?
3. How should pool concurrency interact with delivery leases and lane ownership
   when the same advisor is shared by several lanes?
4. Should business-block advisor answers expire automatically when source
   artifacts or scheduler state change?
5. Which role should own assignment-advisor output consumption in the first
   narrow gate: leader, scheduler policy consumer, or a dedicated supervisor?

## Non-Goals

This record does not implement:

1. automatic assignment policy;
2. a new MCP mutation tool;
3. business-block advisor runtime execution;
4. a pool daemon;
5. UI binding;
6. schema/validator code;
7. any change to `trajectoryTeamContinuity`.
