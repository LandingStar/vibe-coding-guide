"""Tool Permission Resolver — evaluates per-tool permission policies.

Implements B-REF-4: Permission policy layered override model.
Checks pack-level default + per-tool override policies before PDP/PEP execution.
"""

from __future__ import annotations

from ..interfaces import (
    PermissionLevel,
    PermissionResult,
    ToolPermissionConfig,
    ToolPolicy,
    parse_tool_permissions,
)

# Re-export for backward compatibility
__all__ = [
    "PermissionLevel",
    "PermissionResult",
    "ToolPermissionConfig",
    "ToolPolicy",
    "parse_tool_permissions",
    "resolve",
    "merge_configs",
]

# Severity ordering for merging across packs (strictest wins)
_PERMISSION_SEVERITY: dict[str, int] = {"allow": 0, "ask": 1, "deny": 2}


def resolve(action_type: str, config: ToolPermissionConfig) -> PermissionResult:
    """Resolve permission for a given action_type against a ToolPermissionConfig.

    Returns the effective permission level and any deny_message.
    """
    if not action_type:
        return PermissionResult(permission="allow", policy_source="no_action_type")

    policy = config.policies.get(action_type)
    if policy is not None:
        return PermissionResult(
            permission=policy.permission,
            deny_message=policy.deny_message,
            policy_source=f"tool_policy:{action_type}",
        )

    # Fall back to pack default
    return PermissionResult(
        permission=config.default,
        deny_message="" if config.default != "deny" else f"Action '{action_type}' denied by default policy.",
        policy_source="pack_default",
    )


def merge_configs(configs: list[tuple[int, ToolPermissionConfig]]) -> ToolPermissionConfig:
    """Merge multiple ToolPermissionConfigs from different packs.

    Each entry is (priority, config) where higher priority = higher precedence.
    For the same action_type across packs, the strictest permission wins (deny > ask > allow).
    For the default level, the strictest across all packs wins.

    Args:
        configs: List of (priority, config) tuples, sorted by priority ascending.

    Returns:
        Merged ToolPermissionConfig.
    """
    if not configs:
        return ToolPermissionConfig()

    if len(configs) == 1:
        return configs[0][1]

    # Merge defaults: strictest wins
    merged_default: PermissionLevel = "allow"
    for _, cfg in configs:
        if _PERMISSION_SEVERITY.get(cfg.default, 0) > _PERMISSION_SEVERITY.get(merged_default, 0):
            merged_default = cfg.default

    # Merge per-tool policies: strictest wins per action_type
    merged_policies: dict[str, ToolPolicy] = {}
    for _, cfg in configs:
        for action_type, policy in cfg.policies.items():
            existing = merged_policies.get(action_type)
            if existing is None:
                merged_policies[action_type] = ToolPolicy(
                    permission=policy.permission,
                    deny_message=policy.deny_message,
                )
            elif _PERMISSION_SEVERITY.get(policy.permission, 0) > _PERMISSION_SEVERITY.get(existing.permission, 0):
                merged_policies[action_type] = ToolPolicy(
                    permission=policy.permission,
                    deny_message=policy.deny_message or existing.deny_message,
                )

    return ToolPermissionConfig(default=merged_default, policies=merged_policies)
