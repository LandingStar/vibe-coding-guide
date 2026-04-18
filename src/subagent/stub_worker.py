"""Stub implementation of WorkerBackend for testing.

Returns a synthetic report matching the contract, without performing
any real work.  Used to validate the PEP → Worker → Report pipeline.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path


_DEFAULT_DIRECTORY_PAYLOAD = "stub-worker-output.md"


class StubWorkerBackend:
    """Minimal WorkerBackend that echoes contract info as a report."""

    def execute(self, contract: dict) -> dict:
        contract_id = contract.get("contract_id", "contract-unknown")
        report = {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "contract_id": contract_id,
            "status": "completed",
            "changed_artifacts": [],
            "verification_results": [
                "Stub worker: no direct file changes were made.",
            ],
            "escalation_recommendation": "none",
        }

        payload = self._build_payload(
            contract_id,
            contract.get("allowed_artifacts") or [],
        )
        if payload is not None:
            report["artifact_payloads"] = [payload]
            report["verification_results"].append(
                f"Stub worker: emitted 1 synthetic artifact payload for {payload['path']}."
            )

        return report

    def _build_payload(self, contract_id: str, allowed_artifacts: object) -> dict | None:
        target_path = self._select_payload_path(allowed_artifacts)
        if target_path is None:
            return None

        content_type = self._infer_content_type(target_path)
        return {
            "path": target_path,
            "content": self._render_content(contract_id, target_path, content_type),
            "operation": "update",
            "content_type": content_type,
        }

    def _select_payload_path(self, allowed_artifacts: object) -> str | None:
        if not isinstance(allowed_artifacts, list):
            return None

        for value in allowed_artifacts:
            normalized = self._normalize_allowed_path(value)
            if normalized is None:
                continue
            if not normalized:
                return _DEFAULT_DIRECTORY_PAYLOAD
            if self._looks_like_file_path(normalized):
                return normalized
            return f"{normalized.rstrip('/')}/{_DEFAULT_DIRECTORY_PAYLOAD}"
        return None

    @staticmethod
    def _normalize_allowed_path(value: object) -> str | None:
        if not isinstance(value, str):
            return None

        stripped = value.strip()
        if not stripped:
            return None

        candidate = Path(stripped)
        if candidate.is_absolute() or ".." in candidate.parts:
            return None

        normalized = candidate.as_posix()
        if normalized == ".":
            return ""
        return normalized

    @staticmethod
    def _looks_like_file_path(path: str) -> bool:
        name = Path(path).name
        return bool(name) and name not in {".", ".."} and "." in name

    @staticmethod
    def _infer_content_type(target_path: str) -> str:
        suffix = Path(target_path).suffix.lower()
        if suffix == ".md":
            return "markdown"
        if suffix == ".json":
            return "json"
        if suffix in {".yaml", ".yml"}:
            return "yaml"
        return "text"

    @staticmethod
    def _render_content(contract_id: str, target_path: str, content_type: str) -> str:
        if content_type == "json":
            return json.dumps(
                {
                    "stub": True,
                    "contract_id": contract_id,
                    "target_path": target_path,
                },
                ensure_ascii=True,
                indent=2,
            ) + "\n"

        if content_type == "yaml":
            return (
                "stub: true\n"
                f'contract_id: "{contract_id}"\n'
                f'target_path: "{target_path}"\n'
            )

        if content_type == "markdown":
            return (
                "# Stub Worker Output\n\n"
                f"- Contract: {contract_id}\n"
                f"- Target: {target_path}\n"
            )

        return (
            "Stub worker output\n"
            f"contract_id={contract_id}\n"
            f"target_path={target_path}\n"
        )
