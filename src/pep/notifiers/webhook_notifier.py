"""Webhook notifier — sends notifications via HTTP POST.

Uses only ``urllib.request`` (stdlib) to avoid external dependencies.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error


class WebhookNotifier:
    """EscalationNotifier that POSTs notification JSON to a URL."""

    def __init__(
        self,
        *,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> None:
        self._url = url
        self._headers = headers or {}
        self._timeout = timeout

    def notify(self, notification: dict) -> dict:
        body = json.dumps(notification, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=body,
            headers={
                "Content-Type": "application/json",
                **self._headers,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return {
                    "delivered": True,
                    "channel": "webhook",
                    "status_code": resp.status,
                }
        except urllib.error.URLError as exc:
            return {
                "delivered": False,
                "channel": "webhook",
                "error": str(exc),
            }
