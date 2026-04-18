"""Check backed by a plain Python callable."""

from __future__ import annotations

from typing import Callable

from .base import CheckResult


class ScriptCheck:
    """Wrap a Python function as a Check.

    The function signature must be ``(context: dict) -> dict`` and return
    ``{"passed": bool, "message": str}``.
    """

    def __init__(self, func: Callable[[dict], dict]) -> None:
        self._func = func

    def check(self, context: dict) -> CheckResult:
        raw = self._func(context)
        passed = bool(raw.get("passed", False))
        message = str(raw.get("message", ""))
        return CheckResult(passed=passed, message=message)