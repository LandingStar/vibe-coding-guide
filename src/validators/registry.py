"""Registry for validators, checks, and triggers."""

from __future__ import annotations

from .base import Check, Trigger, Validator


class ValidatorRegistry:
    """Named registry for Validator, Check, and Trigger instances."""

    def __init__(self) -> None:
        self._validators: dict[str, Validator] = {}
        self._checks: dict[str, Check] = {}
        self._triggers: dict[str, Trigger] = {}

    # -- validators --

    def register_validator(self, name: str, validator: Validator) -> None:
        self._validators[name] = validator

    def get_validator(self, name: str) -> Validator | None:
        return self._validators.get(name)

    def list_validators(self) -> list[str]:
        return list(self._validators)

    # -- checks --

    def register_check(self, name: str, check: Check) -> None:
        self._checks[name] = check

    def get_check(self, name: str) -> Check | None:
        return self._checks.get(name)

    def list_checks(self) -> list[str]:
        return list(self._checks)

    # -- triggers --

    def register_trigger(self, name: str, trigger: Trigger) -> None:
        self._triggers[name] = trigger

    def get_trigger(self, name: str) -> Trigger | None:
        return self._triggers.get(name)

    def list_triggers(self) -> list[str]:
        return list(self._triggers)
