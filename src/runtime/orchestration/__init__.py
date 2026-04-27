"""Orchestration runtime primitives and helpers."""

from .models import (
    BridgeGroupItem,
    BridgeGroupLifecycle,
    BridgeWorkItem,
    BridgeWorkLifecycle,
    GovernanceSurfaceKind,
    GovernanceSurfaceState,
    WritebackDisposition,
)
from .coordinator import CoordinatorAdvanceResult, advance_work_item_from_execution_result
from .executor_adapter import project_execution_result_to_group_item
from .landing import BridgeLandingArtifact, BridgeLandingKind, build_landing_artifact
from .landing_consumers import (
    BridgeLandingConsumerKind,
    BridgeLandingConsumerPayload,
    build_landing_consumer_payload,
)
from .projection import project_group_item_surface
from .rollup import roll_up_work_item
from .stop_conditions import evaluate_stop_condition

__all__ = [
    "BridgeGroupItem",
    "BridgeGroupLifecycle",
    "BridgeLandingArtifact",
    "BridgeLandingConsumerKind",
    "BridgeLandingConsumerPayload",
    "BridgeLandingKind",
    "BridgeWorkItem",
    "BridgeWorkLifecycle",
    "CoordinatorAdvanceResult",
    "GovernanceSurfaceKind",
    "GovernanceSurfaceState",
    "WritebackDisposition",
    "advance_work_item_from_execution_result",
    "build_landing_artifact",
    "build_landing_consumer_payload",
    "project_execution_result_to_group_item",
    "project_group_item_surface",
    "roll_up_work_item",
    "evaluate_stop_condition",
]