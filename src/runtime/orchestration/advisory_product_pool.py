"""Generic advisory product pool schema and validator skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Mapping

from .exchange import (
    ExchangeArtifact,
    ExchangeCausality,
    ExchangeLog,
    ExchangePayloadPart,
    ExchangeScope,
    VisibilityPolicy,
)

ADVISORY_PRODUCT_POOL_PRODUCT_TYPE = "advisory_product"
ADVISORY_PRODUCT_POOL_SCHEMA_VERSION = "advisory-product-pool/v1"

AdvisoryProductLifecycleState = Literal[
    "draft",
    "proposed",
    "accepted",
    "rejected",
    "consumed",
    "superseded",
    "archived",
]

AdvisoryPoolItemDirection = Literal["input", "output"]
AdvisoryPoolItemStatus = Literal["accepted", "rejected"]
AdvisoryValidator = Callable[["AdvisoryProduct"], tuple[str, ...]]

ADVISORY_PRODUCT_LIFECYCLE_STATES = {
    "draft",
    "proposed",
    "accepted",
    "rejected",
    "consumed",
    "superseded",
    "archived",
}


@dataclass(frozen=True, slots=True)
class AdvisoryProduct:
    """Reusable advisory/policy product with common and role-specific fields."""

    product_id: str
    product_class: str
    product_kind: str
    producer: str
    audience: tuple[str, ...] = ()
    scope: ExchangeScope = field(default_factory=ExchangeScope)
    causality: ExchangeCausality = field(default_factory=ExchangeCausality)
    lifecycle_state: AdvisoryProductLifecycleState = "draft"
    priority: int = 0
    created_at: str = ""
    updated_at: str = ""
    version: str = "v1"
    validation_profile: str = "common"
    common: Mapping[str, object] = field(default_factory=dict)
    payload: Mapping[str, object] = field(default_factory=dict)
    logs: tuple[ExchangeLog, ...] = ()
    decorators: Mapping[str, object] = field(default_factory=dict)

    def to_payload_dict(self) -> dict[str, object]:
        """Return the structured payload used inside ExchangeArtifact."""

        return {
            "product_type": ADVISORY_PRODUCT_POOL_PRODUCT_TYPE,
            "schema_version": ADVISORY_PRODUCT_POOL_SCHEMA_VERSION,
            "product_id": self.product_id,
            "product_class": self.product_class,
            "product_kind": self.product_kind,
            "producer": self.producer,
            "audience": list(self.audience),
            "scope": _scope_to_payload(self.scope),
            "causality": _causality_to_payload(self.causality),
            "lifecycle_state": self.lifecycle_state,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "validation_profile": self.validation_profile,
            "common": dict(self.common),
            "payload": dict(self.payload),
            "logs": [_log_to_payload(log) for log in self.logs],
            "decorators": dict(self.decorators),
        }


@dataclass(frozen=True, slots=True)
class AdvisoryProductValidationResult:
    """Non-raising validation result for advisory product admission."""

    product_id: str
    ok: bool
    validation_profile: str
    errors: tuple[str, ...] = ()

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "product_id": self.product_id,
            "ok": self.ok,
            "validation_profile": self.validation_profile,
            "errors": list(self.errors),
            "error_count": self.error_count,
        }


@dataclass(frozen=True, slots=True)
class AdvisoryPoolItem:
    """One accepted or rejected product in an advisory input/output pool."""

    pool_id: str
    direction: AdvisoryPoolItemDirection
    product: AdvisoryProduct
    validation: AdvisoryProductValidationResult
    item_id: str = ""
    owner_agent_id: str = ""
    role_kind: str = ""
    accepted_at: str = ""

    @property
    def status(self) -> AdvisoryPoolItemStatus:
        return "accepted" if self.validation.ok else "rejected"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "item_id": self.item_id,
            "pool_id": self.pool_id,
            "direction": self.direction,
            "status": self.status,
            "owner_agent_id": self.owner_agent_id,
            "role_kind": self.role_kind,
            "accepted_at": self.accepted_at,
            "product": self.product.to_payload_dict(),
            "validation": self.validation.to_json_dict(),
            "authority_split": {
                "scheduler_state_mutated": False,
                "local_work_trajectory_mutated": False,
                "delivery_state_mutated": False,
                "provider_executed": False,
                "exchange_store_mutated": False,
            },
        }


class AdvisoryProductValidatorRegistry:
    """Profile-keyed validator registry for role-specific advisory payloads."""

    def __init__(self) -> None:
        self._validators: dict[str, AdvisoryValidator] = {"common": validate_advisory_product_common}

    def register(self, profile: str, validator: AdvisoryValidator) -> None:
        if not profile:
            raise ValueError("advisory product validator profile must be non-empty")
        self._validators[profile] = validator

    def validate(self, product: AdvisoryProduct) -> AdvisoryProductValidationResult:
        errors = list(validate_advisory_product_common(product))
        if product.validation_profile != "common":
            validator = self._validators.get(product.validation_profile)
            if validator is None:
                errors.append(
                    "advisory product "
                    f"{product.product_id!r} references unregistered validation_profile "
                    f"{product.validation_profile!r}"
                )
            else:
                errors.extend(validator(product))
        return AdvisoryProductValidationResult(
            product_id=product.product_id,
            ok=not errors,
            validation_profile=product.validation_profile,
            errors=tuple(errors),
        )


def validate_advisory_product_common(product: AdvisoryProduct) -> tuple[str, ...]:
    """Validate fields common to every advisory product."""

    errors: list[str] = []
    if not product.product_id:
        errors.append("advisory product requires non-empty product_id")
    if not product.product_class:
        errors.append(
            f"advisory product {product.product_id!r} requires non-empty product_class"
        )
    if not product.product_kind:
        errors.append(
            f"advisory product {product.product_id!r} requires non-empty product_kind"
        )
    if not product.producer:
        errors.append(f"advisory product {product.product_id!r} requires non-empty producer")
    if not product.version:
        errors.append(f"advisory product {product.product_id!r} requires non-empty version")
    if not product.validation_profile:
        errors.append(
            f"advisory product {product.product_id!r} requires non-empty validation_profile"
        )
    if not isinstance(product.priority, int):
        errors.append(f"advisory product {product.product_id!r} priority must be an int")
    if product.lifecycle_state not in ADVISORY_PRODUCT_LIFECYCLE_STATES:
        errors.append(
            f"advisory product {product.product_id!r} has unsupported lifecycle_state "
            f"{product.lifecycle_state!r}; expected one of "
            f"{sorted(ADVISORY_PRODUCT_LIFECYCLE_STATES)!r}"
        )
    for index, log in enumerate(product.logs):
        if not log.timestamp:
            errors.append(
                f"advisory product {product.product_id!r} logs[{index}].timestamp is empty"
            )
        if not log.actor:
            errors.append(f"advisory product {product.product_id!r} logs[{index}].actor is empty")
        if not log.action:
            errors.append(
                f"advisory product {product.product_id!r} logs[{index}].action is empty"
            )
    return tuple(errors)


def accept_advisory_input(
    *,
    pool_id: str,
    product: AdvisoryProduct,
    registry: AdvisoryProductValidatorRegistry,
    item_id: str = "",
    owner_agent_id: str = "",
    role_kind: str = "",
    accepted_at: str = "",
) -> AdvisoryPoolItem:
    """Validate and represent one product entering an advisory input pool."""

    return _pool_item(
        pool_id=pool_id,
        direction="input",
        product=product,
        registry=registry,
        item_id=item_id,
        owner_agent_id=owner_agent_id,
        role_kind=role_kind,
        accepted_at=accepted_at,
    )


def emit_advisory_output(
    *,
    pool_id: str,
    product: AdvisoryProduct,
    registry: AdvisoryProductValidatorRegistry,
    item_id: str = "",
    owner_agent_id: str = "",
    role_kind: str = "",
    accepted_at: str = "",
) -> AdvisoryPoolItem:
    """Validate and represent one product leaving an advisory output pool."""

    return _pool_item(
        pool_id=pool_id,
        direction="output",
        product=product,
        registry=registry,
        item_id=item_id,
        owner_agent_id=owner_agent_id,
        role_kind=role_kind,
        accepted_at=accepted_at,
    )


def advisory_product_to_artifact(
    product: AdvisoryProduct,
    *,
    artifact_id: str = "",
    producer: str = "",
    version: str = "",
) -> ExchangeArtifact:
    """Encode an advisory product as a structured ExchangeArtifact payload."""

    artifact_identity = artifact_id or f"advisory-product:{product.product_id}"
    artifact_producer = producer or product.producer
    return ExchangeArtifact(
        artifact_id=artifact_identity,
        kind="proposal",
        intent="propose",
        producer=artifact_producer,
        audience=product.audience,
        scope=product.scope,
        causality=product.causality,
        lifecycle_state=product.lifecycle_state,
        visibility_policy=VisibilityPolicy(audience=product.audience),
        created_at=product.created_at,
        version=version or product.version,
        parts=(
            ExchangePayloadPart(
                part_type="structured",
                data=product.to_payload_dict(),
            ),
            *(
                ExchangePayloadPart(part_type="log", log=log)
                for log in product.logs
            ),
        ),
    )


def advisory_product_from_artifact(artifact: ExchangeArtifact) -> AdvisoryProduct:
    """Parse exactly one advisory product from an ExchangeArtifact."""

    matches = [
        part.data
        for part in artifact.parts
        if part.part_type == "structured"
        and part.data.get("product_type") == ADVISORY_PRODUCT_POOL_PRODUCT_TYPE
    ]
    if not matches:
        raise ValueError(
            f"exchange artifact {artifact.artifact_id!r} does not contain structured "
            f"product_type={ADVISORY_PRODUCT_POOL_PRODUCT_TYPE!r}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"exchange artifact {artifact.artifact_id!r} contains multiple "
            f"{ADVISORY_PRODUCT_POOL_PRODUCT_TYPE!r} payloads"
        )
    payload = matches[0]
    schema_version = payload.get("schema_version")
    if schema_version != ADVISORY_PRODUCT_POOL_SCHEMA_VERSION:
        raise ValueError(
            f"advisory product artifact {artifact.artifact_id!r} has unsupported "
            f"schema_version {schema_version!r}; expected "
            f"{ADVISORY_PRODUCT_POOL_SCHEMA_VERSION!r}"
        )
    return AdvisoryProduct(
        product_id=_required_str(payload, "product_id", artifact),
        product_class=_required_str(payload, "product_class", artifact),
        product_kind=_required_str(payload, "product_kind", artifact),
        producer=_required_str(payload, "producer", artifact),
        audience=_str_tuple(payload.get("audience"), "audience", artifact),
        scope=_scope_from_payload(payload.get("scope"), artifact),
        causality=_causality_from_payload(payload.get("causality"), artifact),
        lifecycle_state=_lifecycle_state_from_payload(payload, artifact),
        priority=_int_value(payload.get("priority"), "priority", artifact),
        created_at=str(payload.get("created_at", "") or ""),
        updated_at=str(payload.get("updated_at", "") or ""),
        version=_required_str(payload, "version", artifact),
        validation_profile=_required_str(payload, "validation_profile", artifact),
        common=_mapping(payload.get("common"), "common", artifact),
        payload=_mapping(payload.get("payload"), "payload", artifact),
        logs=_logs_from_payload(payload.get("logs"), artifact),
        decorators=_mapping(payload.get("decorators"), "decorators", artifact),
    )


def _pool_item(
    *,
    pool_id: str,
    direction: AdvisoryPoolItemDirection,
    product: AdvisoryProduct,
    registry: AdvisoryProductValidatorRegistry,
    item_id: str,
    owner_agent_id: str,
    role_kind: str,
    accepted_at: str,
) -> AdvisoryPoolItem:
    if not pool_id:
        raise ValueError("advisory pool item requires non-empty pool_id")
    validation = registry.validate(product)
    return AdvisoryPoolItem(
        pool_id=pool_id,
        direction=direction,
        product=product,
        validation=validation,
        item_id=item_id or f"{pool_id}:{direction}:{product.product_id}",
        owner_agent_id=owner_agent_id,
        role_kind=role_kind,
        accepted_at=accepted_at,
    )


def _required_str(
    payload: Mapping[str, object],
    key: str,
    artifact: ExchangeArtifact,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"advisory product artifact {artifact.artifact_id!r} requires non-empty "
            f"string field {key!r}"
        )
    return value


def _mapping(value: object, key: str, artifact: ExchangeArtifact) -> Mapping[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(
            f"advisory product artifact {artifact.artifact_id!r} field {key!r} "
            "must be an object"
        )
    return value


def _str_tuple(value: object, key: str, artifact: ExchangeArtifact) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"advisory product artifact {artifact.artifact_id!r} field {key!r} "
            "must be a list of strings"
        )
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(
                f"advisory product artifact {artifact.artifact_id!r} field {key!r} "
                f"item {index} must be a string"
            )
        result.append(item)
    return tuple(result)


def _int_value(value: object, key: str, artifact: ExchangeArtifact) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"advisory product artifact {artifact.artifact_id!r} field {key!r} "
            "must be an int"
        )
    return value


def _scope_to_payload(scope: ExchangeScope) -> dict[str, str]:
    return {
        "trajectory_id": scope.trajectory_id,
        "lane_id": scope.lane_id,
        "event_id": scope.event_id,
        "task_id": scope.task_id,
        "context_id": scope.context_id,
        "agent_id": scope.agent_id,
        "runtime_session_id": scope.runtime_session_id,
    }


def _scope_from_payload(value: object, artifact: ExchangeArtifact) -> ExchangeScope:
    payload = _mapping(value, "scope", artifact)
    return ExchangeScope(
        trajectory_id=str(payload.get("trajectory_id", "") or ""),
        lane_id=str(payload.get("lane_id", "") or ""),
        event_id=str(payload.get("event_id", "") or ""),
        task_id=str(payload.get("task_id", "") or ""),
        context_id=str(payload.get("context_id", "") or ""),
        agent_id=str(payload.get("agent_id", "") or ""),
        runtime_session_id=str(payload.get("runtime_session_id", "") or ""),
    )


def _causality_to_payload(causality: ExchangeCausality) -> dict[str, object]:
    return {
        "replies_to": list(causality.replies_to),
        "depends_on": list(causality.depends_on),
        "supersedes": list(causality.supersedes),
        "caused_by": list(causality.caused_by),
        "correlation_id": causality.correlation_id,
    }


def _causality_from_payload(value: object, artifact: ExchangeArtifact) -> ExchangeCausality:
    payload = _mapping(value, "causality", artifact)
    return ExchangeCausality(
        replies_to=_str_tuple(payload.get("replies_to"), "causality.replies_to", artifact),
        depends_on=_str_tuple(payload.get("depends_on"), "causality.depends_on", artifact),
        supersedes=_str_tuple(payload.get("supersedes"), "causality.supersedes", artifact),
        caused_by=_str_tuple(payload.get("caused_by"), "causality.caused_by", artifact),
        correlation_id=str(payload.get("correlation_id", "") or ""),
    )


def _log_to_payload(log: ExchangeLog) -> dict[str, object]:
    return {
        "timestamp": log.timestamp,
        "actor": log.actor,
        "action": log.action,
        "channel": log.channel,
        "summary": log.summary,
        "related_artifact_ids": list(log.related_artifact_ids),
        "related_event_ids": list(log.related_event_ids),
        "related_run_ids": list(log.related_run_ids),
        "sequence": log.sequence,
        "clock": log.clock,
    }


def _logs_from_payload(value: object, artifact: ExchangeArtifact) -> tuple[ExchangeLog, ...]:
    if value in (None, ""):
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"advisory product artifact {artifact.artifact_id!r} field 'logs' must be a list"
        )
    logs: list[ExchangeLog] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(
                f"advisory product artifact {artifact.artifact_id!r} logs[{index}] "
                "must be an object"
            )
        logs.append(
            ExchangeLog(
                timestamp=str(item.get("timestamp", "") or ""),
                actor=str(item.get("actor", "") or ""),
                action=str(item.get("action", "") or ""),
                channel=str(item.get("channel", "") or ""),
                summary=str(item.get("summary", "") or ""),
                related_artifact_ids=_str_tuple(
                    item.get("related_artifact_ids"),
                    f"logs[{index}].related_artifact_ids",
                    artifact,
                ),
                related_event_ids=_str_tuple(
                    item.get("related_event_ids"),
                    f"logs[{index}].related_event_ids",
                    artifact,
                ),
                related_run_ids=_str_tuple(
                    item.get("related_run_ids"),
                    f"logs[{index}].related_run_ids",
                    artifact,
                ),
                sequence=(
                    _int_value(item.get("sequence"), f"logs[{index}].sequence", artifact)
                    if item.get("sequence") is not None
                    else None
                ),
                clock=str(item.get("clock", "wall") or "wall"),  # type: ignore[arg-type]
            )
        )
    return tuple(logs)


def _lifecycle_state_from_payload(
    payload: Mapping[str, object],
    artifact: ExchangeArtifact,
) -> AdvisoryProductLifecycleState:
    value = str(payload.get("lifecycle_state", "draft") or "draft")
    if value not in ADVISORY_PRODUCT_LIFECYCLE_STATES:
        raise ValueError(
            f"advisory product artifact {artifact.artifact_id!r} has unsupported "
            f"lifecycle_state {value!r}; expected one of "
            f"{sorted(ADVISORY_PRODUCT_LIFECYCLE_STATES)!r}"
        )
    return value  # type: ignore[return-value]
