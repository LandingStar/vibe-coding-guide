"""Build a full Subagent Contract from a delegation decision.

Implements the ContractFactory protocol defined in src.interfaces.
"""

from __future__ import annotations

import uuid


def build(delegation_decision: dict) -> dict:
    """Transform a delegation decision (with ``contract_hints``) into a
    complete contract conforming to ``subagent-contract.schema.json``.

    The caller is responsible for ensuring ``delegation_decision`` has
    ``delegate=True`` and a ``contract_hints`` dict.
    """
    hints = delegation_decision.get("contract_hints", {})

    contract_id = f"contract-{uuid.uuid4().hex[:12]}"
    task = hints.get("suggested_task", "Perform delegated work.")
    mode = delegation_decision.get("mode", "supervisor-worker")

    # Map collaboration mode to schema enum value.
    mode_map = {
        "supervisor-worker": "worker",
        "worker": "worker",
        "handoff": "handoff",
        "team": "team",
        "swarm": "swarm",
        "subgraph": "subgraph",
    }
    schema_mode = mode_map.get(mode, "worker")

    scope = delegation_decision.get(
        "scope_summary",
        "Execute narrowly scoped work as described in the task.",
    )

    out_of_scope = hints.get("out_of_scope", [
        "Do not modify authoritative platform docs.",
    ])

    contract: dict = {
        "contract_id": contract_id,
        "task": task,
        "mode": schema_mode,
        "scope": scope,
        "allowed_artifacts": hints.get("allowed_artifacts", []),
        "required_refs": hints.get("required_refs", ["docs/README.md"]),
        "acceptance": hints.get("acceptance", [
            "Task completed as described.",
        ]),
        "verification": hints.get("verification", [
            "Run relevant tests.",
        ]),
        "out_of_scope": out_of_scope if out_of_scope else [
            "No explicit exclusions.",
        ],
        "report_schema": "subagent-report",
    }
    return contract
