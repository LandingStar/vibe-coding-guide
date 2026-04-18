"""AdapterRegistry — unified registration and lookup for all adapter types."""

from __future__ import annotations

from typing import Any

from .descriptor import AdapterDescriptor


class AdapterRegistry:
    """Unified registry for Workers, Notifiers, and Registrars.

    Each adapter is registered with an ``AdapterDescriptor`` and the
    actual adapter instance.  Lookup is available by name or category.

    Example::

        registry = AdapterRegistry()
        registry.register(
            AdapterDescriptor("llm", "worker", "WorkerBackend", ["execute"]),
            llm_worker_instance,
        )
        registry.register(
            AdapterDescriptor("console", "notifier", "EscalationNotifier", ["notify"]),
            console_notifier_instance,
        )

        worker = registry.get("llm")
        all_notifiers = registry.list_by_category("notifier")
    """

    def __init__(self) -> None:
        self._descriptors: dict[str, AdapterDescriptor] = {}
        self._instances: dict[str, Any] = {}

    def register(self, descriptor: AdapterDescriptor, instance: Any) -> None:
        """Register an adapter with its descriptor and instance.

        Raises ``ValueError`` if an adapter with the same name is
        already registered.
        """
        if descriptor.name in self._descriptors:
            raise ValueError(
                f"Adapter '{descriptor.name}' is already registered"
            )
        self._descriptors[descriptor.name] = descriptor
        self._instances[descriptor.name] = instance

    def get(self, name: str) -> Any:
        """Retrieve an adapter instance by name.

        Raises ``KeyError`` if the name is not registered.
        """
        if name not in self._instances:
            raise KeyError(
                f"No adapter registered with name '{name}'. "
                f"Available: {list(self._descriptors.keys())}"
            )
        return self._instances[name]

    def get_descriptor(self, name: str) -> AdapterDescriptor:
        """Retrieve an adapter's descriptor by name.

        Raises ``KeyError`` if the name is not registered.
        """
        if name not in self._descriptors:
            raise KeyError(
                f"No adapter registered with name '{name}'. "
                f"Available: {list(self._descriptors.keys())}"
            )
        return self._descriptors[name]

    def list_all(self) -> list[AdapterDescriptor]:
        """Return descriptors for all registered adapters."""
        return list(self._descriptors.values())

    def list_by_category(self, category: str) -> list[AdapterDescriptor]:
        """Return descriptors for adapters in a specific category."""
        return [d for d in self._descriptors.values() if d.category == category]

    def list_names(self) -> list[str]:
        """Return all registered adapter names."""
        return list(self._descriptors.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._descriptors

    def __len__(self) -> int:
        return len(self._descriptors)
