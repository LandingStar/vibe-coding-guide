# Advisory Product Pool

## Purpose

The Advisory Product Pool contract is the first reusable runtime skeleton for
specialized advisory or policy agents.

It supports roles such as future assignment advisors and business-block
advisors without giving those roles direct authority over scheduler state,
Local Work Trajectory, delivery state, or provider execution.

## Runtime Surface

Current module:

```text
src/runtime/orchestration/advisory_product_pool.py
```

Exported runtime objects:

- `AdvisoryProduct`
- `AdvisoryPoolItem`
- `AdvisoryProductValidationResult`
- `AdvisoryProductValidatorRegistry`

Exported helpers:

- `validate_advisory_product_common`
- `accept_advisory_input`
- `emit_advisory_output`
- `advisory_product_to_artifact`
- `advisory_product_from_artifact`

Structured payload markers:

```text
product_type=advisory_product
schema_version=advisory-product-pool/v1
```

## Product Shape

`AdvisoryProduct` has common fields for audit, scope, causality, priority,
versioning, validation profile, logs, and decorators. Role-specific fields live
in `payload`.

The code layer may carry flexible `payload` fields. Runtime admission must
validate those fields through `AdvisoryProductValidatorRegistry` before a pool
item is considered accepted.

## Pool Items

`accept_advisory_input()` and `emit_advisory_output()` return an
`AdvisoryPoolItem`.

The item reports:

- `direction`: `input` or `output`
- `status`: `accepted` or `rejected`
- `validation`: structured errors and profile
- `authority_split`: confirms no scheduler, delivery, provider, exchange-store,
  or Local Work Trajectory mutation

These helpers are in-memory validation/readback surfaces. They do not create a
persistent queue, daemon, CLI, MCP tool, or worker assignment decision.

## ExchangeArtifact Bridge

`advisory_product_to_artifact()` stores an advisory product as a structured
payload inside an `ExchangeArtifact`. `advisory_product_from_artifact()` parses
exactly one such payload back.

This preserves `ExchangeArtifact` as the versioned coordination-product source
while giving advisory roles a reusable product class and validation boundary.

## Non-Goals

The current skeleton does not implement:

- automatic assignment policy;
- assignment advisor execution;
- business-block advisor execution;
- persistent advisory queues;
- CLI or MCP surfaces;
- UI binding;
- changes to `trajectoryTeamContinuity`.
