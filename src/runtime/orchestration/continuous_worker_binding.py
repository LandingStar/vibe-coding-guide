"""Provider-neutral durable continuous worker binding ledger.

The ledger records which worker identity should be reused for a task, agent,
lane, or lane group. It is project-owned coordination state and may point to a
provider-specific session selector, but it does not create sessions, execute
providers, mutate scheduler state, or write Local Work Trajectory.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Literal

from .runtime_adapter import RuntimeProviderKind


CONTINUOUS_WORKER_BINDING_LEDGER_SCHEMA_VERSION = "continuous-worker-binding-ledger.v1"
CONTINUOUS_WORKER_BINDING_EVENT_LOG_SCHEMA_VERSION = (
    "continuous-worker-binding-event-log.v1"
)
CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_SCHEMA_VERSION = (
    "continuous-worker-delivery-lease-ledger.v1"
)
CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_SCHEMA_VERSION = (
    "continuous-worker-delivery-lease-event-log.v1"
)
CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_SCHEMA_VERSION = (
    "continuous-worker-lane-ownership-ledger.v1"
)
CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_SCHEMA_VERSION = (
    "continuous-worker-lane-ownership-event-log.v1"
)
DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH = (
    ".codex/runtime/continuous-worker-bindings.json"
)
DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH = (
    ".codex/runtime/continuous-worker-binding-events.jsonl"
)
DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH = (
    ".codex/runtime/continuous-worker-delivery-leases.json"
)
DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH = (
    ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"
)
DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH = (
    ".codex/runtime/continuous-worker-lane-ownerships.json"
)
DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH = (
    ".codex/runtime/continuous-worker-lane-ownership-events.jsonl"
)

ContinuousWorkerScopeKind = Literal["lane", "lane_group", "agent", "task"]
ContinuousWorkerLifecycleStatus = Literal[
    "proposed",
    "claimed",
    "ready",
    "active",
    "idle",
    "compacting",
    "forked",
    "stale",
    "released",
    "archived",
]
LaneOwnershipScopeKind = Literal["lane", "lane_group"]
LaneOwnershipStatus = Literal[
    "claimed",
    "active",
    "suspended",
    "transferred",
    "released",
]
DeliveryLeaseStatus = Literal[
    "reserved",
    "running",
    "completed",
    "failed_retryable",
    "failed_terminal",
    "expired",
    "released",
]
CompactPolicyDefault = Literal["auto", "manual", "llm-auto"]
ContinuousWorkerBindingEventKind = Literal[
    "binding_claimed",
    "binding_reused",
    "binding_forked",
    "binding_compacted",
    "binding_released",
    "binding_marked_stale",
    "binding_archived",
]
DeliveryLeaseEventKind = Literal[
    "delivery_lease_reserved",
    "delivery_lease_started",
    "delivery_lease_completed",
    "delivery_lease_failed_retryable",
    "delivery_lease_failed_terminal",
    "delivery_lease_expired",
    "delivery_lease_released",
]
LaneOwnershipEventKind = Literal[
    "lane_ownership_claimed",
    "lane_ownership_activated",
    "lane_ownership_suspended",
    "lane_ownership_resumed",
    "lane_ownership_transferred",
    "lane_ownership_released",
]


@dataclass(frozen=True, slots=True)
class ContinuousWorkerSessionSelector:
    """Provider-specific host session selector carried by a worker binding."""

    provider: RuntimeProviderKind
    attach_url: str = ""
    session_id: str = ""
    continue_session: bool = False
    fork_session: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_no_raw_or_secret_fields(
            "worker binding session selector",
            self.session_id or self.attach_url,
            self.metadata,
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "attach_url": self.attach_url,
            "session_id": self.session_id,
            "continue_session": self.continue_session,
            "fork_session": self.fork_session,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class LaneOwnership:
    """Durable data-contract record mapping a lane/lane group to a binding."""

    ownership_id: str
    scope_kind: LaneOwnershipScopeKind
    scope_id: str
    lane_ids: tuple[str, ...]
    binding_id: str
    worker_id: str
    status: LaneOwnershipStatus = "claimed"
    replacement_binding_id: str = ""
    created_at: str = ""
    activated_at: str = ""
    updated_at: str = ""
    reason: str = ""
    audit_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_lane_ownership_scope_kind(
            self.scope_kind,
            ownership_id=self.ownership_id,
        )
        _validate_lane_ownership_status(
            self.status,
            ownership_id=self.ownership_id,
        )
        if not self.ownership_id:
            raise ValueError("lane ownership schema rejected: ownership_id is required")
        if not self.scope_id:
            raise ValueError(
                f"lane ownership schema rejected: scope_id is required ownership={self.ownership_id}"
            )
        if not self.binding_id:
            raise ValueError(
                f"lane ownership schema rejected: binding_id is required ownership={self.ownership_id}"
            )
        if not self.worker_id:
            raise ValueError(
                f"lane ownership schema rejected: worker_id is required ownership={self.ownership_id}"
            )
        if self.scope_kind == "lane_group" and not self.lane_ids:
            raise ValueError(
                "lane ownership schema rejected: lane_group requires lane_ids "
                f"ownership={self.ownership_id} binding={self.binding_id}"
            )
        if self.status == "transferred" and not self.replacement_binding_id:
            raise ValueError(
                "lane ownership schema rejected: transferred ownership requires "
                f"replacement_binding_id ownership={self.ownership_id} binding={self.binding_id}"
            )
        if self.scope_kind == "lane" and not self.lane_ids and self.scope_id:
            object.__setattr__(self, "lane_ids", (self.scope_id,))
        _validate_no_raw_or_secret_fields(
            "lane ownership",
            self.ownership_id,
            {
                "replacement_binding_id": self.replacement_binding_id,
                "reason": self.reason,
                "audit_refs": list(self.audit_refs),
            },
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ownership_id": self.ownership_id,
            "scope_kind": self.scope_kind,
            "scope_id": self.scope_id,
            "lane_ids": list(self.lane_ids),
            "binding_id": self.binding_id,
            "worker_id": self.worker_id,
            "status": self.status,
            "replacement_binding_id": self.replacement_binding_id,
            "created_at": self.created_at,
            "activated_at": self.activated_at,
            "updated_at": self.updated_at,
            "reason": self.reason,
            "audit_refs": list(self.audit_refs),
            "authority_split": _authority_split(ledger_mutated=False),
        }


@dataclass(frozen=True, slots=True)
class DeliveryLease:
    """Compact durable delivery lease record for one binding delivery attempt."""

    lease_id: str
    binding_id: str
    task_id: str
    delivery_id: str
    status: DeliveryLeaseStatus = "reserved"
    reserved_at: str = ""
    started_at: str = ""
    expires_at: str = ""
    completed_at: str = ""
    failed_at: str = ""
    failure_kind: str = ""
    result_ref: str = ""
    audit_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_delivery_lease_status(
            self.status,
            lease_id=self.lease_id,
            binding_id=self.binding_id,
            task_id=self.task_id,
        )
        if not self.lease_id:
            raise ValueError("delivery lease schema rejected: lease_id is required")
        if not self.binding_id:
            raise ValueError(
                f"delivery lease schema rejected: binding_id is required lease={self.lease_id}"
            )
        if not self.task_id:
            raise ValueError(
                "delivery lease schema rejected: task_id is required "
                f"lease={self.lease_id} binding={self.binding_id}"
            )
        if not self.delivery_id:
            raise ValueError(
                "delivery lease schema rejected: delivery_id is required "
                f"lease={self.lease_id} binding={self.binding_id} task={self.task_id}"
            )
        _validate_no_raw_or_secret_fields(
            "delivery lease",
            self.lease_id,
            {
                "failure_kind": self.failure_kind,
                "result_ref": self.result_ref,
                "audit_refs": list(self.audit_refs),
            },
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "lease_id": self.lease_id,
            "binding_id": self.binding_id,
            "task_id": self.task_id,
            "delivery_id": self.delivery_id,
            "status": self.status,
            "reserved_at": self.reserved_at,
            "started_at": self.started_at,
            "expires_at": self.expires_at,
            "completed_at": self.completed_at,
            "failed_at": self.failed_at,
            "failure_kind": self.failure_kind,
            "result_ref": self.result_ref,
            "audit_refs": list(self.audit_refs),
            "authority_split": _authority_split(ledger_mutated=False),
        }


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBinding:
    """One durable project-owned continuous worker binding."""

    binding_id: str
    worker_id: str
    runtime_provider: RuntimeProviderKind
    scope_kind: ContinuousWorkerScopeKind
    scope_id: str
    lane_ids: tuple[str, ...] = ()
    lifecycle_status: ContinuousWorkerLifecycleStatus = "active"
    active_session_selector: ContinuousWorkerSessionSelector | None = None
    generation: int = 1
    parent_binding_id: str = ""
    owned_lane_ids: tuple[str, ...] = ()
    private_storage_ref: str = ""
    private_storage_policy_ref: str = ""
    compact_policy_ref: str = ""
    compact_policy_default: CompactPolicyDefault = "auto"
    last_compact_at: str = ""
    compact_needed: bool = False
    created_at: str = ""
    updated_at: str = ""
    released_at: str = ""
    expires_at: str = ""
    last_used_at: str = ""
    compact_context_ref: str = ""
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_runtime_provider(self.runtime_provider)
        _validate_scope_kind(self.scope_kind)
        _validate_lifecycle_status(self.lifecycle_status, allow_active=True)
        _validate_compact_policy_default(
            self.compact_policy_default,
            binding_id=self.binding_id,
            metadata=self.metadata,
        )
        _validate_no_raw_or_secret_fields(
            "worker binding",
            self.binding_id,
            self.metadata,
        )
        if self.generation < 1:
            raise ValueError(
                f"worker binding schema rejected: generation must be >= 1 binding={self.binding_id}"
            )
        if not self.private_storage_ref and self.binding_id:
            object.__setattr__(
                self,
                "private_storage_ref",
                _default_private_storage_ref(self.binding_id),
            )
        if not self.private_storage_policy_ref:
            object.__setattr__(
                self,
                "private_storage_policy_ref",
                _default_private_storage_policy_ref(),
            )
        if not self.owned_lane_ids:
            object.__setattr__(self, "owned_lane_ids", _unique_nonempty(self.lane_ids))

    def to_json_dict(self) -> dict[str, object]:
        return {
            "binding_id": self.binding_id,
            "worker_id": self.worker_id,
            "runtime_provider": self.runtime_provider,
            "scope_kind": self.scope_kind,
            "scope_id": self.scope_id,
            "lane_ids": list(self.lane_ids),
            "lifecycle_status": self.lifecycle_status,
            "active_session_selector": (
                None
                if self.active_session_selector is None
                else self.active_session_selector.to_json_dict()
            ),
            "generation": self.generation,
            "parent_binding_id": self.parent_binding_id,
            "owned_lane_ids": list(self.owned_lane_ids),
            "private_storage_ref": self.private_storage_ref,
            "private_storage_policy_ref": self.private_storage_policy_ref,
            "compact_policy_ref": self.compact_policy_ref,
            "compact_policy_default": self.compact_policy_default,
            "last_compact_at": self.last_compact_at,
            "compact_needed": self.compact_needed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "released_at": self.released_at,
            "expires_at": self.expires_at,
            "last_used_at": self.last_used_at,
            "compact_context_ref": self.compact_context_ref,
            "mailbox_cursor_ref": self.mailbox_cursor_ref,
            "worker_report_refs": list(self.worker_report_refs),
            "audit_refs": list(self.audit_refs),
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingLedger:
    """Durable continuous worker binding ledger."""

    bindings: tuple[ContinuousWorkerBinding, ...] = ()
    schema_version: str = CONTINUOUS_WORKER_BINDING_LEDGER_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "bindings": [binding.to_json_dict() for binding in self.bindings],
            "authority_split": _authority_split(ledger_mutated=False),
        }


@dataclass(frozen=True, slots=True)
class LaneOwnershipLedger:
    """Durable lane ownership ledger."""

    ownerships: tuple[LaneOwnership, ...] = ()
    schema_version: str = CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_no_selectable_lane_ownership_conflicts(self.ownerships)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "ownerships": [
                ownership.to_json_dict() for ownership in self.ownerships
            ],
            "authority_split": _authority_split(ledger_mutated=False),
        }


@dataclass(frozen=True, slots=True)
class DeliveryLeaseLedger:
    """Durable compact delivery lease ledger."""

    leases: tuple[DeliveryLease, ...] = ()
    schema_version: str = CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_no_active_delivery_lease_conflicts(self.leases)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "leases": [lease.to_json_dict() for lease in self.leases],
            "authority_split": _authority_split(ledger_mutated=False),
        }


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingEventRecord:
    """Append-only compact lifecycle event for one continuous worker binding."""

    event_id: str
    event_kind: ContinuousWorkerBindingEventKind
    timestamp: str
    binding_id: str
    worker_id: str = ""
    runtime_provider: str = ""
    scope_kind: str = ""
    scope_id: str = ""
    previous_status: str = ""
    next_status: str = ""
    reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": CONTINUOUS_WORKER_BINDING_EVENT_LOG_SCHEMA_VERSION,
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "timestamp": self.timestamp,
            "binding_id": self.binding_id,
            "worker_id": self.worker_id,
            "runtime_provider": self.runtime_provider,
            "scope_kind": self.scope_kind,
            "scope_id": self.scope_id,
            "previous_status": self.previous_status,
            "next_status": self.next_status,
            "reason": self.reason,
            "metadata": dict(self.metadata),
            "authority_split": _authority_split(ledger_mutated=True),
        }


@dataclass(frozen=True, slots=True)
class LaneOwnershipEventRecord:
    """Append-only compact lifecycle event for one lane ownership record."""

    event_id: str
    event_kind: LaneOwnershipEventKind
    timestamp: str
    ownership_id: str
    scope_kind: str
    scope_id: str
    binding_id: str
    previous_status: str = ""
    next_status: str = ""
    reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_no_raw_or_secret_fields(
            "lane ownership event",
            self.event_id,
            self.metadata,
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_SCHEMA_VERSION,
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "timestamp": self.timestamp,
            "ownership_id": self.ownership_id,
            "scope_kind": self.scope_kind,
            "scope_id": self.scope_id,
            "binding_id": self.binding_id,
            "previous_status": self.previous_status,
            "next_status": self.next_status,
            "reason": self.reason,
            "metadata": dict(self.metadata),
            "authority_split": _authority_split(ledger_mutated=True),
        }


@dataclass(frozen=True, slots=True)
class DeliveryLeaseEventRecord:
    """Append-only compact lifecycle event for one delivery lease."""

    event_id: str
    event_kind: DeliveryLeaseEventKind
    timestamp: str
    lease_id: str
    binding_id: str
    task_id: str = ""
    delivery_id: str = ""
    previous_status: str = ""
    next_status: str = ""
    reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_no_raw_or_secret_fields(
            "delivery lease event",
            self.event_id,
            self.metadata,
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_SCHEMA_VERSION,
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "timestamp": self.timestamp,
            "lease_id": self.lease_id,
            "binding_id": self.binding_id,
            "task_id": self.task_id,
            "delivery_id": self.delivery_id,
            "previous_status": self.previous_status,
            "next_status": self.next_status,
            "reason": self.reason,
            "metadata": dict(self.metadata),
            "authority_split": _authority_split(ledger_mutated=True),
        }


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingClaimRequest:
    """Request to claim or update one continuous worker binding."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    worker_id: str = ""
    runtime_provider: RuntimeProviderKind = "opencode"
    scope_kind: ContinuousWorkerScopeKind = "lane"
    scope_id: str = ""
    lane_ids: tuple[str, ...] = ()
    binding_id: str = ""
    lifecycle_status: ContinuousWorkerLifecycleStatus = "active"
    active_session_selector: ContinuousWorkerSessionSelector | None = None
    generation: int = 1
    parent_binding_id: str = ""
    owned_lane_ids: tuple[str, ...] = ()
    private_storage_ref: str = ""
    private_storage_policy_ref: str = ""
    compact_policy_ref: str = ""
    compact_policy_default: CompactPolicyDefault = "auto"
    last_compact_at: str = ""
    compact_needed: bool = False
    timestamp: str = ""
    expires_at: str = ""
    last_used_at: str = ""
    compact_context_ref: str = ""
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    reason: str = ""
    replace_existing: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ServerApiCreatedSessionPromotionRequest:
    """Promote one explicit server/API-created session into a worker binding."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    session_selector_source: str = "server_api_created"
    provider: RuntimeProviderKind = "opencode"
    attach_url: str = ""
    session_id: str = ""
    worker_id: str = ""
    scope_kind: ContinuousWorkerScopeKind = "lane"
    scope_id: str = ""
    lane_ids: tuple[str, ...] = ()
    binding_id: str = ""
    compact_context_ref: str = ""
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    timestamp: str = ""
    expires_at: str = ""
    reason: str = "server/API-created OpenCode session promoted"
    replace_existing: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingReleaseRequest:
    """Request to release, stale, or archive one binding."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    binding_id: str = ""
    scope_kind: ContinuousWorkerScopeKind | str = ""
    scope_id: str = ""
    lifecycle_status: ContinuousWorkerLifecycleStatus = "released"
    timestamp: str = ""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingInspectRequest:
    """Read-only continuous worker binding inspection request."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    runtime_provider: RuntimeProviderKind | str = ""
    scope_kind: ContinuousWorkerScopeKind | str = ""
    scope_id: str = ""
    worker_id: str = ""
    lane_id: str = ""
    include_inactive: bool = False


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingRecoverStaleRequest:
    """Request to mark elapsed bindings stale by explicit timestamp policy."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    now: str = ""
    timestamp: str = ""
    reason: str = "continuous worker binding stale recovery"


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingReuseRequest:
    """Request to record that delivery reused one binding."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    binding_id: str = ""
    task_id: str = ""
    agent_id: str = ""
    lane_id: str = ""
    timestamp: str = ""
    reason: str = "continuous worker binding reused for delivery"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingForkRequest:
    """Request to derive a new binding from an existing active binding."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    source_binding_id: str = ""
    new_binding_id: str = ""
    worker_id: str = ""
    scope_kind: ContinuousWorkerScopeKind = "lane"
    scope_id: str = ""
    lane_ids: tuple[str, ...] = ()
    active_session_selector: ContinuousWorkerSessionSelector | None = None
    generation: int = 0
    private_storage_ref: str = ""
    private_storage_policy_ref: str = ""
    compact_policy_ref: str = ""
    compact_policy_default: CompactPolicyDefault = "auto"
    compact_needed: bool = False
    timestamp: str = ""
    expires_at: str = ""
    compact_context_ref: str = ""
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    reason: str = "continuous worker binding forked"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingCompactRequest:
    """Request to attach a new project-owned compact context snapshot."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    binding_id: str = ""
    scope_kind: ContinuousWorkerScopeKind | str = ""
    scope_id: str = ""
    compact_context_ref: str = ""
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    timestamp: str = ""
    reason: str = "continuous worker binding compacted"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingResolveRequest:
    """Resolve the active binding for one delivery-time task context."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    runtime_provider: RuntimeProviderKind = "opencode"
    task_id: str = ""
    agent_id: str = ""
    lane_id: str = ""
    timestamp: str = ""


