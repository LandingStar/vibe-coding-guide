"""HTTP Worker — delegate contracts to an external HTTP API endpoint.

Posts the contract JSON to the configured URL and expects a report
JSON in response.  Uses stdlib ``urllib.request`` only.
"""

from __future__ import annotations

import json
import time
import uuid
import urllib.error
import urllib.request

from .base import WorkerConfig


class HTTPWorker:
    """WorkerBackend that delegates contracts via HTTP POST.

    The target service is expected to accept a subagent contract JSON
    and return a subagent report JSON.
    """

    def __init__(self, config: WorkerConfig) -> None:
        if not config.base_url:
            raise ValueError("HTTPWorker requires config.base_url.")
        self._config = config

    def execute(self, contract: dict) -> dict:
        """POST contract to the external API and return the report."""
        contract_id = contract.get("contract_id", "contract-unknown")

        try:
            response_data = self._post(contract)
        except HTTPWorkerError as exc:
            return self._error_report(contract_id, str(exc))

        # Ensure required fields exist in response
        if "report_id" not in response_data:
            response_data["report_id"] = f"report-{uuid.uuid4().hex[:12]}"
        if "contract_id" not in response_data:
            response_data["contract_id"] = contract_id
        if "status" not in response_data:
            response_data["status"] = "completed"

        return response_data

    def _post(self, contract: dict) -> dict:
        """POST contract JSON with retry logic."""
        url = self._config.base_url
        api_key = self._config.api_key

        headers = {
            "Content-Type": "application/json",
            **self._config.headers,
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        body = json.dumps(contract, ensure_ascii=False).encode("utf-8")

        last_error: Exception | None = None
        for attempt in range(self._config.max_retries + 1):
            try:
                req = urllib.request.Request(
                    url, data=body, headers=headers, method="POST",
                )
                with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last_error = exc
                if 400 <= exc.code < 500 and exc.code != 429:
                    raise HTTPWorkerError(
                        f"HTTP {exc.code}: {exc.reason}"
                    ) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc

            if attempt < self._config.max_retries:
                time.sleep(min(2 ** attempt, 8))

        raise HTTPWorkerError(
            f"HTTP call failed after {self._config.max_retries + 1} attempts: "
            f"{last_error}"
        )

    @staticmethod
    def _error_report(contract_id: str, error_msg: str) -> dict:
        return {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "contract_id": contract_id,
            "status": "blocked",
            "changed_artifacts": [],
            "verification_results": [
                f"HTTP worker error: {error_msg}",
            ],
            "unresolved_items": [
                "HTTP API call failed before a response was produced.",
            ],
            "escalation_recommendation": "review_by_supervisor",
        }


class HTTPWorkerError(Exception):
    """Raised when the HTTP API call fails."""
