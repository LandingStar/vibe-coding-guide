"""Tests for Worker registry, LLM Worker, and HTTP Worker (Phase 15)."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.workers.base import WorkerConfig
from src.workers.registry import WorkerRegistry
from src.workers.llm_worker import LLMWorker, LLMWorkerError
from src.workers.http_worker import HTTPWorker, HTTPWorkerError
from src.subagent.stub_worker import StubWorkerBackend


# ── WorkerConfig ────────────────────────────────────────

class TestWorkerConfig:
    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "secret-123")
        cfg = WorkerConfig(worker_type="llm", api_key_env="TEST_API_KEY")
        assert cfg.api_key == "secret-123"

    def test_api_key_missing_env(self):
        cfg = WorkerConfig(worker_type="llm", api_key_env="NONEXISTENT_KEY_XYZ")
        assert cfg.api_key == ""

    def test_api_key_no_env_var(self):
        cfg = WorkerConfig(worker_type="llm")
        assert cfg.api_key == ""

    def test_defaults(self):
        cfg = WorkerConfig(worker_type="stub")
        assert cfg.timeout == 60
        assert cfg.max_retries == 2


# ── WorkerRegistry ──────────────────────────────────────

class TestWorkerRegistry:
    def test_register_and_get(self):
        reg = WorkerRegistry()
        stub = StubWorkerBackend()
        reg.register("stub", stub)
        assert reg.get("stub") is stub

    def test_get_not_found(self):
        reg = WorkerRegistry()
        with pytest.raises(KeyError, match="No worker registered"):
            reg.get("llm")

    def test_list_types(self):
        reg = WorkerRegistry()
        reg.register("stub", StubWorkerBackend())
        reg.register("llm", StubWorkerBackend())
        assert sorted(reg.list_types()) == ["llm", "stub"]

    def test_contains(self):
        reg = WorkerRegistry()
        reg.register("stub", StubWorkerBackend())
        assert "stub" in reg
        assert "llm" not in reg

    def test_overwrite(self):
        reg = WorkerRegistry()
        old = StubWorkerBackend()
        new = StubWorkerBackend()
        reg.register("stub", old)
        reg.register("stub", new)
        assert reg.get("stub") is new


# ── LLM Worker ──────────────────────────────────────────

class TestLLMWorkerPrompt:
    def test_build_prompt_includes_task(self):
        contract = {
            "contract_id": "c-1",
            "task": "Fix the database query.",
            "scope": "Only modify db.py.",
            "required_refs": ["docs/README.md"],
            "acceptance": ["Query returns correct results."],
            "out_of_scope": ["Do not modify tests."],
        }
        prompt = LLMWorker._build_prompt(contract)
        assert "Fix the database query." in prompt
        assert "Only modify db.py." in prompt
        assert "docs/README.md" in prompt
        assert "Query returns correct results." in prompt
        assert "Do not modify tests." in prompt

    def test_build_prompt_minimal(self):
        contract = {"contract_id": "c-2"}
        prompt = LLMWorker._build_prompt(contract)
        assert "No task specified." in prompt


class TestLLMWorkerResponse:
    def test_build_report(self):
        report = LLMWorker._build_report("c-1", "Here is the fix...")
        assert report["contract_id"] == "c-1"
        assert report["status"] == "completed"
        assert "llm_response" in report
        assert report["llm_response"] == "Here is the fix..."

    def test_error_report(self):
        report = LLMWorker._error_report("c-1", "Timeout")
        assert report["status"] == "failed"
        assert report["escalation_recommendation"] == "escalate_to_supervisor"

    def test_extract_content_valid(self):
        data = {
            "choices": [
                {"message": {"content": "Hello from LLM"}}
            ]
        }
        assert LLMWorker._extract_content(data) == "Hello from LLM"

    def test_extract_content_invalid(self):
        with pytest.raises(LLMWorkerError, match="Unexpected API response"):
            LLMWorker._extract_content({"choices": []})


class TestLLMWorkerExecution:
    def test_requires_base_url(self):
        cfg = WorkerConfig(worker_type="llm")
        with pytest.raises(ValueError):
            LLMWorker(cfg)

    def test_execute_no_api_key(self, monkeypatch):
        monkeypatch.delenv("TEST_LLM_KEY", raising=False)
        cfg = WorkerConfig(
            worker_type="llm",
            base_url="https://example.com/v1",
            api_key_env="TEST_LLM_KEY",
        )
        worker = LLMWorker(cfg)
        report = worker.execute({"contract_id": "c-1", "task": "test"})
        assert report["status"] == "failed"
        assert "API key not found" in report["verification_results"][0]

    def test_execute_with_mock_api(self, monkeypatch):
        monkeypatch.setenv("TEST_LLM_KEY", "fake-key-xxx")
        cfg = WorkerConfig(
            worker_type="llm",
            base_url="https://example.com/v1",
            api_key_env="TEST_LLM_KEY",
            model="test-model",
        )
        worker = LLMWorker(cfg)

        mock_response = json.dumps({
            "choices": [{"message": {"content": "Task completed successfully."}}]
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            report = worker.execute({
                "contract_id": "c-1",
                "task": "Fix the bug.",
                "scope": "Only edit utils.py",
            })

        assert report["status"] == "completed"
        assert report["contract_id"] == "c-1"
        assert "Task completed successfully." in report["llm_response"]

    def test_execute_http_error_4xx(self, monkeypatch):
        monkeypatch.setenv("TEST_LLM_KEY", "fake-key")
        cfg = WorkerConfig(
            worker_type="llm",
            base_url="https://example.com/v1",
            api_key_env="TEST_LLM_KEY",
            max_retries=0,
        )
        worker = LLMWorker(cfg)

        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
            "https://example.com", 401, "Unauthorized", {}, None,
        )):
            report = worker.execute({"contract_id": "c-2", "task": "test"})

        assert report["status"] == "failed"
        assert "401" in report["verification_results"][0]


# ── HTTP Worker ─────────────────────────────────────────

class TestHTTPWorker:
    def test_requires_base_url(self):
        cfg = WorkerConfig(worker_type="http")
        with pytest.raises(ValueError):
            HTTPWorker(cfg)

    def test_execute_with_mock(self, monkeypatch):
        monkeypatch.setenv("TEST_HTTP_KEY", "key-abc")
        cfg = WorkerConfig(
            worker_type="http",
            base_url="https://worker-api.example.com/execute",
            api_key_env="TEST_HTTP_KEY",
        )
        worker = HTTPWorker(cfg)

        mock_report = json.dumps({
            "report_id": "r-ext-1",
            "contract_id": "c-ext-1",
            "status": "completed",
            "changed_artifacts": ["file.py"],
            "verification_results": ["All tests pass."],
            "escalation_recommendation": "none",
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_report
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            report = worker.execute({"contract_id": "c-ext-1", "task": "do work"})

        assert report["status"] == "completed"
        assert report["report_id"] == "r-ext-1"
        assert "All tests pass." in report["verification_results"]

    def test_execute_fills_missing_fields(self, monkeypatch):
        cfg = WorkerConfig(
            worker_type="http",
            base_url="https://api.example.com/work",
        )
        worker = HTTPWorker(cfg)

        # Response missing required fields
        mock_report = json.dumps({"result": "ok"}).encode("utf-8")
        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_report
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            report = worker.execute({"contract_id": "c-x"})

        # Should have auto-filled fields
        assert "report_id" in report
        assert report["contract_id"] == "c-x"
        assert report["status"] == "completed"

    def test_execute_connection_error(self, monkeypatch):
        cfg = WorkerConfig(
            worker_type="http",
            base_url="https://unreachable.example.com/",
            max_retries=0,
        )
        worker = HTTPWorker(cfg)

        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
            report = worker.execute({"contract_id": "c-fail"})

        assert report["status"] == "failed"
        assert "Connection refused" in report["verification_results"][0]


# ── Integration: Worker in PEP pipeline ─────────────────

class TestWorkerPipelineIntegration:
    def test_registry_with_executor(self):
        """Registry can supply worker to executor pipeline."""
        reg = WorkerRegistry()
        stub = StubWorkerBackend()
        reg.register("stub", stub)

        from src.subagent import contract_factory, report_validator
        from src.pep.executor import Executor

        exe = Executor(
            dry_run=True,
            worker=reg.get("stub"),
            contract_factory=contract_factory,
            report_validator=report_validator,
        )
        from src.pdp.decision_envelope import build_envelope
        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        assert result["review_state"] == "applied"


# ── Live LLM test (skip if no key) ─────────────────────

@pytest.mark.skipif(
    not os.environ.get("DASHSCOPE_API_KEY"),
    reason="DASHSCOPE_API_KEY not set — skipping live LLM test",
)
class TestLLMWorkerLive:
    def test_live_llm_call(self):
        cfg = WorkerConfig(
            worker_type="llm",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            api_key_env="DASHSCOPE_API_KEY",
            timeout=30,
        )
        worker = LLMWorker(cfg)
        report = worker.execute({
            "contract_id": "live-test-1",
            "task": "Return exactly the text: HELLO_TEST_OK",
            "scope": "Test only",
            "acceptance": ["Response contains HELLO_TEST_OK"],
        })
        assert report["status"] == "completed"
        assert "HELLO_TEST_OK" in report.get("llm_response", "")