@dataclass(frozen=True, slots=True)
class LaneOwnershipClaimRequest:
    """Claim one lane or lane group for a continuous worker binding."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    ownership_id: str = ""
    scope_kind: LaneOwnershipScopeKind = "lane"
    scope_id: str = ""
    lane_ids: tuple[str, ...] = ()
    binding_id: str = ""
    worker_id: str = ""
    timestamp: str = ""
    requested_by: str = "host:continuous-worker-lane-ownership"
    reason: str = "lane ownership claimed"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LaneOwnershipActivateRequest:
    """Activate a claimed lane ownership after first successful delivery."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    ownership_id: str = ""
    binding_id: str = ""
    activated_at: str = ""
    delivery_id: str = ""
    task_id: str = ""
    reason: str = "lane ownership activated"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LaneOwnershipSuspendRequest:
    """Suspend active lane ownership without releasing it."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    ownership_id: str = ""
    binding_id: str = ""
    timestamp: str = ""
    reason: str = "lane ownership suspended"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LaneOwnershipResumeRequest:
    """Resume suspended lane ownership."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    ownership_id: str = ""
    binding_id: str = ""
    timestamp: str = ""
    reason: str = "lane ownership resumed"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LaneOwnershipTransferRequest:
    """Transfer lane ownership to a replacement binding."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    ownership_id: str = ""
    binding_id: str = ""
    replacement_binding_id: str = ""
    timestamp: str = ""
    reason: str = "lane ownership transferred"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LaneOwnershipReleaseRequest:
    """Release lane ownership."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    ownership_id: str = ""
    binding_id: str = ""
    timestamp: str = ""
    reason: str = "lane ownership released"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LaneOwnershipInspectRequest:
    """Read-only lane ownership inspection request."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    ownership_id: str = ""
    scope_kind: LaneOwnershipScopeKind | str = ""
    scope_id: str = ""
    lane_id: str = ""
    binding_id: str = ""
    worker_id: str = ""
    include_inactive: bool = False


@dataclass(frozen=True, slots=True)
class LaneOwnershipResult:
    """Result for lane ownership ledger operations."""

    ok: bool
    action: str
    ledger_path: Path
    ownership: LaneOwnership | None = None
    ownerships: tuple[LaneOwnership, ...] = ()
    status: str = ""
    message: str = ""
    ledger_mutated: bool = False
    selectable: bool = False
    event_records: tuple[LaneOwnershipEventRecord, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "ledger_path": str(self.ledger_path),
            "ownership": (
                None if self.ownership is None else self.ownership.to_json_dict()
            ),
            "ownerships": [
                ownership.to_json_dict() for ownership in self.ownerships
            ],
            "selectable": self.selectable,
            "events": [event.to_json_dict() for event in self.event_records],
            "authority_split": _authority_split(ledger_mutated=self.ledger_mutated),
        }


@dataclass(frozen=True, slots=True)
class DeliveryLeaseReserveRequest:
    """Reserve a continuous worker binding for one delivery attempt."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH
    lease_id: str = ""
    binding_id: str = ""
    task_id: str = ""
    delivery_id: str = ""
    reserved_at: str = ""
    expires_at: str = ""
    reason: str = "continuous worker delivery lease reserved"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeliveryLeaseBeginRequest:
    """Mark a reserved delivery lease running."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH
    lease_id: str = ""
    binding_id: str = ""
    started_at: str = ""
    reason: str = "continuous worker delivery lease run started"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeliveryLeaseCompleteRequest:
    """Mark a running delivery lease completed."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH
    lease_id: str = ""
    binding_id: str = ""
    completed_at: str = ""
    result_ref: str = ""
    reason: str = "continuous worker delivery lease completed"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeliveryLeaseFailRequest:
    """Mark an active delivery lease failed."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH
    lease_id: str = ""
    binding_id: str = ""
    failed_at: str = ""
    failure_kind: str = ""
    result_ref: str = ""
    reason: str = "continuous worker delivery lease failed"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeliveryLeaseExpireRequest:
    """Mark an active delivery lease expired by host-owned recovery."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH
    lease_id: str = ""
    binding_id: str = ""
    observed_at: str = ""
    reason: str = "continuous worker delivery lease expired"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeliveryLeaseReleaseRequest:
    """Mark an inactive delivery lease released and available for a new reserve."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH
    event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH
    lease_id: str = ""
    binding_id: str = ""
    released_at: str = ""
    reason: str = "continuous worker delivery lease released"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeliveryLeaseInspectRequest:
    """Read-only delivery lease inspection request."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH
    binding_id: str = ""
    task_id: str = ""
    delivery_id: str = ""
    lease_id: str = ""
    include_inactive: bool = True


@dataclass(frozen=True, slots=True)
class DeliveryLeaseResult:
    """Result for delivery lease ledger operations."""

    ok: bool
    action: str
    ledger_path: Path
    lease: DeliveryLease | None = None
    leases: tuple[DeliveryLease, ...] = ()
    status: str = ""
    message: str = ""
    ledger_mutated: bool = False
    event_records: tuple[DeliveryLeaseEventRecord, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "ledger_path": str(self.ledger_path),
            "lease": None if self.lease is None else self.lease.to_json_dict(),
            "leases": [lease.to_json_dict() for lease in self.leases],
            "events": [event.to_json_dict() for event in self.event_records],
            "authority_split": _authority_split(ledger_mutated=self.ledger_mutated),
        }


@dataclass(frozen=True, slots=True)
class ContinuousWorkerBindingResult:
    """Result for continuous worker binding ledger operations."""

    ok: bool
    action: str
    ledger_path: Path
    binding: ContinuousWorkerBinding | None = None
    bindings: tuple[ContinuousWorkerBinding, ...] = ()
    status: str = ""
    message: str = ""
    ledger_mutated: bool = False
    checked_count: int = 0
    stale_count: int = 0
    stale_reasons: Mapping[str, str] = field(default_factory=dict)
    selector_source: str = ""
    event_records: tuple[ContinuousWorkerBindingEventRecord, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "ledger_path": str(self.ledger_path),
            "binding": None if self.binding is None else self.binding.to_json_dict(),
            "bindings": [binding.to_json_dict() for binding in self.bindings],
            "checked_count": self.checked_count,
            "stale_count": self.stale_count,
            "stale_reasons": dict(self.stale_reasons),
            "selector_source": self.selector_source,
            "events": [event.to_json_dict() for event in self.event_records],
            "authority_split": _authority_split(ledger_mutated=self.ledger_mutated),
        }


