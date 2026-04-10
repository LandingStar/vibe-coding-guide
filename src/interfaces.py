"""Protocol definitions for PEP ↔ Subagent integration.

These protocols break the circular dependency between PEP and the
subagent runtime by providing a stable contract layer both sides can
code against.
"""

from __future__ import annotations

from typing import Protocol


class WorkerBackend(Protocol):
    """Execute a subagent contract and return a report."""

    def execute(self, contract: dict) -> dict:
        """Accept a Subagent Contract dict and return a Subagent Report dict."""
        ...


class ContractFactory(Protocol):
    """Build a full Subagent Contract from a delegation decision."""

    def build(self, delegation_decision: dict) -> dict:
        """Transform delegation_decision (with contract_hints) into a
        complete contract conforming to subagent-contract.schema.json."""
        ...


class ReportValidator(Protocol):
    """Validate a Subagent Report against the schema."""

    def validate(self, report: dict) -> dict:
        """Return a structured validation result dict.

        Expected keys:
        - ``valid`` (bool): whether the report is schema-compliant.
        - ``errors`` (list[str]): human-readable error descriptions,
          empty when valid.
        """
        ...


class EscalationNotifier(Protocol):
    """Deliver an escalation notification to the target authority."""

    def notify(self, notification: dict) -> dict:
        """Send *notification* and return a delivery result dict.

        Expected keys:
        - ``delivered`` (bool): whether the notification was accepted.
        - ``channel`` (str): the delivery channel used.
        """
        ...
