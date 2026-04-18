"""LLM Worker — execute contracts via OpenAI-compatible LLM API.

Uses stdlib ``urllib.request`` only — no third-party LLM SDK required.
Compatible with Aliyun DashScope, OpenAI, and any OpenAI-compatible endpoint.

API keys are read from environment variables via ``WorkerConfig.api_key``.
"""

from __future__ import annotations

import json
import time
import uuid
import urllib.error
import urllib.request
from typing import Any

from .base import WorkerConfig

_ALLOWED_STATUSES = {"completed", "partial", "blocked"}
_ALLOWED_ESCALATIONS = {"none", "review_by_supervisor", "human_review"}
_ALLOWED_OPERATIONS = {"create", "update", "append"}
_ALLOWED_CONTENT_TYPES = {"markdown", "json", "yaml", "text"}
_CONTENT_TYPE_ALIASES = {
    "text/markdown": "markdown",
    "text/plain": "text",
    "application/json": "json",
}


class LLMWorker:
    """WorkerBackend that delegates contract tasks to an LLM.

    The worker translates contract fields (task, scope, required_refs,
    acceptance criteria) into a structured prompt, sends it to an
    OpenAI-compatible chat completion endpoint, and wraps the response
    in a subagent report.
    """

    def __init__(self, config: WorkerConfig) -> None:
        if not config.base_url:
            raise ValueError("LLMWorker requires config.base_url.")
        self._config = config

    def execute(self, contract: dict) -> dict:
        """Execute a subagent contract via LLM API and return a report."""
        prompt = self._build_prompt(contract)
        contract_id = contract.get("contract_id", "contract-unknown")
        allowed_artifacts = contract.get("allowed_artifacts") or []

        try:
            response_text = self._call_llm(prompt)
        except LLMWorkerError as exc:
            return self._error_report(contract_id, str(exc))

        return self._build_report(contract_id, response_text, allowed_artifacts)

    # ── Prompt construction ─────────────────────────────

    @staticmethod
    def _build_prompt(contract: dict) -> str:
        """Translate contract fields into a structured LLM prompt."""
        task = contract.get("task", "No task specified.")
        scope = contract.get("scope", "")
        refs = contract.get("required_refs", [])
        acceptance = contract.get("acceptance", [])
        out_of_scope = contract.get("out_of_scope", [])
        allowed_artifacts = contract.get("allowed_artifacts") or []

        parts = [
            "You are a focused worker agent. Complete the following task:",
            "",
            f"## Task\n{task}",
        ]
        if scope:
            parts.append(f"\n## Scope\n{scope}")
        if refs:
            parts.append(f"\n## Required References\n" + "\n".join(f"- {r}" for r in refs))
        if acceptance:
            parts.append(f"\n## Acceptance Criteria\n" + "\n".join(f"- {a}" for a in acceptance))
        if out_of_scope:
            parts.append(f"\n## Out of Scope\n" + "\n".join(f"- {o}" for o in out_of_scope))
        parts.append(
            "\n## Instructions\n"
            "Return JSON only. Do not wrap the JSON in markdown fences or add any extra prose. "
            "The JSON object may contain only these keys: status, verification_results, "
            "unresolved_items, assumptions, escalation_recommendation, artifact_payloads."
        )
        parts.append(
            "\n## Response Contract\n"
            "- status: completed | partial | blocked\n"
            "- verification_results: array of concise evidence strings\n"
            "- unresolved_items: optional array of remaining gaps\n"
            "- assumptions: optional array of assumptions that need supervisor review\n"
            "- escalation_recommendation: none | review_by_supervisor | human_review\n"
            "- artifact_payloads: optional array with at most one object containing path, content, operation, content_type\n"
            "- artifact_payloads.operation must be exactly one of: create | update | append\n"
            "- artifact_payloads.content_type must be exactly one of: markdown | json | yaml | text\n"
            "- Do not include report_id, contract_id, changed_artifacts, llm_response, or any other keys\n"
            "- artifact_payloads.content must always be a string\n"
            "- Never use upsert or MIME-style content_type values such as text/markdown, text/plain, or application/json"
        )
        normalized_artifacts = [
            artifact.replace("\\", "/").strip()
            for artifact in allowed_artifacts
            if isinstance(artifact, str) and artifact.strip()
        ]
        if normalized_artifacts:
            parts.append(
                "\n## Allowed Artifacts\n" +
                "\n".join(f"- {artifact}" for artifact in normalized_artifacts)
            )
            parts.append(
                "\nOnly propose artifact_payloads inside the allowed artifacts listed above. "
                "Return at most one artifact_payload. If you cannot satisfy the allowed operation and content_type values exactly, omit artifact_payloads entirely."
            )
        else:
            parts.append(
                "\n## Artifact Payload Constraint\n"
                "Do not include artifact_payloads unless allowed_artifacts are provided."
            )
        return "\n".join(parts)

    # ── LLM API call ────────────────────────────────────

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API with retry logic. Returns response text."""
        api_key = self._config.api_key
        if not api_key:
            raise LLMWorkerError(
                f"API key not found. Set environment variable "
                f"'{self._config.api_key_env}'."
            )

        url = self._config.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            **self._config.headers,
        }
        body = json.dumps({
            "model": self._config.model or "qwen-plus",
            "messages": [
                {"role": "system", "content": "You are a precise worker agent."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
        }).encode("utf-8")

        last_error: Exception | None = None
        for attempt in range(self._config.max_retries + 1):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return self._extract_content(data)
            except urllib.error.HTTPError as exc:
                last_error = exc
                # Don't retry on 4xx client errors (except 429)
                if 400 <= exc.code < 500 and exc.code != 429:
                    raise LLMWorkerError(
                        f"HTTP {exc.code}: {exc.reason}"
                    ) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc

            # Exponential backoff before retry
            if attempt < self._config.max_retries:
                time.sleep(min(2 ** attempt, 8))

        raise LLMWorkerError(
            f"LLM API call failed after {self._config.max_retries + 1} attempts: "
            f"{last_error}"
        )

    @staticmethod
    def _extract_content(response_data: dict) -> str:
        """Extract the assistant message content from API response."""
        try:
            choices = response_data["choices"]
            return choices[0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMWorkerError(
                f"Unexpected API response format: {exc}"
            ) from exc

    # ── Report construction ─────────────────────────────

    @staticmethod
    def _build_report(
        contract_id: str,
        response_text: str,
        allowed_artifacts: list[str] | None = None,
    ) -> dict:
        """Normalize an LLM response into a schema-valid subagent report."""
        allowed_artifacts = allowed_artifacts or []

        try:
            response_data = LLMWorker._parse_response_fragment(response_text)
        except ValueError as exc:
            return LLMWorker._partial_report(contract_id, response_text, str(exc))

        verification_results = LLMWorker._normalize_string_list(
            response_data.get("verification_results")
        )
        status = response_data.get("status")
        if status not in _ALLOWED_STATUSES:
            status = "completed"
            verification_results.append(
                "LLM response omitted or used an invalid status; defaulted to completed."
            )

        if not verification_results:
            verification_results = [
                f"LLM worker returned structured response with status={status}.",
                f"Response length: {len(response_text)} characters.",
            ]

        unresolved_items = LLMWorker._normalize_string_list(
            response_data.get("unresolved_items")
        )
        assumptions = LLMWorker._normalize_string_list(
            response_data.get("assumptions")
        )
        artifact_payloads, payload_notes, payload_attempted = LLMWorker._normalize_artifact_payloads(
            response_data.get("artifact_payloads"),
            allowed_artifacts,
        )
        verification_results.extend(payload_notes)
        if status == "completed" and payload_attempted and not artifact_payloads:
            status = "partial"
            verification_results.append(
                "Downgraded report status to partial because the LLM attempted artifact_payloads but none passed output guard normalization."
            )

        escalation = response_data.get("escalation_recommendation")
        if escalation not in _ALLOWED_ESCALATIONS:
            escalation = "none" if status == "completed" else "review_by_supervisor"
            if response_data.get("escalation_recommendation") is not None:
                verification_results.append(
                    "LLM response used an invalid escalation_recommendation; defaulted to a schema-valid value."
                )

        report = {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "contract_id": contract_id,
            "status": status,
            "changed_artifacts": [],
            "verification_results": verification_results,
            "escalation_recommendation": escalation,
        }
        if unresolved_items:
            report["unresolved_items"] = unresolved_items
        if assumptions:
            report["assumptions"] = assumptions
        if artifact_payloads:
            report["artifact_payloads"] = artifact_payloads
        return report

    @staticmethod
    def _parse_response_fragment(response_text: str) -> dict[str, Any]:
        candidate = LLMWorker._strip_json_fence(response_text)
        try:
            response_data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError(f"response is not valid JSON: {exc.msg}") from exc
        if not isinstance(response_data, dict):
            raise ValueError("response JSON must be an object")
        return response_data

    @staticmethod
    def _strip_json_fence(response_text: str) -> str:
        stripped = response_text.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if len(lines) < 3:
            return stripped
        if not lines[-1].strip().startswith("```"):
            return stripped
        return "\n".join(lines[1:-1]).strip()

    @staticmethod
    def _normalize_string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]

    @staticmethod
    def _normalize_artifact_payloads(
        payloads: Any,
        allowed_artifacts: list[str],
    ) -> tuple[list[dict[str, str]], list[str], bool]:
        payload_attempted = payloads is not None and payloads != []
        if not payloads:
            return [], [], payload_attempted

        if not allowed_artifacts:
            return [], [
                "Ignored artifact_payloads because contract.allowed_artifacts is empty."
            ], payload_attempted

        if not isinstance(payloads, list):
            return [], [
                "Ignored artifact_payloads because the LLM response used a non-list payload shape."
            ], payload_attempted

        normalized_payloads: list[dict[str, str]] = []
        notes: list[str] = []
        for index, payload in enumerate(payloads, start=1):
            normalized, payload_notes = LLMWorker._normalize_artifact_payload(
                payload,
                index,
            )
            notes.extend(payload_notes)
            if normalized is None:
                continue
            normalized_payloads.append(normalized)

        if len(normalized_payloads) > 1:
            notes.append(
                "LLM response returned multiple artifact_payloads; kept only the first payload."
            )
        return normalized_payloads[:1], notes, payload_attempted

    @staticmethod
    def _normalize_artifact_payload(
        payload: Any,
        index: int,
    ) -> tuple[dict[str, str] | None, list[str]]:
        if not isinstance(payload, dict):
            return None, [
                f"Rejected artifact_payload[{index}] because it is not an object."
            ]

        path = payload.get("path")
        content = payload.get("content")
        operation = payload.get("operation")
        content_type = payload.get("content_type")

        if not isinstance(path, str) or not path.strip():
            return None, [
                f"Rejected artifact_payload[{index}] because path is missing or empty."
            ]
        if not isinstance(content, str):
            return None, [
                f"Rejected artifact_payload[{index}] because content is not a string."
            ]
        if not isinstance(operation, str) or operation not in _ALLOWED_OPERATIONS:
            return None, [
                f"Rejected artifact_payload[{index}] because operation '{operation}' is not allowed."
            ]
        if not isinstance(content_type, str) or not content_type.strip():
            return None, [
                f"Rejected artifact_payload[{index}] because content_type is missing or empty."
            ]

        normalized_content_type = content_type.strip().lower()
        alias_content_type = _CONTENT_TYPE_ALIASES.get(normalized_content_type)
        notes: list[str] = []
        if alias_content_type is not None:
            notes.append(
                f"Normalized artifact_payload[{index}] content_type from '{content_type}' to '{alias_content_type}'."
            )
            normalized_content_type = alias_content_type
        elif normalized_content_type != content_type:
            notes.append(
                f"Normalized artifact_payload[{index}] content_type formatting from '{content_type}' to '{normalized_content_type}'."
            )

        if normalized_content_type not in _ALLOWED_CONTENT_TYPES:
            return None, [
                f"Rejected artifact_payload[{index}] because content_type '{content_type}' is not allowed."
            ]

        return {
            "path": path.strip().replace("\\", "/"),
            "content": content,
            "operation": operation,
            "content_type": normalized_content_type,
        }, notes

    @staticmethod
    def _partial_report(contract_id: str, response_text: str, error_msg: str) -> dict:
        return {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "contract_id": contract_id,
            "status": "partial",
            "changed_artifacts": [],
            "verification_results": [
                "LLM worker returned an unstructured response; structured parsing failed.",
                f"Response length: {len(response_text)} characters.",
                f"Parsing error: {error_msg}",
            ],
            "unresolved_items": [
                "LLM response did not match the expected JSON response contract.",
            ],
            "escalation_recommendation": "review_by_supervisor",
        }

    @staticmethod
    def _error_report(contract_id: str, error_msg: str) -> dict:
        """Build a failure report when the LLM call fails."""
        return {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "contract_id": contract_id,
            "status": "blocked",
            "changed_artifacts": [],
            "verification_results": [
                f"LLM worker error: {error_msg}",
            ],
            "unresolved_items": [
                "LLM API call failed before a structured response was produced.",
            ],
            "escalation_recommendation": "review_by_supervisor",
        }


class LLMWorkerError(Exception):
    """Raised when the LLM API call fails."""