@dataclass(frozen=True, slots=True)
class ServerApiCreatedSessionPromotionResult:
    """Result for explicit server/API-created session promotion."""

    ok: bool
    action: str
    ledger_path: Path
    binding_result: ContinuousWorkerBindingResult
    binding: ContinuousWorkerBinding | None = None
    status: str = ""
    message: str = ""
    promotion_source: str = "server_api_created"
    provider: str = "opencode"
    binding_claimed: bool = False

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "ledger_path": str(self.ledger_path),
            "promotion_source": self.promotion_source,
            "provider": self.provider,
            "binding_claimed": self.binding_claimed,
            "binding": None if self.binding is None else self.binding.to_json_dict(),
            "binding_result": self.binding_result.to_json_dict(),
            "authority_split": {
                **_authority_split(ledger_mutated=self.binding_result.ledger_mutated),
                "provider_executed": False,
                "delivery_state_mutated": False,
                "runtime_invocation_log_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


class JsonlContinuousWorkerBindingEventLog:
    """Append-only JSONL store for continuous worker binding events."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        record: ContinuousWorkerBindingEventRecord,
    ) -> ContinuousWorkerBindingEventRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_json_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return record

    def read_all(self) -> tuple[ContinuousWorkerBindingEventRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[ContinuousWorkerBindingEventRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(
                        continuous_worker_binding_event_record_from_json_dict(
                            json.loads(stripped)
                        )
                    )
                except Exception as exc:
                    raise ValueError(
                        f"invalid continuous worker binding event log line "
                        f"{line_number} in {self.path}: {exc}"
                    ) from exc
        return tuple(records)


class JsonlLaneOwnershipEventLog:
    """Append-only JSONL store for lane ownership events."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        record: LaneOwnershipEventRecord,
    ) -> LaneOwnershipEventRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_json_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return record

    def read_all(self) -> tuple[LaneOwnershipEventRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[LaneOwnershipEventRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(
                        lane_ownership_event_record_from_json_dict(json.loads(stripped))
                    )
                except Exception as exc:
                    raise ValueError(
                        f"invalid lane ownership event log line "
                        f"{line_number} in {self.path}: {exc}"
                    ) from exc
        return tuple(records)


class JsonlDeliveryLeaseEventLog:
    """Append-only JSONL store for delivery lease events."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        record: DeliveryLeaseEventRecord,
    ) -> DeliveryLeaseEventRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_json_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return record

    def read_all(self) -> tuple[DeliveryLeaseEventRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[DeliveryLeaseEventRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(
                        delivery_lease_event_record_from_json_dict(json.loads(stripped))
                    )
                except Exception as exc:
                    raise ValueError(
                        f"invalid delivery lease event log line "
                        f"{line_number} in {self.path}: {exc}"
                    ) from exc
        return tuple(records)


def claim_continuous_worker_binding(
    request: ContinuousWorkerBindingClaimRequest,
) -> ContinuousWorkerBindingResult:
    """Create or replace one active continuous worker binding."""

    if not request.worker_id:
        raise ValueError("continuous worker binding claim requires worker_id")
    _validate_runtime_provider(request.runtime_provider)
    _validate_scope_kind(request.scope_kind)
    _validate_lifecycle_status(request.lifecycle_status, allow_active=True)
    if request.lifecycle_status not in {"active", "idle"}:
        raise ValueError("continuous worker binding claim status must be active or idle")
    if not request.scope_id:
        raise ValueError("continuous worker binding claim requires scope_id")
    if request.scope_kind == "lane" and not request.lane_ids and request.scope_id:
        lane_ids = (request.scope_id,)
    else:
        lane_ids = _unique_nonempty(request.lane_ids)
    if request.scope_kind == "lane_group" and not lane_ids:
        raise ValueError("lane_group continuous worker binding requires lane_ids")
    if request.active_session_selector is not None:
        _validate_session_selector(
            request.active_session_selector,
            expected_provider=request.runtime_provider,
        )
    _validate_compact_policy_default(
        request.compact_policy_default,
        binding_id=request.binding_id or _binding_id(request.scope_kind, request.scope_id),
        metadata=request.metadata,
    )
    _validate_no_raw_or_secret_fields(
        "worker binding",
        request.binding_id or _binding_id(request.scope_kind, request.scope_id),
        request.metadata,
    )

    ledger_path = Path(request.ledger_path)
    ledger = read_continuous_worker_binding_ledger(ledger_path)
    binding_id = request.binding_id or _binding_id(request.scope_kind, request.scope_id)
    existing = [
        binding
        for binding in ledger.bindings
        if binding.binding_id == binding_id
        or (
            binding.scope_kind == request.scope_kind
            and binding.scope_id == request.scope_id
            and _binding_active(binding)
        )
    ]
    if existing and not request.replace_existing:
        return ContinuousWorkerBindingResult(
            ok=False,
            action="claim",
            ledger_path=ledger_path,
            binding=existing[0],
            bindings=ledger.bindings,
            status="conflict",
            message="active continuous worker binding already exists for this scope",
            ledger_mutated=False,
        )

    binding = ContinuousWorkerBinding(
        binding_id=binding_id,
        worker_id=request.worker_id,
        runtime_provider=request.runtime_provider,
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
        lane_ids=lane_ids,
        lifecycle_status=request.lifecycle_status,
        active_session_selector=request.active_session_selector,
        generation=request.generation,
        parent_binding_id=request.parent_binding_id,
        owned_lane_ids=_unique_nonempty(request.owned_lane_ids or lane_ids),
        private_storage_ref=request.private_storage_ref,
        private_storage_policy_ref=request.private_storage_policy_ref,
        compact_policy_ref=request.compact_policy_ref,
        compact_policy_default=request.compact_policy_default,
        last_compact_at=request.last_compact_at,
        compact_needed=request.compact_needed,
        created_at=request.timestamp,
        updated_at=request.timestamp,
        expires_at=request.expires_at,
        last_used_at=request.last_used_at or request.timestamp,
        compact_context_ref=request.compact_context_ref,
        mailbox_cursor_ref=request.mailbox_cursor_ref,
        worker_report_refs=_unique_nonempty(request.worker_report_refs),
        audit_refs=_unique_nonempty(request.audit_refs),
        reason=request.reason,
        metadata=dict(request.metadata),
    )
    retained = tuple(
        old
        for old in ledger.bindings
        if old.binding_id != binding_id
        and not (
            old.scope_kind == request.scope_kind
            and old.scope_id == request.scope_id
            and _binding_active(old)
        )
    )
    updated = ContinuousWorkerBindingLedger(bindings=(*retained, binding))
    write_continuous_worker_binding_ledger(updated, ledger_path)
    event = _append_binding_event(
        request.event_log_path,
        event_kind="binding_claimed",
        timestamp=request.timestamp,
        binding=binding,
        previous_status=existing[0].lifecycle_status if existing else "",
        next_status=binding.lifecycle_status,
        reason=request.reason,
        metadata={
            "replace_existing": request.replace_existing,
            "promotion_source": request.metadata.get("promotion_source", ""),
            "session_selector_source": request.metadata.get("session_selector_source", ""),
            "promotion_authority": request.metadata.get("promotion_authority", ""),
        },
    )
    return ContinuousWorkerBindingResult(
        ok=True,
        action="claim",
        ledger_path=ledger_path,
        binding=binding,
        bindings=updated.bindings,
        status="claimed",
        message="continuous worker binding claimed",
        ledger_mutated=True,
        event_records=(event,),
    )


def promote_server_api_created_session_to_continuous_worker_binding(
    request: ServerApiCreatedSessionPromotionRequest,
) -> ServerApiCreatedSessionPromotionResult:
    """Claim a continuous worker binding from an explicit server/API session."""

    _validate_server_api_created_session_promotion_request(request)
    lane_ids = (
        (request.scope_id,)
        if request.scope_kind == "lane" and not request.lane_ids
        else _unique_nonempty(request.lane_ids)
    )
    selector = ContinuousWorkerSessionSelector(
        provider=request.provider,
        attach_url=request.attach_url.rstrip("/"),
        session_id=request.session_id,
        metadata={
            "promotion_source": "server_api_created",
            "session_selector_source": request.session_selector_source,
        },
    )
    promotion_metadata = {
        **dict(request.metadata),
        "promotion_source": "server_api_created",
        "session_selector_source": request.session_selector_source,
        "session_persistence": "promoted_to_continuous_worker_binding",
        "promotion_authority": "explicit_host_owned_claim",
        "provider": request.provider,
    }
    claim = claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=request.ledger_path,
            event_log_path=request.event_log_path,
            worker_id=request.worker_id,
            runtime_provider=request.provider,
            scope_kind=request.scope_kind,
            scope_id=request.scope_id,
            lane_ids=lane_ids,
            binding_id=request.binding_id,
            active_session_selector=selector,
            compact_context_ref=request.compact_context_ref,
            mailbox_cursor_ref=request.mailbox_cursor_ref,
            worker_report_refs=_unique_nonempty(request.worker_report_refs),
            audit_refs=_unique_nonempty(request.audit_refs),
            timestamp=request.timestamp,
            expires_at=request.expires_at,
            reason=request.reason,
            replace_existing=request.replace_existing,
            metadata=promotion_metadata,
        )
    )
    return ServerApiCreatedSessionPromotionResult(
        ok=claim.ok,
        action="promote_server_api_created_session",
        ledger_path=Path(request.ledger_path),
        binding_result=claim,
        binding=claim.binding,
        status="promoted" if claim.ok else claim.status,
        message=(
            "server/API-created session promoted to continuous worker binding"
            if claim.ok
            else claim.message
        ),
        promotion_source="server_api_created",
        provider=request.provider,
        binding_claimed=claim.ok and claim.binding is not None,
    )


def release_continuous_worker_binding(
    request: ContinuousWorkerBindingReleaseRequest,
) -> ContinuousWorkerBindingResult:
    """Mark one active binding released, stale, or archived."""

    _validate_lifecycle_status(request.lifecycle_status, allow_active=False)
    if request.lifecycle_status not in {"released", "stale", "archived"}:
        raise ValueError(
            "continuous worker binding release status must be released, stale, or archived"
        )
    ledger_path = Path(request.ledger_path)
    ledger = read_continuous_worker_binding_ledger(ledger_path)
    target = _find_binding(
        ledger,
        binding_id=request.binding_id,
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
        include_inactive=False,
    )
    if target is None:
        return ContinuousWorkerBindingResult(
            ok=False,
            action="release",
            ledger_path=ledger_path,
            bindings=ledger.bindings,
            status="not_found",
            message="active continuous worker binding not found",
            ledger_mutated=False,
        )
    released = replace(
        target,
        lifecycle_status=request.lifecycle_status,
        updated_at=request.timestamp,
        released_at=request.timestamp,
        reason=request.reason or target.reason,
    )
    updated = ContinuousWorkerBindingLedger(
        bindings=tuple(
            released if binding.binding_id == target.binding_id else binding
            for binding in ledger.bindings
        )
    )
    write_continuous_worker_binding_ledger(updated, ledger_path)
    event = _append_binding_event(
        request.event_log_path,
        event_kind=_release_event_kind(request.lifecycle_status),
        timestamp=request.timestamp,
        binding=released,
        previous_status=target.lifecycle_status,
        next_status=request.lifecycle_status,
        reason=request.reason or target.reason,
    )
    return ContinuousWorkerBindingResult(
        ok=True,
        action="release",
        ledger_path=ledger_path,
        binding=released,
        bindings=updated.bindings,
        status=request.lifecycle_status,
        message=f"continuous worker binding marked {request.lifecycle_status}",
        ledger_mutated=True,
        event_records=(event,),
    )


def inspect_continuous_worker_bindings(
    request: ContinuousWorkerBindingInspectRequest,
) -> ContinuousWorkerBindingResult:
    """Inspect continuous worker bindings without mutation."""

    ledger_path = Path(request.ledger_path)
    ledger = read_continuous_worker_binding_ledger(ledger_path)
    bindings = ledger.bindings
    if request.runtime_provider:
        bindings = tuple(
            binding
            for binding in bindings
            if binding.runtime_provider == request.runtime_provider
        )
    if request.scope_kind:
        bindings = tuple(
            binding for binding in bindings if binding.scope_kind == request.scope_kind
        )
    if request.scope_id:
        bindings = tuple(binding for binding in bindings if binding.scope_id == request.scope_id)
    if request.worker_id:
        bindings = tuple(binding for binding in bindings if binding.worker_id == request.worker_id)
    if request.lane_id:
        bindings = tuple(
            binding
            for binding in bindings
            if request.lane_id == binding.scope_id
            or request.lane_id in binding.lane_ids
        )
    if not request.include_inactive:
        bindings = tuple(binding for binding in bindings if _binding_active(binding))
    return ContinuousWorkerBindingResult(
        ok=True,
        action="inspect",
        ledger_path=ledger_path,
        bindings=bindings,
        status="inspected",
        message=f"{len(bindings)} continuous worker binding(s) matched",
        ledger_mutated=False,
    )


def recover_stale_continuous_worker_bindings(
    request: ContinuousWorkerBindingRecoverStaleRequest,
) -> ContinuousWorkerBindingResult:
    """Mark active bindings stale when their expires_at is elapsed."""

    if not request.now:
        raise ValueError("continuous worker binding stale recovery requires now")
    now = _parse_timestamp(request.now, "now")
    ledger_path = Path(request.ledger_path)
    ledger = read_continuous_worker_binding_ledger(ledger_path)
    stale_ids: set[str] = set()
    stale_reasons: dict[str, str] = {}
    checked = 0
    for binding in ledger.bindings:
        if not _binding_active(binding):
            continue
        checked += 1
        reason = _binding_stale_reason_by_expiry(binding, now)
        if reason:
            stale_ids.add(binding.binding_id)
            stale_reasons[binding.binding_id] = reason
    if not stale_ids:
        return ContinuousWorkerBindingResult(
            ok=True,
            action="recover-stale",
            ledger_path=ledger_path,
            bindings=ledger.bindings,
            status="no_stale_bindings",
            message="No stale continuous worker bindings matched the recovery policy",
            ledger_mutated=False,
            checked_count=checked,
        )

    timestamp = request.timestamp or request.now
    updated_bindings = tuple(
        replace(
            binding,
            lifecycle_status="stale",
            updated_at=timestamp,
            released_at=timestamp,
            reason=stale_reasons[binding.binding_id],
        )
        if binding.binding_id in stale_ids
        else binding
        for binding in ledger.bindings
    )
    updated = ContinuousWorkerBindingLedger(bindings=updated_bindings)
    write_continuous_worker_binding_ledger(updated, ledger_path)
    stale = tuple(binding for binding in updated_bindings if binding.binding_id in stale_ids)
    event_log = JsonlContinuousWorkerBindingEventLog(request.event_log_path)
    existing_event_count = len(event_log.read_all())
    events: list[ContinuousWorkerBindingEventRecord] = []
    for binding in stale:
        event = _binding_event_record(
            event_index=existing_event_count + len(events) + 1,
            event_kind="binding_marked_stale",
            timestamp=timestamp,
            binding=binding,
            previous_status="active",
            next_status="stale",
            reason=stale_reasons[binding.binding_id],
        )
        event_log.append(event)
        events.append(event)
    return ContinuousWorkerBindingResult(
        ok=True,
        action="recover-stale",
        ledger_path=ledger_path,
        bindings=stale,
        status="stale_bindings_marked",
        message=f"Marked {len(stale)} continuous worker binding(s) stale",
        ledger_mutated=True,
        checked_count=checked,
        stale_count=len(stale),
        stale_reasons=stale_reasons,
        event_records=tuple(events),
    )


def record_continuous_worker_binding_reuse(
    request: ContinuousWorkerBindingReuseRequest,
) -> ContinuousWorkerBindingResult:
    """Record delivery-time reuse and update last_used_at/audit refs."""

    if not request.binding_id:
        raise ValueError("continuous worker binding reuse requires binding_id")
    _validate_no_raw_or_secret_fields(
        "worker binding",
        request.binding_id,
        request.metadata,
    )
    ledger_path = Path(request.ledger_path)
    ledger = read_continuous_worker_binding_ledger(ledger_path)
    target = _find_binding(
        ledger,
        binding_id=request.binding_id,
        include_inactive=False,
    )
    if target is None:
        return ContinuousWorkerBindingResult(
            ok=False,
            action="reuse",
            ledger_path=ledger_path,
            bindings=ledger.bindings,
            status="not_found",
            message="active continuous worker binding not found for reuse",
            ledger_mutated=False,
        )
    if _binding_stale_reason_by_timestamp(target, request.timestamp):
        return ContinuousWorkerBindingResult(
            ok=False,
            action="reuse",
            ledger_path=ledger_path,
            binding=target,
            bindings=ledger.bindings,
            status="stale",
            message="continuous worker binding is expired and cannot be reused",
            ledger_mutated=False,
        )
    reused = replace(
        target,
        lifecycle_status="active",
        updated_at=request.timestamp or target.updated_at,
        last_used_at=request.timestamp or target.last_used_at,
        audit_refs=_merge_unique(target.audit_refs, request.audit_refs),
        metadata=_merge_metadata(
            target.metadata,
            {
                "last_reuse_task_id": request.task_id,
                "last_reuse_agent_id": request.agent_id,
                "last_reuse_lane_id": request.lane_id,
            },
            request.metadata,
        ),
    )
    updated = ContinuousWorkerBindingLedger(
        bindings=tuple(
            reused if binding.binding_id == target.binding_id else binding
            for binding in ledger.bindings
        )
    )
    write_continuous_worker_binding_ledger(updated, ledger_path)
    event = _append_binding_event(
        request.event_log_path,
        event_kind="binding_reused",
        timestamp=request.timestamp,
        binding=reused,
        previous_status=target.lifecycle_status,
        next_status=reused.lifecycle_status,
        reason=request.reason,
        metadata={
            "task_id": request.task_id,
            "agent_id": request.agent_id,
            "lane_id": request.lane_id,
            **dict(request.metadata),
        },
    )
    return ContinuousWorkerBindingResult(
        ok=True,
        action="reuse",
        ledger_path=ledger_path,
        binding=reused,
        bindings=updated.bindings,
        status="reused",
        message="continuous worker binding reuse recorded",
        ledger_mutated=True,
        event_records=(event,),
    )


def fork_continuous_worker_binding(
    request: ContinuousWorkerBindingForkRequest,
) -> ContinuousWorkerBindingResult:
    """Derive a new binding from an active parent binding without running a provider."""

    if not request.source_binding_id:
        raise ValueError("continuous worker binding fork requires source_binding_id")
    _validate_scope_kind(request.scope_kind)
    if not request.scope_id:
        raise ValueError("continuous worker binding fork requires scope_id")
    ledger_path = Path(request.ledger_path)
    ledger = read_continuous_worker_binding_ledger(ledger_path)
    source = _find_binding(
        ledger,
        binding_id=request.source_binding_id,
        include_inactive=False,
    )
    if source is None:
        return ContinuousWorkerBindingResult(
            ok=False,
            action="fork",
            ledger_path=ledger_path,
            bindings=ledger.bindings,
            status="source_not_found",
            message="active source continuous worker binding not found",
            ledger_mutated=False,
        )
    if _binding_stale_reason_by_timestamp(source, request.timestamp):
        return ContinuousWorkerBindingResult(
            ok=False,
            action="fork",
            ledger_path=ledger_path,
            binding=source,
            bindings=ledger.bindings,
            status="source_stale",
            message="source continuous worker binding is expired and cannot be forked",
            ledger_mutated=False,
        )
    selector = request.active_session_selector
    if selector is None and source.active_session_selector is not None:
        selector = replace(source.active_session_selector, fork_session=True)
    if selector is not None:
        _validate_session_selector(selector, expected_provider=source.runtime_provider)
    _validate_compact_policy_default(
        request.compact_policy_default,
        binding_id=request.new_binding_id or _binding_id(request.scope_kind, request.scope_id),
        metadata=request.metadata,
    )
    _validate_no_raw_or_secret_fields(
        "worker binding",
        request.new_binding_id or _binding_id(request.scope_kind, request.scope_id),
        request.metadata,
    )
    lane_ids = (
        (request.scope_id,)
        if request.scope_kind == "lane" and not request.lane_ids
        else _unique_nonempty(request.lane_ids)
    )
    if request.scope_kind == "lane_group" and not lane_ids:
        raise ValueError("lane_group continuous worker binding fork requires lane_ids")
    binding_id = request.new_binding_id or _binding_id(request.scope_kind, request.scope_id)
    existing_active = _find_binding(
        ledger,
        binding_id=binding_id,
        include_inactive=False,
    )
    if existing_active is not None:
        return ContinuousWorkerBindingResult(
            ok=False,
            action="fork",
            ledger_path=ledger_path,
            binding=existing_active,
            bindings=ledger.bindings,
            status="conflict",
            message="active continuous worker binding already exists for fork target",
            ledger_mutated=False,
        )
    forked = ContinuousWorkerBinding(
        binding_id=binding_id,
        worker_id=request.worker_id or f"{source.worker_id}:fork",
        runtime_provider=source.runtime_provider,
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
        lane_ids=lane_ids,
        lifecycle_status="active",
        active_session_selector=selector,
        generation=request.generation or source.generation + 1,
        parent_binding_id=source.binding_id,
        owned_lane_ids=lane_ids,
        private_storage_ref=request.private_storage_ref,
        private_storage_policy_ref=request.private_storage_policy_ref,
        compact_policy_ref=request.compact_policy_ref or source.compact_policy_ref,
        compact_policy_default=request.compact_policy_default,
        last_compact_at=source.last_compact_at,
        compact_needed=request.compact_needed,
        created_at=request.timestamp,
        updated_at=request.timestamp,
        expires_at=request.expires_at,
        last_used_at=request.timestamp,
        compact_context_ref=request.compact_context_ref or source.compact_context_ref,
        mailbox_cursor_ref=request.mailbox_cursor_ref or source.mailbox_cursor_ref,
        worker_report_refs=_merge_unique(
            source.worker_report_refs,
            request.worker_report_refs,
        ),
        audit_refs=_merge_unique(source.audit_refs, request.audit_refs),
        reason=request.reason,
        metadata=_merge_metadata(
            source.metadata,
            {
                "forked_from_binding_id": source.binding_id,
                "forked_at": request.timestamp,
            },
            request.metadata,
        ),
    )
    updated = ContinuousWorkerBindingLedger(bindings=(*ledger.bindings, forked))
    write_continuous_worker_binding_ledger(updated, ledger_path)
    event = _append_binding_event(
        request.event_log_path,
        event_kind="binding_forked",
        timestamp=request.timestamp,
        binding=forked,
        previous_status=source.lifecycle_status,
        next_status=forked.lifecycle_status,
        reason=request.reason,
        metadata={"source_binding_id": source.binding_id, **dict(request.metadata)},
    )
    return ContinuousWorkerBindingResult(
        ok=True,
        action="fork",
        ledger_path=ledger_path,
        binding=forked,
        bindings=updated.bindings,
        status="forked",
        message="continuous worker binding fork recorded",
        ledger_mutated=True,
        event_records=(event,),
    )


def compact_continuous_worker_binding(
    request: ContinuousWorkerBindingCompactRequest,
) -> ContinuousWorkerBindingResult:
    """Attach compact context/mailbox/report refs to one active binding."""

    if not request.compact_context_ref:
        raise ValueError("continuous worker binding compact requires compact_context_ref")
    _validate_no_raw_or_secret_fields(
        "worker binding",
        request.binding_id or f"{request.scope_kind}:{request.scope_id}",
        request.metadata,
    )
    ledger_path = Path(request.ledger_path)
    ledger = read_continuous_worker_binding_ledger(ledger_path)
    target = _find_binding(
        ledger,
        binding_id=request.binding_id,
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
        include_inactive=False,
    )
    if target is None:
        return ContinuousWorkerBindingResult(
            ok=False,
            action="compact",
            ledger_path=ledger_path,
            bindings=ledger.bindings,
            status="not_found",
            message="active continuous worker binding not found for compact",
            ledger_mutated=False,
        )
    compacted = replace(
        target,
        updated_at=request.timestamp or target.updated_at,
        compact_context_ref=request.compact_context_ref,
        last_compact_at=request.timestamp or target.last_compact_at,
        compact_needed=False,
        mailbox_cursor_ref=request.mailbox_cursor_ref or target.mailbox_cursor_ref,
        worker_report_refs=_merge_unique(
            target.worker_report_refs,
            request.worker_report_refs,
        ),
        audit_refs=_merge_unique(target.audit_refs, request.audit_refs),
        metadata=_merge_metadata(
            target.metadata,
            {"last_compacted_at": request.timestamp},
            request.metadata,
        ),
    )
    updated = ContinuousWorkerBindingLedger(
        bindings=tuple(
            compacted if binding.binding_id == target.binding_id else binding
            for binding in ledger.bindings
        )
    )
    write_continuous_worker_binding_ledger(updated, ledger_path)
    event = _append_binding_event(
        request.event_log_path,
        event_kind="binding_compacted",
        timestamp=request.timestamp,
        binding=compacted,
        previous_status=target.lifecycle_status,
        next_status=compacted.lifecycle_status,
        reason=request.reason,
        metadata={
            "compact_context_ref": request.compact_context_ref,
            "mailbox_cursor_ref": request.mailbox_cursor_ref,
            "worker_report_refs": list(request.worker_report_refs),
            **dict(request.metadata),
        },
    )
    return ContinuousWorkerBindingResult(
        ok=True,
        action="compact",
        ledger_path=ledger_path,
        binding=compacted,
        bindings=updated.bindings,
        status="compacted",
        message="continuous worker binding compact context recorded",
        ledger_mutated=True,
        event_records=(event,),
    )


def resolve_continuous_worker_binding(
    request: ContinuousWorkerBindingResolveRequest,
) -> ContinuousWorkerBindingResult:
    """Resolve one active binding by task, agent, lane, then lane-group match."""

    _validate_runtime_provider(request.runtime_provider)
    ledger_path = Path(request.ledger_path)
    ledger = read_continuous_worker_binding_ledger(ledger_path)
    active = tuple(
        binding
        for binding in ledger.bindings
        if _binding_active(binding)
        and binding.runtime_provider == request.runtime_provider
        and not _binding_stale_reason_by_timestamp(binding, request.timestamp)
    )
    candidates = (
        ("task", request.task_id),
        ("agent", request.agent_id),
        ("lane", request.lane_id),
    )
    for scope_kind, scope_id in candidates:
        if not scope_id:
            continue
        for binding in active:
            if binding.scope_kind == scope_kind and binding.scope_id == scope_id:
                return _resolved_result(binding, ledger_path)
    if request.lane_id:
        for binding in active:
            if binding.scope_kind == "lane_group" and request.lane_id in binding.lane_ids:
                return _resolved_result(binding, ledger_path)
    return ContinuousWorkerBindingResult(
        ok=False,
        action="resolve",
        ledger_path=ledger_path,
        bindings=active,
        status="not_found",
        message="no active continuous worker binding matched task, agent, lane, or lane group",
        ledger_mutated=False,
        selector_source="none",
    )


def claim_lane_ownership(
    request: LaneOwnershipClaimRequest,
) -> LaneOwnershipResult:
    """Claim one lane or lane group for a continuous worker binding."""

    _validate_lane_ownership_scope_kind(request.scope_kind)
    if not request.scope_id:
        raise ValueError("lane ownership claim requires scope_id")
    if not request.binding_id:
        raise ValueError("lane ownership claim requires binding_id")
    if not request.worker_id:
        raise ValueError("lane ownership claim requires worker_id")
    lane_ids = _normalize_lane_ownership_lane_ids(
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
        lane_ids=request.lane_ids,
    )
    ownership_id = request.ownership_id or _lane_ownership_id(
        request.scope_kind,
        request.scope_id,
    )
    _validate_no_raw_or_secret_fields(
        "lane ownership",
        ownership_id,
        {
            "requested_by": request.requested_by,
            "reason": request.reason,
            "audit_refs": list(request.audit_refs),
            "metadata": dict(request.metadata),
        },
    )
    ledger_path = Path(request.ledger_path)
    ledger = read_lane_ownership_ledger(ledger_path)
    existing = _find_lane_ownership(ledger, ownership_id=ownership_id)
    if existing is not None and _lane_ownership_selectable(existing):
        return LaneOwnershipResult(
            ok=False,
            action="claim",
            ledger_path=ledger_path,
            ownership=existing,
            ownerships=ledger.ownerships,
            status="conflict",
            message=_lane_ownership_error_message(
                "lane ownership conflict: lane already has active owner",
                ownership=existing,
                action="claimLane",
                allowed=("transferOwnership", "releaseOwnership", "suspendOwnership"),
            ),
            ledger_mutated=False,
            selectable=_lane_ownership_selectable(existing),
        )
    conflict = _selectable_lane_ownership_conflict(
        ledger.ownerships,
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
        lane_ids=lane_ids,
        exclude_ownership_id=ownership_id,
    )
    if conflict is not None:
        return LaneOwnershipResult(
            ok=False,
            action="claim",
            ledger_path=ledger_path,
            ownership=conflict,
            ownerships=ledger.ownerships,
            status="conflict",
            message=_lane_ownership_error_message(
                "lane ownership conflict: lane already has active owner",
                ownership=conflict,
                action="claimLane",
                allowed=("transferOwnership", "releaseOwnership", "suspendOwnership"),
            ),
            ledger_mutated=False,
            selectable=False,
        )
    ownership = LaneOwnership(
        ownership_id=ownership_id,
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
        lane_ids=lane_ids,
        binding_id=request.binding_id,
        worker_id=request.worker_id,
        status="claimed",
        created_at=request.timestamp,
        updated_at=request.timestamp,
        reason=request.reason,
        audit_refs=_unique_nonempty(request.audit_refs),
    )
    retained = tuple(
        item for item in ledger.ownerships if item.ownership_id != ownership_id
    )
    updated = LaneOwnershipLedger(ownerships=(*retained, ownership))
    write_lane_ownership_ledger(updated, ledger_path)
    event = _append_lane_ownership_event(
        request.event_log_path,
        event_kind="lane_ownership_claimed",
        timestamp=request.timestamp,
        ownership=ownership,
        previous_status="" if existing is None else existing.status,
        next_status="claimed",
        reason=request.reason,
        metadata={
            "requested_by": request.requested_by,
            **dict(request.metadata),
        },
    )
    return LaneOwnershipResult(
        ok=True,
        action="claim",
        ledger_path=ledger_path,
        ownership=ownership,
        ownerships=updated.ownerships,
        status="claimed",
        message="lane ownership claimed",
        ledger_mutated=True,
        selectable=True,
        event_records=(event,),
    )


def activate_lane_ownership(
    request: LaneOwnershipActivateRequest,
) -> LaneOwnershipResult:
    """Activate a claimed lane ownership after first successful delivery."""

    if not request.delivery_id:
        raise ValueError("lane ownership activation requires delivery_id")
    if not request.task_id:
        raise ValueError("lane ownership activation requires task_id")
    return _transition_lane_ownership(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="activate",
        requested_action="activateOwnership",
        ownership_id=request.ownership_id,
        binding_id=request.binding_id,
        allowed_statuses={"claimed"},
        next_status="active",
        event_kind="lane_ownership_activated",
        timestamp=request.activated_at,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata={
            "delivery_id": request.delivery_id,
            "task_id": request.task_id,
            **dict(request.metadata),
        },
        updates={
            "activated_at": request.activated_at,
            "updated_at": request.activated_at,
        },
    )


def suspend_lane_ownership(
    request: LaneOwnershipSuspendRequest,
) -> LaneOwnershipResult:
    """Suspend active lane ownership without releasing the owner."""

    return _transition_lane_ownership(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="suspend",
        requested_action="suspendOwnership",
        ownership_id=request.ownership_id,
        binding_id=request.binding_id,
        allowed_statuses={"active"},
        next_status="suspended",
        event_kind="lane_ownership_suspended",
        timestamp=request.timestamp,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata=request.metadata,
        updates={"updated_at": request.timestamp},
    )


def resume_lane_ownership(
    request: LaneOwnershipResumeRequest,
) -> LaneOwnershipResult:
    """Resume suspended lane ownership."""

    return _transition_lane_ownership(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="resume",
        requested_action="resumeOwnership",
        ownership_id=request.ownership_id,
        binding_id=request.binding_id,
        allowed_statuses={"suspended"},
        next_status="active",
        event_kind="lane_ownership_resumed",
        timestamp=request.timestamp,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata=request.metadata,
        updates={"updated_at": request.timestamp},
    )


def transfer_lane_ownership(
    request: LaneOwnershipTransferRequest,
) -> LaneOwnershipResult:
    """Transfer lane ownership away from the current binding."""

    if not request.replacement_binding_id:
        raise ValueError("lane ownership transfer requires replacement_binding_id")
    return _transition_lane_ownership(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="transfer",
        requested_action="transferOwnership",
        ownership_id=request.ownership_id,
        binding_id=request.binding_id,
        allowed_statuses={"claimed", "active", "suspended"},
        next_status="transferred",
        event_kind="lane_ownership_transferred",
        timestamp=request.timestamp,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata={
            "replacement_binding_id": request.replacement_binding_id,
            **dict(request.metadata),
        },
        updates={
            "replacement_binding_id": request.replacement_binding_id,
            "updated_at": request.timestamp,
        },
    )


def release_lane_ownership(
    request: LaneOwnershipReleaseRequest,
) -> LaneOwnershipResult:
    """Release lane ownership."""

    return _transition_lane_ownership(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="release",
        requested_action="releaseOwnership",
        ownership_id=request.ownership_id,
        binding_id=request.binding_id,
        allowed_statuses={"claimed", "active", "suspended"},
        next_status="released",
        event_kind="lane_ownership_released",
        timestamp=request.timestamp,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata=request.metadata,
        updates={"updated_at": request.timestamp},
    )


def inspect_lane_ownerships(
    request: LaneOwnershipInspectRequest,
) -> LaneOwnershipResult:
    """Inspect lane ownership records without mutation."""

    ledger_path = Path(request.ledger_path)
    ledger = read_lane_ownership_ledger(ledger_path)
    ownerships = ledger.ownerships
    if request.ownership_id:
        ownerships = tuple(
            item for item in ownerships if item.ownership_id == request.ownership_id
        )
    if request.scope_kind:
        ownerships = tuple(
            item for item in ownerships if item.scope_kind == request.scope_kind
        )
    if request.scope_id:
        ownerships = tuple(item for item in ownerships if item.scope_id == request.scope_id)
    if request.lane_id:
        ownerships = tuple(
            item
            for item in ownerships
            if request.lane_id == item.scope_id or request.lane_id in item.lane_ids
        )
    if request.binding_id:
        ownerships = tuple(item for item in ownerships if item.binding_id == request.binding_id)
    if request.worker_id:
        ownerships = tuple(item for item in ownerships if item.worker_id == request.worker_id)
    if not request.include_inactive:
        ownerships = tuple(
            item for item in ownerships if _lane_ownership_selectable(item)
        )
    return LaneOwnershipResult(
        ok=True,
        action="inspect",
        ledger_path=ledger_path,
        ownerships=ownerships,
        status="inspected",
        message=f"{len(ownerships)} lane ownership record(s) matched",
        ledger_mutated=False,
        selectable=any(_lane_ownership_selectable(item) for item in ownerships),
    )


def lane_ownership_allows_delivery(
    ledger_path: str | Path,
    *,
    binding_id: str,
    lane_id: str,
) -> bool:
    """Return whether lane ownership allows a binding to deliver this lane."""

    if not binding_id or not lane_id:
        return True
    ledger = read_lane_ownership_ledger(ledger_path)
    relevant = tuple(
        item
        for item in ledger.ownerships
        if lane_id == item.scope_id or lane_id in item.lane_ids
    )
    if not relevant:
        return True
    return any(
        item.binding_id == binding_id and _lane_ownership_selectable(item)
        for item in relevant
    )


def reserve_delivery_lease(
    request: DeliveryLeaseReserveRequest,
) -> DeliveryLeaseResult:
    """Reserve one binding for a delivery if no active lease exists."""

    if not request.binding_id:
        raise ValueError("delivery lease reserve requires binding_id")
    if not request.task_id:
        raise ValueError("delivery lease reserve requires task_id")
    if not request.delivery_id:
        raise ValueError("delivery lease reserve requires delivery_id")
    lease_id = request.lease_id or _delivery_lease_id(
        request.binding_id,
        request.delivery_id,
    )
    _validate_no_raw_or_secret_fields(
        "delivery lease",
        lease_id,
        {
            "audit_refs": list(request.audit_refs),
            "metadata": dict(request.metadata),
        },
    )
    ledger_path = Path(request.ledger_path)
    ledger = read_delivery_lease_ledger(ledger_path)
    active = _active_delivery_lease_for_binding(ledger, request.binding_id)
    if active is not None:
        return DeliveryLeaseResult(
            ok=False,
            action="reserve",
            ledger_path=ledger_path,
            lease=active,
            leases=ledger.leases,
            status="active_conflict",
            message=(
                "delivery lease conflict: binding already has active lease "
                f"binding={active.binding_id} lease={active.lease_id} "
                f"task={active.task_id}"
            ),
            ledger_mutated=False,
        )
    existing = _find_delivery_lease(ledger, lease_id=lease_id)
    if existing is not None and _delivery_lease_active(existing):
        return DeliveryLeaseResult(
            ok=False,
            action="reserve",
            ledger_path=ledger_path,
            lease=existing,
            leases=ledger.leases,
            status="active_conflict",
            message="delivery lease conflict: lease_id is already active",
            ledger_mutated=False,
        )
    lease = DeliveryLease(
        lease_id=lease_id,
        binding_id=request.binding_id,
        task_id=request.task_id,
        delivery_id=request.delivery_id,
        status="reserved",
        reserved_at=request.reserved_at,
        expires_at=request.expires_at,
        audit_refs=_unique_nonempty(request.audit_refs),
    )
    retained = tuple(item for item in ledger.leases if item.lease_id != lease_id)
    updated = DeliveryLeaseLedger(leases=(*retained, lease))
    write_delivery_lease_ledger(updated, ledger_path)
    event = _append_delivery_lease_event(
        request.event_log_path,
        event_kind="delivery_lease_reserved",
        timestamp=request.reserved_at,
        lease=lease,
        previous_status="" if existing is None else existing.status,
        next_status="reserved",
        reason=request.reason,
        metadata=request.metadata,
    )
    return DeliveryLeaseResult(
        ok=True,
        action="reserve",
        ledger_path=ledger_path,
        lease=lease,
        leases=updated.leases,
        status="reserved",
        message="continuous worker delivery lease reserved",
        ledger_mutated=True,
        event_records=(event,),
    )


def begin_delivery_lease_run(
    request: DeliveryLeaseBeginRequest,
) -> DeliveryLeaseResult:
    """Mark a reserved delivery lease running."""

    return _transition_delivery_lease(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="begin",
        lease_id=request.lease_id,
        binding_id=request.binding_id,
        allowed_statuses={"reserved"},
        next_status="running",
        event_kind="delivery_lease_started",
        timestamp=request.started_at,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata=request.metadata,
        updates={"started_at": request.started_at},
    )


def complete_delivery_lease(
    request: DeliveryLeaseCompleteRequest,
) -> DeliveryLeaseResult:
    """Mark a reserved or running delivery lease completed."""

    _validate_no_raw_or_secret_fields(
        "delivery lease",
        request.lease_id or request.binding_id,
        {
            "result_ref": request.result_ref,
            "audit_refs": list(request.audit_refs),
            "metadata": dict(request.metadata),
        },
    )
    return _transition_delivery_lease(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="complete",
        lease_id=request.lease_id,
        binding_id=request.binding_id,
        allowed_statuses={"reserved", "running"},
        next_status="completed",
        event_kind="delivery_lease_completed",
        timestamp=request.completed_at,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata=request.metadata,
        updates={
            "completed_at": request.completed_at,
            "result_ref": request.result_ref,
        },
    )


def fail_delivery_lease_retryable(
    request: DeliveryLeaseFailRequest,
) -> DeliveryLeaseResult:
    """Mark a reserved or running delivery lease failed with retryable cause."""

    return _fail_delivery_lease(request, next_status="failed_retryable")


def fail_delivery_lease_terminal(
    request: DeliveryLeaseFailRequest,
) -> DeliveryLeaseResult:
    """Mark a reserved or running delivery lease failed terminally."""

    return _fail_delivery_lease(request, next_status="failed_terminal")


def expire_delivery_lease(
    request: DeliveryLeaseExpireRequest,
) -> DeliveryLeaseResult:
    """Mark a reserved or running delivery lease expired."""

    return _transition_delivery_lease(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="expire",
        lease_id=request.lease_id,
        binding_id=request.binding_id,
        allowed_statuses={"reserved", "running"},
        next_status="expired",
        event_kind="delivery_lease_expired",
        timestamp=request.observed_at,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata=request.metadata,
    )


def release_delivery_lease(
    request: DeliveryLeaseReleaseRequest,
) -> DeliveryLeaseResult:
    """Release a non-active delivery lease while preserving audit history."""

    return _transition_delivery_lease(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="release",
        lease_id=request.lease_id,
        binding_id=request.binding_id,
        allowed_statuses={
            "completed",
            "failed_retryable",
            "failed_terminal",
            "expired",
            "released",
        },
        next_status="released",
        event_kind="delivery_lease_released",
        timestamp=request.released_at,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata=request.metadata,
    )


def inspect_delivery_leases(
    request: DeliveryLeaseInspectRequest,
) -> DeliveryLeaseResult:
    """Inspect delivery leases without mutation."""

    ledger_path = Path(request.ledger_path)
    ledger = read_delivery_lease_ledger(ledger_path)
    leases = ledger.leases
    if request.binding_id:
        leases = tuple(lease for lease in leases if lease.binding_id == request.binding_id)
    if request.task_id:
        leases = tuple(lease for lease in leases if lease.task_id == request.task_id)
    if request.delivery_id:
        leases = tuple(lease for lease in leases if lease.delivery_id == request.delivery_id)
    if request.lease_id:
        leases = tuple(lease for lease in leases if lease.lease_id == request.lease_id)
    if not request.include_inactive:
        leases = tuple(lease for lease in leases if _delivery_lease_active(lease))
    return DeliveryLeaseResult(
        ok=True,
        action="inspect",
        ledger_path=ledger_path,
        leases=leases,
        status="inspected",
        message=f"{len(leases)} delivery lease(s) matched",
        ledger_mutated=False,
    )


def binding_has_active_delivery_lease(
    ledger_path: str | Path,
    binding_id: str,
) -> bool:
    """Return whether a binding currently has an active delivery lease."""

    if not binding_id:
        return False
    ledger = read_delivery_lease_ledger(ledger_path)
    return _active_delivery_lease_for_binding(ledger, binding_id) is not None


def read_continuous_worker_binding_ledger(
    path: str | Path,
) -> ContinuousWorkerBindingLedger:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return ContinuousWorkerBindingLedger()
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != CONTINUOUS_WORKER_BINDING_LEDGER_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported continuous worker binding ledger schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    return ContinuousWorkerBindingLedger(
        bindings=tuple(
            _binding_from_json_dict(item)
            for item in payload.get("bindings", [])
        )
    )


def write_continuous_worker_binding_ledger(
    ledger: ContinuousWorkerBindingLedger,
    path: str | Path,
) -> None:
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(ledger.to_json_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def read_lane_ownership_ledger(
    path: str | Path,
) -> LaneOwnershipLedger:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return LaneOwnershipLedger()
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported continuous worker lane ownership ledger schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    return LaneOwnershipLedger(
        ownerships=tuple(
            lane_ownership_from_json_dict(item)
            for item in payload.get("ownerships", [])
        )
    )


def write_lane_ownership_ledger(
    ledger: LaneOwnershipLedger,
    path: str | Path,
) -> None:
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(ledger.to_json_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def read_delivery_lease_ledger(
    path: str | Path,
) -> DeliveryLeaseLedger:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return DeliveryLeaseLedger()
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported continuous worker delivery lease ledger schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    return DeliveryLeaseLedger(
        leases=tuple(
            delivery_lease_from_json_dict(item)
            for item in payload.get("leases", [])
        )
    )


def write_delivery_lease_ledger(
    ledger: DeliveryLeaseLedger,
    path: str | Path,
) -> None:
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(ledger.to_json_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def lane_ownership_from_json_dict(payload: Mapping[str, object]) -> LaneOwnership:
    """Parse one LaneOwnership schema record with contract-level validation."""

    _reject_disallowed_keys(
        "lane ownership",
        payload,
        disallowed={"has_private_storage"},
        record_id=str(payload.get("ownership_id", "")),
    )
    _validate_no_raw_or_secret_fields(
        "lane ownership",
        str(payload.get("ownership_id", "")),
        payload,
    )
    scope_kind = str(payload.get("scope_kind", ""))
    status = str(payload.get("status", "claimed"))
    _validate_lane_ownership_scope_kind(
        scope_kind,
        ownership_id=str(payload.get("ownership_id", "")),
    )
    _validate_lane_ownership_status(
        status,
        ownership_id=str(payload.get("ownership_id", "")),
    )
    return LaneOwnership(
        ownership_id=str(payload.get("ownership_id", "")),
        scope_kind=scope_kind,  # type: ignore[arg-type]
        scope_id=str(payload.get("scope_id", "")),
        lane_ids=_tuple_of_strings(payload.get("lane_ids", ())),
        binding_id=str(payload.get("binding_id", "")),
        worker_id=str(payload.get("worker_id", "")),
        status=status,  # type: ignore[arg-type]
        replacement_binding_id=str(payload.get("replacement_binding_id", "")),
        created_at=str(payload.get("created_at", "")),
        activated_at=str(payload.get("activated_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        reason=str(payload.get("reason", "")),
        audit_refs=_tuple_of_strings(payload.get("audit_refs", ())),
    )


def delivery_lease_from_json_dict(payload: Mapping[str, object]) -> DeliveryLease:
    """Parse one DeliveryLease schema record with contract-level validation."""

    _reject_disallowed_keys(
        "delivery lease",
        payload,
        disallowed={"has_private_storage"},
        record_id=str(payload.get("lease_id", "")),
    )
    _validate_no_raw_or_secret_fields(
        "delivery lease",
        str(payload.get("lease_id", "")),
        payload,
    )
    status = str(payload.get("status", "reserved"))
    _validate_delivery_lease_status(
        status,
        lease_id=str(payload.get("lease_id", "")),
        binding_id=str(payload.get("binding_id", "")),
        task_id=str(payload.get("task_id", "")),
    )
    return DeliveryLease(
        lease_id=str(payload.get("lease_id", "")),
        binding_id=str(payload.get("binding_id", "")),
        task_id=str(payload.get("task_id", "")),
        delivery_id=str(payload.get("delivery_id", "")),
        status=status,  # type: ignore[arg-type]
        reserved_at=str(payload.get("reserved_at", "")),
        started_at=str(payload.get("started_at", "")),
        expires_at=str(payload.get("expires_at", "")),
        completed_at=str(payload.get("completed_at", "")),
        failed_at=str(payload.get("failed_at", "")),
        failure_kind=str(payload.get("failure_kind", "")),
        result_ref=str(payload.get("result_ref", "")),
        audit_refs=_tuple_of_strings(payload.get("audit_refs", ())),
    )


def continuous_worker_binding_from_json_dict(
    payload: Mapping[str, object],
) -> ContinuousWorkerBinding:
    """Parse one ContinuousWorkerBinding record with public schema validation."""

    return _binding_from_json_dict(payload)


def active_delivery_lease_conflicts(
    leases: tuple[DeliveryLease, ...],
) -> tuple[tuple[DeliveryLease, DeliveryLease], ...]:
    """Return data-layer active lease conflicts by binding id.

    This helper is intentionally pure schema logic. It does not reserve,
    release, schedule, or recover leases.
    """

    active_by_binding: dict[str, DeliveryLease] = {}
    conflicts: list[tuple[DeliveryLease, DeliveryLease]] = []
    for lease in leases:
        if not _delivery_lease_active(lease):
            continue
        existing = active_by_binding.get(lease.binding_id)
        if existing is None:
            active_by_binding[lease.binding_id] = lease
            continue
        conflicts.append((existing, lease))
    return tuple(conflicts)


def validate_no_active_delivery_lease_conflicts(
    leases: tuple[DeliveryLease, ...],
) -> None:
    """Raise when more than one active lease exists for the same binding."""

    conflicts = active_delivery_lease_conflicts(leases)
    if not conflicts:
        return
    first, second = conflicts[0]
    raise ValueError(
        "delivery lease conflict: binding already has active lease "
        f"binding={first.binding_id} lease={first.lease_id} task={first.task_id} "
        f"conflicting_lease={second.lease_id} conflicting_task={second.task_id}"
    )


def selectable_lane_ownership_conflicts(
    ownerships: tuple[LaneOwnership, ...],
) -> tuple[tuple[LaneOwnership, LaneOwnership], ...]:
    """Return selectable lane ownership conflicts by lane intersection."""

    selectable = tuple(
        ownership for ownership in ownerships if _lane_ownership_selectable(ownership)
    )
    conflicts: list[tuple[LaneOwnership, LaneOwnership]] = []
    for index, first in enumerate(selectable):
        first_lanes = set(_lane_ownership_lane_ids(first))
        for second in selectable[index + 1:]:
            if first_lanes.intersection(_lane_ownership_lane_ids(second)):
                conflicts.append((first, second))
    return tuple(conflicts)


def validate_no_selectable_lane_ownership_conflicts(
    ownerships: tuple[LaneOwnership, ...],
) -> None:
    """Raise when more than one selectable owner exists for the same lane."""

    conflicts = selectable_lane_ownership_conflicts(ownerships)
    if not conflicts:
        return
    first, second = conflicts[0]
    raise ValueError(
        "lane ownership conflict: lane already has active owner "
        f"scope_kind={first.scope_kind} scope_id={first.scope_id} "
        f"lane_ids={'|'.join(_shared_lane_ids(first, second))} "
        f"binding={first.binding_id} ownership={first.ownership_id} "
        f"conflicting_binding={second.binding_id} "
        f"conflicting_ownership={second.ownership_id} "
        "allowed=transferOwnership|releaseOwnership|suspendOwnership"
    )


def continuous_worker_binding_event_record_from_json_dict(
    payload: Mapping[str, object],
) -> ContinuousWorkerBindingEventRecord:
    if str(payload.get("schema_version", "")) != CONTINUOUS_WORKER_BINDING_EVENT_LOG_SCHEMA_VERSION:
        raise ValueError(
            "unsupported continuous worker binding event log schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    event_kind = str(payload.get("event_kind", "binding_claimed"))
    if event_kind not in {
        "binding_claimed",
        "binding_reused",
        "binding_forked",
        "binding_compacted",
        "binding_released",
        "binding_marked_stale",
        "binding_archived",
    }:
        raise ValueError(f"invalid continuous worker binding event kind: {event_kind!r}")
    return ContinuousWorkerBindingEventRecord(
        event_id=str(payload.get("event_id", "")),
        event_kind=event_kind,  # type: ignore[arg-type]
        timestamp=str(payload.get("timestamp", "")),
        binding_id=str(payload.get("binding_id", "")),
        worker_id=str(payload.get("worker_id", "")),
        runtime_provider=str(payload.get("runtime_provider", "")),
        scope_kind=str(payload.get("scope_kind", "")),
        scope_id=str(payload.get("scope_id", "")),
        previous_status=str(payload.get("previous_status", "")),
        next_status=str(payload.get("next_status", "")),
        reason=str(payload.get("reason", "")),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def lane_ownership_event_record_from_json_dict(
    payload: Mapping[str, object],
) -> LaneOwnershipEventRecord:
    if str(payload.get("schema_version", "")) != CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_SCHEMA_VERSION:
        raise ValueError(
            "unsupported lane ownership event log schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    event_kind = str(payload.get("event_kind", "lane_ownership_claimed"))
    if event_kind not in {
        "lane_ownership_claimed",
        "lane_ownership_activated",
        "lane_ownership_suspended",
        "lane_ownership_resumed",
        "lane_ownership_transferred",
        "lane_ownership_released",
    }:
        raise ValueError(f"invalid lane ownership event kind: {event_kind!r}")
    _validate_no_raw_or_secret_fields(
        "lane ownership event",
        str(payload.get("event_id", "")),
        payload,
    )
    return LaneOwnershipEventRecord(
        event_id=str(payload.get("event_id", "")),
        event_kind=event_kind,  # type: ignore[arg-type]
        timestamp=str(payload.get("timestamp", "")),
        ownership_id=str(payload.get("ownership_id", "")),
        scope_kind=str(payload.get("scope_kind", "")),
        scope_id=str(payload.get("scope_id", "")),
        binding_id=str(payload.get("binding_id", "")),
        previous_status=str(payload.get("previous_status", "")),
        next_status=str(payload.get("next_status", "")),
        reason=str(payload.get("reason", "")),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def delivery_lease_event_record_from_json_dict(
    payload: Mapping[str, object],
) -> DeliveryLeaseEventRecord:
    if str(payload.get("schema_version", "")) != CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_SCHEMA_VERSION:
        raise ValueError(
            "unsupported delivery lease event log schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    event_kind = str(payload.get("event_kind", "delivery_lease_reserved"))
    if event_kind not in {
        "delivery_lease_reserved",
        "delivery_lease_started",
        "delivery_lease_completed",
        "delivery_lease_failed_retryable",
        "delivery_lease_failed_terminal",
        "delivery_lease_expired",
        "delivery_lease_released",
    }:
        raise ValueError(f"invalid delivery lease event kind: {event_kind!r}")
    _validate_no_raw_or_secret_fields(
        "delivery lease event",
        str(payload.get("event_id", "")),
        payload,
    )
    return DeliveryLeaseEventRecord(
        event_id=str(payload.get("event_id", "")),
        event_kind=event_kind,  # type: ignore[arg-type]
        timestamp=str(payload.get("timestamp", "")),
        lease_id=str(payload.get("lease_id", "")),
        binding_id=str(payload.get("binding_id", "")),
        task_id=str(payload.get("task_id", "")),
        delivery_id=str(payload.get("delivery_id", "")),
        previous_status=str(payload.get("previous_status", "")),
        next_status=str(payload.get("next_status", "")),
        reason=str(payload.get("reason", "")),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def _resolved_result(
    binding: ContinuousWorkerBinding,
    ledger_path: Path,
) -> ContinuousWorkerBindingResult:
    return ContinuousWorkerBindingResult(
        ok=True,
        action="resolve",
        ledger_path=ledger_path,
        binding=binding,
        bindings=(binding,),
        status="resolved",
        message="continuous worker binding resolved",
        ledger_mutated=False,
        selector_source="continuous_worker_binding",
    )


def _append_binding_event(
    event_log_path: str | Path,
    *,
    event_kind: ContinuousWorkerBindingEventKind,
    timestamp: str,
    binding: ContinuousWorkerBinding,
    previous_status: str,
    next_status: str,
    reason: str = "",
    metadata: Mapping[str, object] | None = None,
) -> ContinuousWorkerBindingEventRecord:
    event_log = JsonlContinuousWorkerBindingEventLog(event_log_path)
    event = _binding_event_record(
        event_index=len(event_log.read_all()) + 1,
        event_kind=event_kind,
        timestamp=timestamp,
        binding=binding,
        previous_status=previous_status,
        next_status=next_status,
        reason=reason,
        metadata=metadata,
    )
    return event_log.append(event)


def _append_lane_ownership_event(
    event_log_path: str | Path,
    *,
    event_kind: LaneOwnershipEventKind,
    timestamp: str,
    ownership: LaneOwnership,
    previous_status: str,
    next_status: str,
    reason: str = "",
    metadata: Mapping[str, object] | None = None,
) -> LaneOwnershipEventRecord:
    event_log = JsonlLaneOwnershipEventLog(event_log_path)
    event = _lane_ownership_event_record(
        event_index=len(event_log.read_all()) + 1,
        event_kind=event_kind,
        timestamp=timestamp,
        ownership=ownership,
        previous_status=previous_status,
        next_status=next_status,
        reason=reason,
        metadata=metadata,
    )
    return event_log.append(event)


def _lane_ownership_event_record(
    *,
    event_index: int,
    event_kind: LaneOwnershipEventKind,
    timestamp: str,
    ownership: LaneOwnership,
    previous_status: str,
    next_status: str,
    reason: str = "",
    metadata: Mapping[str, object] | None = None,
) -> LaneOwnershipEventRecord:
    return LaneOwnershipEventRecord(
        event_id=f"continuous-worker-lane-ownership:event-{event_index:04d}",
        event_kind=event_kind,
        timestamp=timestamp,
        ownership_id=ownership.ownership_id,
        scope_kind=ownership.scope_kind,
        scope_id=ownership.scope_id,
        binding_id=ownership.binding_id,
        previous_status=previous_status,
        next_status=next_status,
        reason=reason,
        metadata=dict(metadata or {}),
    )


def _transition_lane_ownership(
    *,
    ledger_path: str | Path,
    event_log_path: str | Path,
    action: str,
    requested_action: str,
    ownership_id: str,
    binding_id: str,
    allowed_statuses: set[str],
    next_status: LaneOwnershipStatus,
    event_kind: LaneOwnershipEventKind,
    timestamp: str,
    reason: str,
    audit_refs: tuple[str, ...],
    metadata: Mapping[str, object],
    updates: Mapping[str, object] | None = None,
) -> LaneOwnershipResult:
    _validate_no_raw_or_secret_fields(
        "lane ownership",
        ownership_id or binding_id,
        {
            "reason": reason,
            "audit_refs": list(audit_refs),
            "metadata": dict(metadata),
            "updates": dict(updates or {}),
        },
    )
    ledger_path = Path(ledger_path)
    ledger = read_lane_ownership_ledger(ledger_path)
    ownership = _find_lane_ownership(
        ledger,
        ownership_id=ownership_id,
        binding_id=binding_id,
    )
    if ownership is None:
        return LaneOwnershipResult(
            ok=False,
            action=action,
            ledger_path=ledger_path,
            ownerships=ledger.ownerships,
            status="not_found",
            message=(
                "lane ownership transition rejected: ownership not found "
                f"ownership={ownership_id} binding={binding_id} action={requested_action}"
            ),
            ledger_mutated=False,
            selectable=False,
        )
    if ownership.status not in allowed_statuses:
        return LaneOwnershipResult(
            ok=False,
            action=action,
            ledger_path=ledger_path,
            ownership=ownership,
            ownerships=ledger.ownerships,
            status="invalid_status",
            message=_lane_ownership_error_message(
                "lane ownership transition rejected: status is not allowed",
                ownership=ownership,
                action=requested_action,
                allowed=_allowed_lane_ownership_actions(ownership.status),
            ),
            ledger_mutated=False,
            selectable=_lane_ownership_selectable(ownership),
        )
    updated_kwargs = dict(updates or {})
    updated_kwargs["status"] = next_status
    updated_kwargs["reason"] = reason or ownership.reason
    if audit_refs:
        updated_kwargs["audit_refs"] = _merge_unique(ownership.audit_refs, audit_refs)
    transitioned = replace(ownership, **updated_kwargs)
    if _lane_ownership_selectable(transitioned):
        conflict = _selectable_lane_ownership_conflict(
            ledger.ownerships,
            scope_kind=transitioned.scope_kind,
            scope_id=transitioned.scope_id,
            lane_ids=transitioned.lane_ids,
            exclude_ownership_id=transitioned.ownership_id,
        )
        if conflict is not None:
            return LaneOwnershipResult(
                ok=False,
                action=action,
                ledger_path=ledger_path,
                ownership=conflict,
                ownerships=ledger.ownerships,
                status="conflict",
                message=_lane_ownership_error_message(
                    "lane ownership conflict: lane already has active owner",
                    ownership=conflict,
                    action=requested_action,
                    allowed=("transferOwnership", "releaseOwnership", "suspendOwnership"),
                ),
                ledger_mutated=False,
                selectable=False,
            )
    updated = LaneOwnershipLedger(
        ownerships=tuple(
            transitioned if item.ownership_id == ownership.ownership_id else item
            for item in ledger.ownerships
        )
    )
    write_lane_ownership_ledger(updated, ledger_path)
    event = _append_lane_ownership_event(
        event_log_path,
        event_kind=event_kind,
        timestamp=timestamp,
        ownership=transitioned,
        previous_status=ownership.status,
        next_status=next_status,
        reason=reason,
        metadata=metadata,
    )
    return LaneOwnershipResult(
        ok=True,
        action=action,
        ledger_path=ledger_path,
        ownership=transitioned,
        ownerships=updated.ownerships,
        status=next_status,
        message=f"lane ownership marked {next_status}",
        ledger_mutated=True,
        selectable=_lane_ownership_selectable(transitioned),
        event_records=(event,),
    )


def _append_delivery_lease_event(
    event_log_path: str | Path,
    *,
    event_kind: DeliveryLeaseEventKind,
    timestamp: str,
    lease: DeliveryLease,
    previous_status: str,
    next_status: str,
    reason: str = "",
    metadata: Mapping[str, object] | None = None,
) -> DeliveryLeaseEventRecord:
    event_log = JsonlDeliveryLeaseEventLog(event_log_path)
    event = _delivery_lease_event_record(
        event_index=len(event_log.read_all()) + 1,
        event_kind=event_kind,
        timestamp=timestamp,
        lease=lease,
        previous_status=previous_status,
        next_status=next_status,
        reason=reason,
        metadata=metadata,
    )
    return event_log.append(event)


def _delivery_lease_event_record(
    *,
    event_index: int,
    event_kind: DeliveryLeaseEventKind,
    timestamp: str,
    lease: DeliveryLease,
    previous_status: str,
    next_status: str,
    reason: str = "",
    metadata: Mapping[str, object] | None = None,
) -> DeliveryLeaseEventRecord:
    return DeliveryLeaseEventRecord(
        event_id=f"continuous-worker-delivery-lease:event-{event_index:04d}",
        event_kind=event_kind,
        timestamp=timestamp,
        lease_id=lease.lease_id,
        binding_id=lease.binding_id,
        task_id=lease.task_id,
        delivery_id=lease.delivery_id,
        previous_status=previous_status,
        next_status=next_status,
        reason=reason,
        metadata=dict(metadata or {}),
    )


def _transition_delivery_lease(
    *,
    ledger_path: str | Path,
    event_log_path: str | Path,
    action: str,
    lease_id: str,
    binding_id: str,
    allowed_statuses: set[str],
    next_status: DeliveryLeaseStatus,
    event_kind: DeliveryLeaseEventKind,
    timestamp: str,
    reason: str,
    audit_refs: tuple[str, ...],
    metadata: Mapping[str, object],
    updates: Mapping[str, object] | None = None,
) -> DeliveryLeaseResult:
    _validate_no_raw_or_secret_fields(
        "delivery lease",
        lease_id or binding_id,
        {
            "audit_refs": list(audit_refs),
            "metadata": dict(metadata),
            "updates": dict(updates or {}),
        },
    )
    ledger_path = Path(ledger_path)
    ledger = read_delivery_lease_ledger(ledger_path)
    lease = _find_delivery_lease(
        ledger,
        lease_id=lease_id,
        binding_id=binding_id,
    )
    if lease is None:
        return DeliveryLeaseResult(
            ok=False,
            action=action,
            ledger_path=ledger_path,
            leases=ledger.leases,
            status="not_found",
            message=(
                "delivery lease transition rejected: lease not found "
                f"lease={lease_id} binding={binding_id} action={action}"
            ),
            ledger_mutated=False,
        )
    if lease.status not in allowed_statuses:
        return DeliveryLeaseResult(
            ok=False,
            action=action,
            ledger_path=ledger_path,
            lease=lease,
            leases=ledger.leases,
            status="invalid_status",
            message=(
                "delivery lease transition rejected: status is not allowed "
                f"lease={lease.lease_id} binding={lease.binding_id} "
                f"current={lease.status} action={action} "
                f"allowed={'|'.join(sorted(allowed_statuses))}"
            ),
            ledger_mutated=False,
        )
    updated_kwargs = dict(updates or {})
    updated_kwargs["status"] = next_status
    if audit_refs:
        updated_kwargs["audit_refs"] = _merge_unique(lease.audit_refs, audit_refs)
    transitioned = replace(lease, **updated_kwargs)
    updated = DeliveryLeaseLedger(
        leases=tuple(
            transitioned if item.lease_id == lease.lease_id else item
            for item in ledger.leases
        )
    )
    write_delivery_lease_ledger(updated, ledger_path)
    event = _append_delivery_lease_event(
        event_log_path,
        event_kind=event_kind,
        timestamp=timestamp,
        lease=transitioned,
        previous_status=lease.status,
        next_status=next_status,
        reason=reason,
        metadata=metadata,
    )
    return DeliveryLeaseResult(
        ok=True,
        action=action,
        ledger_path=ledger_path,
        lease=transitioned,
        leases=updated.leases,
        status=next_status,
        message=f"continuous worker delivery lease marked {next_status}",
        ledger_mutated=True,
        event_records=(event,),
    )


def _fail_delivery_lease(
    request: DeliveryLeaseFailRequest,
    *,
    next_status: DeliveryLeaseStatus,
) -> DeliveryLeaseResult:
    _validate_no_raw_or_secret_fields(
        "delivery lease",
        request.lease_id or request.binding_id,
        {
            "failure_kind": request.failure_kind,
            "result_ref": request.result_ref,
            "audit_refs": list(request.audit_refs),
            "metadata": dict(request.metadata),
        },
    )
    return _transition_delivery_lease(
        ledger_path=request.ledger_path,
        event_log_path=request.event_log_path,
        action="fail_retryable" if next_status == "failed_retryable" else "fail_terminal",
        lease_id=request.lease_id,
        binding_id=request.binding_id,
        allowed_statuses={"reserved", "running"},
        next_status=next_status,
        event_kind=(
            "delivery_lease_failed_retryable"
            if next_status == "failed_retryable"
            else "delivery_lease_failed_terminal"
        ),
        timestamp=request.failed_at,
        reason=request.reason,
        audit_refs=request.audit_refs,
        metadata=request.metadata,
        updates={
            "failed_at": request.failed_at,
            "failure_kind": request.failure_kind,
            "result_ref": request.result_ref,
        },
    )


def _binding_event_record(
    *,
    event_index: int,
    event_kind: ContinuousWorkerBindingEventKind,
    timestamp: str,
    binding: ContinuousWorkerBinding,
    previous_status: str,
    next_status: str,
    reason: str = "",
    metadata: Mapping[str, object] | None = None,
) -> ContinuousWorkerBindingEventRecord:
    return ContinuousWorkerBindingEventRecord(
        event_id=f"continuous-worker-binding:event-{event_index:04d}",
        event_kind=event_kind,
        timestamp=timestamp,
        binding_id=binding.binding_id,
        worker_id=binding.worker_id,
        runtime_provider=binding.runtime_provider,
        scope_kind=binding.scope_kind,
        scope_id=binding.scope_id,
        previous_status=previous_status,
        next_status=next_status,
        reason=reason,
        metadata=dict(metadata or {}),
    )


def _release_event_kind(
    lifecycle_status: ContinuousWorkerLifecycleStatus,
) -> ContinuousWorkerBindingEventKind:
    if lifecycle_status == "stale":
        return "binding_marked_stale"
    if lifecycle_status == "archived":
        return "binding_archived"
    return "binding_released"


def _find_binding(
    ledger: ContinuousWorkerBindingLedger,
    *,
    binding_id: str = "",
    scope_kind: str = "",
    scope_id: str = "",
    include_inactive: bool,
) -> ContinuousWorkerBinding | None:
    for binding in ledger.bindings:
        if not include_inactive and not _binding_active(binding):
            continue
        if binding_id and binding.binding_id == binding_id:
            return binding
        if scope_kind and scope_id and binding.scope_kind == scope_kind and binding.scope_id == scope_id:
            return binding
    return None


def _find_lane_ownership(
    ledger: LaneOwnershipLedger,
    *,
    ownership_id: str = "",
    binding_id: str = "",
) -> LaneOwnership | None:
    if ownership_id:
        for ownership in ledger.ownerships:
            if ownership.ownership_id == ownership_id:
                return ownership
        return None
    if binding_id:
        for ownership in ledger.ownerships:
            if ownership.binding_id == binding_id:
                return ownership
        return None
    return None


def _selectable_lane_ownership_conflict(
    ownerships: tuple[LaneOwnership, ...],
    *,
    scope_kind: str,
    scope_id: str,
    lane_ids: tuple[str, ...],
    exclude_ownership_id: str = "",
) -> LaneOwnership | None:
    incoming = set(
        _normalize_lane_ownership_lane_ids(
            scope_kind=scope_kind,
            scope_id=scope_id,
            lane_ids=lane_ids,
        )
    )
    for ownership in ownerships:
        if ownership.ownership_id == exclude_ownership_id:
            continue
        if not _lane_ownership_selectable(ownership):
            continue
        if incoming.intersection(_lane_ownership_lane_ids(ownership)):
            return ownership
    return None


def _lane_ownership_selectable(ownership: LaneOwnership) -> bool:
    return ownership.status in {"claimed", "active"}


def _lane_ownership_lane_ids(ownership: LaneOwnership) -> tuple[str, ...]:
    return _normalize_lane_ownership_lane_ids(
        scope_kind=ownership.scope_kind,
        scope_id=ownership.scope_id,
        lane_ids=ownership.lane_ids,
    )


def _normalize_lane_ownership_lane_ids(
    *,
    scope_kind: str,
    scope_id: str,
    lane_ids: tuple[str, ...],
) -> tuple[str, ...]:
    normalized = _unique_nonempty(lane_ids)
    if scope_kind == "lane":
        return _unique_nonempty((scope_id, *normalized))
    if scope_kind == "lane_group":
        if not normalized:
            raise ValueError("lane_group lane ownership requires lane_ids")
        return normalized
    raise ValueError(
        f"lane ownership scope_kind must be lane or lane_group scope_kind={scope_kind!r}"
    )


def _shared_lane_ids(
    first: LaneOwnership,
    second: LaneOwnership,
) -> tuple[str, ...]:
    return tuple(
        sorted(set(_lane_ownership_lane_ids(first)).intersection(_lane_ownership_lane_ids(second)))
    )


def _allowed_lane_ownership_actions(status: str) -> tuple[str, ...]:
    if status == "claimed":
        return ("activateOwnership", "transferOwnership", "releaseOwnership")
    if status == "active":
        return ("suspendOwnership", "transferOwnership", "releaseOwnership")
    if status == "suspended":
        return ("resumeOwnership", "transferOwnership", "releaseOwnership")
    if status == "transferred":
        return ("claimLane",)
    if status == "released":
        return ("claimLane",)
    return ()


def _lane_ownership_error_message(
    prefix: str,
    *,
    ownership: LaneOwnership,
    action: str,
    allowed: tuple[str, ...],
) -> str:
    return (
        f"{prefix} scope_kind={ownership.scope_kind} scope_id={ownership.scope_id} "
        f"lane_ids={'|'.join(_lane_ownership_lane_ids(ownership))} "
        f"binding={ownership.binding_id} ownership={ownership.ownership_id} "
        f"current={ownership.status} action={action} allowed={'|'.join(allowed)}"
    )


def _find_delivery_lease(
    ledger: DeliveryLeaseLedger,
    *,
    lease_id: str = "",
    binding_id: str = "",
) -> DeliveryLease | None:
    if lease_id:
        for lease in ledger.leases:
            if lease.lease_id == lease_id:
                return lease
        return None
    if binding_id:
        active = _active_delivery_lease_for_binding(ledger, binding_id)
        if active is not None:
            return active
        for lease in reversed(ledger.leases):
            if lease.binding_id == binding_id:
                return lease
        return None
    return None


def _active_delivery_lease_for_binding(
    ledger: DeliveryLeaseLedger,
    binding_id: str,
) -> DeliveryLease | None:
    for lease in ledger.leases:
        if lease.binding_id == binding_id and _delivery_lease_active(lease):
            return lease
    return None


def _binding_from_json_dict(payload: Mapping[str, object]) -> ContinuousWorkerBinding:
    _reject_disallowed_keys(
        "worker binding",
        payload,
        disallowed={"has_private_storage"},
        record_id=str(payload.get("binding_id", "")),
    )
    _validate_no_raw_or_secret_fields(
        "worker binding",
        str(payload.get("binding_id", "")),
        payload,
    )
    runtime_provider = str(payload.get("runtime_provider", "opencode"))
    _validate_runtime_provider(runtime_provider)
    scope_kind = str(payload.get("scope_kind", ""))
    _validate_scope_kind(scope_kind)
    lifecycle_status = str(payload.get("lifecycle_status", "active"))
    _validate_lifecycle_status(lifecycle_status, allow_active=True)
    compact_policy_default = str(payload.get("compact_policy_default", "auto"))
    _validate_compact_policy_default(
        compact_policy_default,
        binding_id=str(payload.get("binding_id", "")),
        metadata=_mapping(payload.get("metadata")),
    )
    selector_payload = payload.get("active_session_selector")
    selector = (
        None
        if selector_payload is None
        else _session_selector_from_json_dict(_mapping(selector_payload))
    )
    return ContinuousWorkerBinding(
        binding_id=str(payload.get("binding_id", "")),
        worker_id=str(payload.get("worker_id", "")),
        runtime_provider=runtime_provider,  # type: ignore[arg-type]
        scope_kind=scope_kind,  # type: ignore[arg-type]
        scope_id=str(payload.get("scope_id", "")),
        lane_ids=_tuple_of_strings(payload.get("lane_ids", ())),
        lifecycle_status=lifecycle_status,  # type: ignore[arg-type]
        active_session_selector=selector,
        generation=_positive_int(payload.get("generation", 1), "worker binding generation"),
        parent_binding_id=str(payload.get("parent_binding_id", "")),
        owned_lane_ids=_tuple_of_strings(payload.get("owned_lane_ids", ())),
        private_storage_ref=str(payload.get("private_storage_ref", "")),
        private_storage_policy_ref=str(payload.get("private_storage_policy_ref", "")),
        compact_policy_ref=str(payload.get("compact_policy_ref", "")),
        compact_policy_default=compact_policy_default,  # type: ignore[arg-type]
        last_compact_at=str(payload.get("last_compact_at", "")),
        compact_needed=bool(payload.get("compact_needed", False)),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        released_at=str(payload.get("released_at", "")),
        expires_at=str(payload.get("expires_at", "")),
        last_used_at=str(payload.get("last_used_at", "")),
        compact_context_ref=str(payload.get("compact_context_ref", "")),
        mailbox_cursor_ref=str(payload.get("mailbox_cursor_ref", "")),
        worker_report_refs=_tuple_of_strings(payload.get("worker_report_refs", ())),
        audit_refs=_tuple_of_strings(payload.get("audit_refs", ())),
        reason=str(payload.get("reason", "")),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def _session_selector_from_json_dict(
    payload: Mapping[str, object],
) -> ContinuousWorkerSessionSelector:
    _validate_no_raw_or_secret_fields(
        "worker binding session selector",
        str(payload.get("session_id", "")),
        payload,
    )
    provider = str(payload.get("provider", "opencode"))
    _validate_runtime_provider(provider)
    selector = ContinuousWorkerSessionSelector(
        provider=provider,  # type: ignore[arg-type]
        attach_url=str(payload.get("attach_url", "")),
        session_id=str(payload.get("session_id", "")),
        continue_session=bool(payload.get("continue_session", False)),
        fork_session=bool(payload.get("fork_session", False)),
        metadata=dict(_mapping(payload.get("metadata"))),
    )
    _validate_session_selector(selector, expected_provider=provider)
    return selector


def _validate_session_selector(
    selector: ContinuousWorkerSessionSelector,
    *,
    expected_provider: str,
) -> None:
    _validate_runtime_provider(selector.provider)
    if selector.provider != expected_provider:
        raise ValueError(
            "continuous worker binding session selector provider must match "
            f"runtime_provider: {selector.provider!r} != {expected_provider!r}"
        )
    if selector.provider == "opencode" and not (
        selector.session_id or selector.continue_session
    ):
        raise ValueError(
            "OpenCode continuous worker session selector requires session_id or continue_session"
        )
    if selector.fork_session and not (selector.session_id or selector.continue_session):
        raise ValueError(
            "continuous worker session selector fork_session requires session_id or continue_session"
        )


def _validate_server_api_created_session_promotion_request(
    request: ServerApiCreatedSessionPromotionRequest,
) -> None:
    _validate_runtime_provider(request.provider)
    _validate_scope_kind(request.scope_kind)
    if request.provider != "opencode":
        raise ValueError(
            "server/API-created session promotion currently supports provider=opencode "
            f"provider={request.provider!r}"
        )
    if request.session_selector_source != "server_api_created":
        raise ValueError(
            "server/API-created session promotion requires "
            "session_selector_source=server_api_created "
            f"provider={request.provider} source={request.session_selector_source!r} "
            "allowed=server_api_created"
        )
    if not request.attach_url:
        raise ValueError(
            "server/API-created session promotion requires attach_url "
            f"provider={request.provider} source={request.session_selector_source}"
        )
    if not request.session_id:
        raise ValueError(
            "server/API-created session promotion requires session_id "
            f"provider={request.provider} source={request.session_selector_source}"
        )
    if not request.scope_id:
        raise ValueError(
            "server/API-created session promotion requires scope_id "
            f"scope_kind={request.scope_kind} worker_id={request.worker_id or '<missing>'}"
        )
    if not request.worker_id:
        raise ValueError(
            "server/API-created session promotion requires worker_id "
            f"scope_kind={request.scope_kind} scope_id={request.scope_id}"
        )
    lane_ids = (
        (request.scope_id,)
        if request.scope_kind == "lane" and not request.lane_ids
        else _unique_nonempty(request.lane_ids)
    )
    if request.scope_kind == "lane_group" and not lane_ids:
        raise ValueError(
            "server/API-created session promotion requires lane_ids for lane_group "
            f"scope_id={request.scope_id} worker_id={request.worker_id}"
        )
    _validate_no_raw_or_secret_fields(
        "server/API-created session promotion",
        request.binding_id or _binding_id(request.scope_kind, request.scope_id),
        {
            "attach_url": request.attach_url,
            "session_id": request.session_id,
            "reason": request.reason,
            "audit_refs": list(request.audit_refs),
            "metadata": dict(request.metadata),
        },
    )


def _binding_stale_reason_by_expiry(
    binding: ContinuousWorkerBinding,
    now: datetime,
) -> str:
    if not binding.expires_at:
        return ""
    expires_at = _parse_timestamp(binding.expires_at, "expires_at")
    if expires_at <= now:
        return "expires_at elapsed"
    return ""


def _binding_stale_reason_by_timestamp(
    binding: ContinuousWorkerBinding,
    timestamp: str,
) -> str:
    if not timestamp:
        return ""
    return _binding_stale_reason_by_expiry(
        binding,
        _parse_timestamp(timestamp, "timestamp"),
    )


def _parse_timestamp(value: str, field_name: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"continuous worker binding stale recovery {field_name} must be ISO-8601"
        ) from exc


def _binding_active(binding: ContinuousWorkerBinding) -> bool:
    return binding.lifecycle_status in {"active", "idle"}


def _binding_id(scope_kind: str, scope_id: str) -> str:
    safe_scope = scope_id.replace("\\", "/").strip("/").replace("/", "-").replace(":", "-")
    return f"continuous-worker:{scope_kind}:{safe_scope}"


def _lane_ownership_id(scope_kind: str, scope_id: str) -> str:
    safe_scope = scope_id.replace("\\", "/").strip("/").replace("/", "-").replace(":", "-")
    return f"lane-ownership:{scope_kind}:{safe_scope}"


def _validate_runtime_provider(provider: str) -> None:
    if provider not in {"fake", "qoder", "codex", "opencode"}:
        raise ValueError(
            "continuous worker binding runtime_provider must be fake, qoder, codex, or opencode"
        )


def _validate_scope_kind(scope_kind: str) -> None:
    if scope_kind not in {"lane", "lane_group", "agent", "task"}:
        raise ValueError(
            "continuous worker binding scope_kind must be lane, lane_group, agent, or task"
        )


def _validate_lifecycle_status(status: str, *, allow_active: bool) -> None:
    allowed = {
        "proposed",
        "claimed",
        "ready",
        "active",
        "idle",
        "compacting",
        "forked",
        "stale",
        "released",
        "archived",
    }
    if not allow_active:
        allowed = {"stale", "released", "archived"}
    if status not in allowed:
        raise ValueError(
            "continuous worker binding lifecycle_status must be "
            + ", ".join(sorted(allowed))
        )


def _validate_lane_ownership_scope_kind(
    scope_kind: str,
    *,
    ownership_id: str = "",
) -> None:
    if scope_kind not in {"lane", "lane_group"}:
        raise ValueError(
            "lane ownership scope_kind must be lane or lane_group "
            f"ownership={ownership_id} scope_kind={scope_kind!r}"
        )


def _validate_lane_ownership_status(
    status: str,
    *,
    ownership_id: str = "",
) -> None:
    if status not in {"claimed", "active", "suspended", "transferred", "released"}:
        raise ValueError(
            "lane ownership status must be claimed, active, suspended, "
            f"transferred, or released ownership={ownership_id} status={status!r}"
        )


def _validate_delivery_lease_status(
    status: str,
    *,
    lease_id: str = "",
    binding_id: str = "",
    task_id: str = "",
) -> None:
    if status not in {
        "reserved",
        "running",
        "completed",
        "failed_retryable",
        "failed_terminal",
        "expired",
        "released",
    }:
        raise ValueError(
            "delivery lease status must be reserved, running, completed, "
            "failed_retryable, failed_terminal, expired, or released "
            f"lease={lease_id} binding={binding_id} task={task_id} status={status!r}"
        )


def _validate_compact_policy_default(
    policy: str,
    *,
    binding_id: str,
    metadata: Mapping[str, object] | None = None,
) -> None:
    if policy not in {"auto", "manual", "llm-auto"}:
        raise ValueError(
            "compact policy rejected: compact_policy_default must be auto, "
            f"manual, or llm-auto binding={binding_id}"
        )
    metadata = _mapping(metadata)
    disables_auto_fallback = any(
        bool(metadata.get(key))
        for key in (
            "auto_fallback_disabled",
            "disable_auto_fallback",
            "manual_only",
            "compact_auto_disabled",
        )
    )
    if policy == "manual" and disables_auto_fallback:
        raise ValueError(
            "compact policy rejected: manual compact cannot disable auto fallback "
            f"binding={binding_id}"
        )


def _validate_no_raw_or_secret_fields(
    layer: str,
    record_id: str,
    value: object,
) -> None:
    blocked_key_fragments = (
        "raw_transcript",
        "transcript_text",
        "transcript_body",
        "secret_value",
        "api_key",
        "access_token",
        "password",
        "credential",
    )
    for path, item in _walk_mapping_items(value):
        if path[:1] == ("authority_split",):
            continue
        lowered_path = ".".join(path).lower()
        if any(fragment in lowered_path for fragment in blocked_key_fragments):
            raise ValueError(
                f"{layer} rejected: raw transcript or secret value is not allowed "
                f"id={record_id} field={'.'.join(path)}"
            )
        if any(segment.lower() in {"secret", "secrets"} for segment in path):
            raise ValueError(
                f"{layer} rejected: raw transcript or secret value is not allowed "
                f"id={record_id} field={'.'.join(path)}"
            )
        if isinstance(item, str) and _looks_like_secret_or_raw_transcript(item):
            raise ValueError(
                f"{layer} rejected: raw transcript or secret value is not allowed "
                f"id={record_id} field={'.'.join(path)}"
            )


def _walk_mapping_items(value: object) -> tuple[tuple[tuple[str, ...], object], ...]:
    items: list[tuple[tuple[str, ...], object]] = []

    def visit(current: object, path: tuple[str, ...]) -> None:
        if isinstance(current, Mapping):
            for key, nested in current.items():
                nested_path = (*path, str(key))
                items.append((nested_path, nested))
                visit(nested, nested_path)
        elif isinstance(current, (list, tuple)):
            for index, nested in enumerate(current):
                visit(nested, (*path, str(index)))

    visit(value, ())
    return tuple(items)


def _looks_like_secret_or_raw_transcript(value: str) -> bool:
    lowered = value.lower()
    if "raw transcript" in lowered:
        return True
    if "raw_transcript" in lowered:
        return True
    secret_markers = (
        "api_key=",
        "access_token=",
        "password=",
        "secret=",
        "bearer ",
    )
    return any(marker in lowered for marker in secret_markers)


def _reject_disallowed_keys(
    layer: str,
    payload: Mapping[str, object],
    *,
    disallowed: set[str],
    record_id: str,
) -> None:
    for key in payload:
        if key in disallowed:
            raise ValueError(
                f"{layer} schema rejected: private storage is a derived invariant, "
                f"use private_storage_ref/private_storage_policy_ref id={record_id}"
            )


def _positive_int(value: object, field_name: str) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if normalized < 1:
        raise ValueError(f"{field_name} must be >= 1")
    return normalized


def _delivery_lease_active(lease: DeliveryLease) -> bool:
    return lease.status in {"reserved", "running"}


def _delivery_lease_id(binding_id: str, delivery_id: str) -> str:
    safe_binding = binding_id.replace("\\", "/").strip("/").replace("/", "-")
    safe_delivery = delivery_id.replace("\\", "/").strip("/").replace("/", "-")
    return f"continuous-worker-delivery-lease:{safe_binding}:{safe_delivery}"


def _default_private_storage_ref(binding_id: str) -> str:
    return f"dbc://agent-home/continuous-worker/{binding_id}"


def _default_private_storage_policy_ref() -> str:
    return "dbc://agent-home-policy/continuous-worker/default-retain-after-owned-lanes-merge"


def _unique_nonempty(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if value and value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _merge_unique(
    existing: tuple[str, ...],
    incoming: tuple[str, ...],
) -> tuple[str, ...]:
    return _unique_nonempty((*existing, *incoming))


def _merge_metadata(
    *metadata_values: Mapping[str, object],
) -> Mapping[str, object]:
    merged: dict[str, object] = {}
    for metadata in metadata_values:
        merged.update({key: value for key, value in dict(metadata).items() if value != ""})
    return merged


def _tuple_of_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return _unique_nonempty(tuple(str(item) for item in value))
    if isinstance(value, list):
        return _unique_nonempty(tuple(str(item) for item in value))
    return (str(value),) if str(value) else ()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _authority_split(*, ledger_mutated: bool) -> dict[str, object]:
    return {
        "host_owned": True,
        "continuous_worker_binding_ledger_mutated": ledger_mutated,
        "provider_executed": False,
        "server_started": False,
        "server_stopped": False,
        "scheduler_state_mutated": False,
        "delivery_state_mutated": False,
        "runtime_invocation_log_mutated": False,
        "local_work_trajectory_mutated": False,
        "raw_transcript_persisted": False,
        "secret_value_persisted": False,
    }


__all__ = [
    "CONTINUOUS_WORKER_BINDING_LEDGER_SCHEMA_VERSION",
    "CONTINUOUS_WORKER_BINDING_EVENT_LOG_SCHEMA_VERSION",
    "CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_SCHEMA_VERSION",
    "CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_SCHEMA_VERSION",
    "CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_SCHEMA_VERSION",
    "CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_SCHEMA_VERSION",
    "DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH",
    "DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH",
    "DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH",
    "DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH",
    "DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH",
    "DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH",
    "CompactPolicyDefault",
    "ContinuousWorkerBinding",
    "ContinuousWorkerBindingEventKind",
    "ContinuousWorkerBindingEventRecord",
    "ContinuousWorkerBindingClaimRequest",
    "ContinuousWorkerBindingCompactRequest",
    "ContinuousWorkerBindingForkRequest",
    "ContinuousWorkerBindingInspectRequest",
    "ContinuousWorkerBindingLedger",
    "ContinuousWorkerBindingRecoverStaleRequest",
    "ContinuousWorkerBindingReleaseRequest",
    "ContinuousWorkerBindingReuseRequest",
    "ContinuousWorkerBindingResolveRequest",
    "ContinuousWorkerBindingResult",
    "ContinuousWorkerLifecycleStatus",
    "ContinuousWorkerScopeKind",
    "ContinuousWorkerSessionSelector",
    "ServerApiCreatedSessionPromotionRequest",
    "ServerApiCreatedSessionPromotionResult",
    "DeliveryLease",
    "DeliveryLeaseBeginRequest",
    "DeliveryLeaseCompleteRequest",
    "DeliveryLeaseEventKind",
    "DeliveryLeaseEventRecord",
    "DeliveryLeaseExpireRequest",
    "DeliveryLeaseFailRequest",
    "DeliveryLeaseInspectRequest",
    "DeliveryLeaseLedger",
    "DeliveryLeaseReleaseRequest",
    "DeliveryLeaseReserveRequest",
    "DeliveryLeaseResult",
    "DeliveryLeaseStatus",
    "JsonlContinuousWorkerBindingEventLog",
    "JsonlDeliveryLeaseEventLog",
    "JsonlLaneOwnershipEventLog",
    "LaneOwnership",
    "LaneOwnershipActivateRequest",
    "LaneOwnershipClaimRequest",
    "LaneOwnershipEventKind",
    "LaneOwnershipEventRecord",
    "LaneOwnershipInspectRequest",
    "LaneOwnershipLedger",
    "LaneOwnershipReleaseRequest",
    "LaneOwnershipResult",
    "LaneOwnershipResumeRequest",
    "LaneOwnershipScopeKind",
    "LaneOwnershipStatus",
    "LaneOwnershipSuspendRequest",
    "LaneOwnershipTransferRequest",
    "active_delivery_lease_conflicts",
    "activate_lane_ownership",
    "begin_delivery_lease_run",
    "binding_has_active_delivery_lease",
    "claim_continuous_worker_binding",
    "claim_lane_ownership",
    "compact_continuous_worker_binding",
    "complete_delivery_lease",
    "continuous_worker_binding_from_json_dict",
    "continuous_worker_binding_event_record_from_json_dict",
    "delivery_lease_from_json_dict",
    "delivery_lease_event_record_from_json_dict",
    "expire_delivery_lease",
    "fail_delivery_lease_retryable",
    "fail_delivery_lease_terminal",
    "fork_continuous_worker_binding",
    "inspect_delivery_leases",
    "inspect_lane_ownerships",
    "inspect_continuous_worker_bindings",
    "lane_ownership_allows_delivery",
    "lane_ownership_from_json_dict",
    "lane_ownership_event_record_from_json_dict",
    "record_continuous_worker_binding_reuse",
    "promote_server_api_created_session_to_continuous_worker_binding",
    "read_delivery_lease_ledger",
    "read_lane_ownership_ledger",
    "read_continuous_worker_binding_ledger",
    "recover_stale_continuous_worker_bindings",
    "release_delivery_lease",
    "release_lane_ownership",
    "release_continuous_worker_binding",
    "resume_lane_ownership",
    "reserve_delivery_lease",
    "resolve_continuous_worker_binding",
    "selectable_lane_ownership_conflicts",
    "suspend_lane_ownership",
    "transfer_lane_ownership",
    "validate_no_active_delivery_lease_conflicts",
    "validate_no_selectable_lane_ownership_conflicts",
    "write_delivery_lease_ledger",
    "write_lane_ownership_ledger",
    "write_continuous_worker_binding_ledger",
]
