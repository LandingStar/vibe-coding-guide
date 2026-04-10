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

        try:
            response_text = self._call_llm(prompt)
        except LLMWorkerError as exc:
            return self._error_report(contract_id, str(exc))

        return self._build_report(contract_id, response_text)

    # ── Prompt construction ─────────────────────────────

    @staticmethod
    def _build_prompt(contract: dict) -> str:
        """Translate contract fields into a structured LLM prompt."""
        task = contract.get("task", "No task specified.")
        scope = contract.get("scope", "")
        refs = contract.get("required_refs", [])
        acceptance = contract.get("acceptance", [])
        out_of_scope = contract.get("out_of_scope", [])

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
            "Provide a clear, concise response that fulfills the task. "
            "List any artifacts you would change and verification steps taken."
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
    def _build_report(contract_id: str, response_text: str) -> dict:
        """Wrap LLM response into a subagent report."""
        return {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "contract_id": contract_id,
            "status": "completed",
            "changed_artifacts": [],
            "verification_results": [
                "LLM worker completed task.",
                f"Response length: {len(response_text)} characters.",
            ],
            "llm_response": response_text,
            "escalation_recommendation": "none",
        }

    @staticmethod
    def _error_report(contract_id: str, error_msg: str) -> dict:
        """Build a failure report when the LLM call fails."""
        return {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "contract_id": contract_id,
            "status": "failed",
            "changed_artifacts": [],
            "verification_results": [
                f"LLM worker error: {error_msg}",
            ],
            "escalation_recommendation": "escalate_to_supervisor",
        }


class LLMWorkerError(Exception):
    """Raised when the LLM API call fails."""
