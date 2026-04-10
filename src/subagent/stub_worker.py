"""Stub implementation of WorkerBackend for testing.

Returns a synthetic report matching the contract, without performing
any real work.  Used to validate the PEP → Worker → Report pipeline.
"""

from __future__ import annotations

import uuid


class StubWorkerBackend:
    """Minimal WorkerBackend that echoes contract info as a report."""

    def execute(self, contract: dict) -> dict:
        contract_id = contract.get("contract_id", "contract-unknown")
        return {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "contract_id": contract_id,
            "status": "completed",
            "changed_artifacts": [],
            "verification_results": [
                "Stub worker: no real changes made.",
            ],
            "escalation_recommendation": "none",
        }
