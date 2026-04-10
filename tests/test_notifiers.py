"""Tests for notification adapters (Phase 13 Slice A)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pep.notifiers.console_notifier import ConsoleNotifier
from src.pep.notifiers.file_notifier import FileNotifier
from src.pep.notifiers.webhook_notifier import WebhookNotifier


SAMPLE_NOTIFICATION = {
    "notification_id": "notif-001",
    "target": "human_reviewer",
    "reason": "High impact decision",
    "envelope_id": "env-001",
}


# ── ConsoleNotifier ────────────────────────────────────

class TestConsoleNotifier:
    def test_returns_delivered(self):
        notifier = ConsoleNotifier(stream=io.StringIO())
        result = notifier.notify(SAMPLE_NOTIFICATION)
        assert result["delivered"] is True
        assert result["channel"] == "console"

    def test_writes_to_stream(self):
        buf = io.StringIO()
        notifier = ConsoleNotifier(stream=buf)
        notifier.notify(SAMPLE_NOTIFICATION)
        output = buf.getvalue()
        assert "[NOTIFICATION]" in output
        assert "notif-001" in output

    def test_protocol_compatible(self):
        """ConsoleNotifier satisfies EscalationNotifier protocol."""
        notifier = ConsoleNotifier(stream=io.StringIO())
        assert hasattr(notifier, "notify")
        result = notifier.notify(SAMPLE_NOTIFICATION)
        assert "delivered" in result
        assert "channel" in result


# ── FileNotifier ───────────────────────────────────────

class TestFileNotifier:
    def test_writes_json_file(self, tmp_path):
        notifier = FileNotifier(output_dir=tmp_path)
        result = notifier.notify(SAMPLE_NOTIFICATION)
        assert result["delivered"] is True
        assert result["channel"] == "file"
        target = tmp_path / "notif-001.json"
        assert target.exists()
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["notification_id"] == "notif-001"

    def test_creates_output_dir(self, tmp_path):
        out_dir = tmp_path / "notifications"
        notifier = FileNotifier(output_dir=out_dir)
        notifier.notify(SAMPLE_NOTIFICATION)
        assert out_dir.exists()

    def test_returns_path(self, tmp_path):
        notifier = FileNotifier(output_dir=tmp_path)
        result = notifier.notify(SAMPLE_NOTIFICATION)
        assert "path" in result
        assert "notif-001.json" in result["path"]

    def test_protocol_compatible(self, tmp_path):
        notifier = FileNotifier(output_dir=tmp_path)
        result = notifier.notify(SAMPLE_NOTIFICATION)
        assert "delivered" in result
        assert "channel" in result


# ── WebhookNotifier ────────────────────────────────────

class TestWebhookNotifier:
    def test_successful_post(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("src.pep.notifiers.webhook_notifier.urllib.request.urlopen", return_value=mock_resp):
            notifier = WebhookNotifier(url="https://example.com/hook")
            result = notifier.notify(SAMPLE_NOTIFICATION)
            assert result["delivered"] is True
            assert result["channel"] == "webhook"
            assert result["status_code"] == 200

    def test_failed_post_returns_error(self):
        import urllib.error
        with patch(
            "src.pep.notifiers.webhook_notifier.urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            notifier = WebhookNotifier(url="https://example.com/hook")
            result = notifier.notify(SAMPLE_NOTIFICATION)
            assert result["delivered"] is False
            assert "error" in result

    def test_custom_headers(self):
        mock_resp = MagicMock()
        mock_resp.status = 201
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("src.pep.notifiers.webhook_notifier.urllib.request.urlopen", return_value=mock_resp) as mock_open:
            notifier = WebhookNotifier(
                url="https://example.com/hook",
                headers={"Authorization": "Bearer test-token"},
            )
            notifier.notify(SAMPLE_NOTIFICATION)
            req = mock_open.call_args[0][0]
            assert req.get_header("Authorization") == "Bearer test-token"
            assert req.get_header("Content-type") == "application/json"

    def test_protocol_compatible(self):
        notifier = WebhookNotifier(url="https://example.com/hook")
        assert hasattr(notifier, "notify")
