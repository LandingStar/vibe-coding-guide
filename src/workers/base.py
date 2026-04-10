"""Worker configuration and base types."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class WorkerConfig:
    """Configuration for a worker backend.

    API keys are resolved from environment variables.  Never hardcode
    secrets in source.
    """

    worker_type: str                  # "llm" | "http" | "stub"
    base_url: str = ""                # API endpoint URL
    model: str = ""                   # model identifier (e.g. "qwen-plus")
    api_key_env: str = ""             # env var name holding the API key
    timeout: int = 60                 # request timeout in seconds
    max_retries: int = 2              # retry count on transient errors
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def api_key(self) -> str:
        """Read the API key from the environment variable.

        Returns empty string if the env var is not set.
        Never stores the key in the config object itself.
        """
        if not self.api_key_env:
            return ""
        return os.environ.get(self.api_key_env, "")
