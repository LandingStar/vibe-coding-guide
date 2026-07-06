# Planning Gate - Advisory Product Pool Schema Validator Skeleton

Date: 2026-07-05

Status: COMPLETED / VERIFIED

## Purpose

Create the first reusable schema and validation skeleton for advisory product
pools. This is the common substrate for later assignment advisors,
business-block advisors, and other specialized policy/question-answering
agents.

The slice keeps the interface above individual advisor calls:

- product objects carry common audit/scope/causality fields;
- role-specific payload fields are allowed at the code layer;
- runtime admission validates those payload fields through a registered
  validator profile before the product becomes usable.

## Scope

Implement a narrow runtime contract:

1. `AdvisoryProduct`
2. `AdvisoryPoolItem`
3. `AdvisoryProductValidationResult`
4. `AdvisoryProductValidatorRegistry`
5. default common validator
6. pool accept / emit helpers that return validation results
7. conversion to and from `ExchangeArtifact` structured payloads

## Acceptance Criteria

This gate closes only when:

1. A valid advisory product with free role-specific payload fields can be
   validated by the default common validator.
2. Missing required common fields produce readable validation errors.
3. A registered profile validator can reject role-specific payload fields.
4. Pool accept / emit helpers report accepted or rejected items without
   mutating scheduler state, Local Work Trajectory, delivery state, or provider
   state.
5. The product can round-trip through an `ExchangeArtifact` structured payload
   with exact `product_type` and `schema_version` markers.
6. Focused tests cover validation, profile dispatch, pool result shape, and
   artifact round-trip.

## Non-Goals

This gate does not:

1. implement automatic worker assignment;
2. implement assignment advisor execution;
3. implement business-block advisor execution;
4. create a persistent queue or daemon;
5. expose CLI or MCP surfaces;
6. add UI;
7. alter `trajectoryTeamContinuity`;
8. alter `ExchangeArtifact` storage semantics.

## Design Inputs

- `design_docs/advisory-product-pool-interface-design-record.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `docs/trajectory-team-continuity-surface.md`

## Implementation

Runtime:

- `src/runtime/orchestration/advisory_product_pool.py`
- exported from `src/runtime/orchestration/__init__.py`

Docs:

- `docs/advisory-product-pool.md`
- `docs/README.md`
- `design_docs/advisory-product-pool-interface-design-record.md`

Tests:

- `tests/test_runtime_orchestration.py`

## Verification

Focused validation:

```text
python -m py_compile src/runtime/orchestration/advisory_product_pool.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py

python -m pytest tests/test_runtime_orchestration.py -k "advisory_product" -q
5 passed, 461 deselected

python -m pytest tests/test_runtime_orchestration.py -k "advisory_product or exchange_" -q
42 passed, 424 deselected

git diff --check -- <touched files>
passed with Windows LF-to-CRLF warnings only

MCP GovernanceTools.analyze_changes for touched files:
impact direct/transitive empty; coupling alerts empty.
```

Note: the local tool invocation also printed an existing pack-lock warning:
`Pack 'doc-loop-vibe-coding' content changed since lock was recorded`. This is
not from the advisory product pool files and is not treated as this gate's
validation failure.
