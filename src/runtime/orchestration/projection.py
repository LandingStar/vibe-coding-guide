"""Projection helpers for orchestration bridge group items."""

from __future__ import annotations

from dataclasses import replace

from .models import (
    BridgeGroupItem,
    DeliveryState,
    DeliverySurfaceKind,
    GovernanceSurfaceKind,
    GovernanceSurfaceState,
    WritebackDisposition,
)


def project_group_item_surface(
    group_item: BridgeGroupItem,
    *,
    governance_surface_kind: GovernanceSurfaceKind,
    governance_surface_state: GovernanceSurfaceState = "",
    blocked_reason: str = "",
    writeback_disposition: WritebackDisposition = "pending",
) -> BridgeGroupItem:
    """Project a compact governance footprint onto a group item.

    The helper is pure: it returns a new settled group item and leaves the
    original instance unchanged.
    """

    return replace(
        group_item,
        lifecycle_state="settled",
        governance_surface_kind=governance_surface_kind,
        governance_surface_state=governance_surface_state,
        blocked_reason=blocked_reason,
        writeback_disposition=writeback_disposition,
    )


def project_group_item_delivery_signal(
    group_item: BridgeGroupItem,
    *,
    delivery_surface_kind: DeliverySurfaceKind,
    delivery_state: DeliveryState,
    delivery_record_id: str = "",
    delivery_failure_detail: str = "",
) -> BridgeGroupItem:
    """Overlay a compact owner-facing delivery footprint onto a group item.

    The helper is pure: it returns a new group item and leaves governance-side
    and lifecycle state unchanged.
    """

    return replace(
        group_item,
        delivery_surface_kind=delivery_surface_kind,
        delivery_state=delivery_state,
        delivery_record_id=delivery_record_id,
        delivery_failure_detail=delivery_failure_detail,
    )