"""Worker registry — register and retrieve worker backends by type."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces import WorkerBackend


class WorkerRegistry:
    """Registry mapping worker_type strings to WorkerBackend instances.

    Example::

        registry = WorkerRegistry()
        registry.register("llm", llm_worker)
        registry.register("http", http_worker)

        worker = registry.get("llm")
        report = worker.execute(contract)
    """

    def __init__(self) -> None:
        self._workers: dict[str, WorkerBackend] = {}

    def register(self, worker_type: str, worker: WorkerBackend) -> None:
        """Register a worker backend under the given type name."""
        self._workers[worker_type] = worker

    def get(self, worker_type: str) -> WorkerBackend:
        """Retrieve a registered worker by type.

        Raises ``KeyError`` if the type is not registered.
        """
        if worker_type not in self._workers:
            raise KeyError(
                f"No worker registered for type '{worker_type}'. "
                f"Available: {list(self._workers.keys())}"
            )
        return self._workers[worker_type]

    def list_types(self) -> list[str]:
        """Return all registered worker type names."""
        return list(self._workers.keys())

    def __contains__(self, worker_type: str) -> bool:
        return worker_type in self._workers
