"""User-global configuration: ``~/.doc-based-coding/config.json``.

This module defines the :class:`UserConfig` dataclass and a loader that
reads it from the user home directory.  Missing or invalid files are
silently ignored so the platform degrades gracefully.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Fields recognised in config.json.  Unknown keys are silently ignored
# for forward-compatibility.
_KNOWN_FIELDS = frozenset({"extra_pack_dirs", "default_model", "default_llm_params"})


@dataclass(frozen=True)
class UserConfig:
    """Typed, immutable representation of the user-global config file."""

    extra_pack_dirs: tuple[str, ...] = ()
    """Additional directories to scan for packs (appended to discovery)."""

    default_model: str | None = None
    """Default LLM model identifier applied when no project-level override."""

    default_llm_params: dict[str, Any] = field(default_factory=dict)
    """Default LLM parameters (temperature, max_tokens, etc.)."""

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict for ``Pipeline.info()``."""
        return {
            "extra_pack_dirs": list(self.extra_pack_dirs),
            "default_model": self.default_model,
            "default_llm_params": dict(self.default_llm_params),
        }


_EMPTY = UserConfig()


def load_user_config(user_dir: Path | None) -> UserConfig:
    """Read ``config.json`` from *user_dir* and return a :class:`UserConfig`.

    Returns the empty default when:
    - *user_dir* is ``None`` or does not exist
    - ``config.json`` is missing
    - the file contains invalid JSON
    """
    if user_dir is None or not user_dir.is_dir():
        return _EMPTY

    config_path = user_dir / "config.json"
    if not config_path.is_file():
        return _EMPTY

    try:
        raw: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Ignoring invalid user config %s: %s", config_path, exc)
        return _EMPTY

    if not isinstance(raw, dict):
        logger.warning("Ignoring user config %s: expected JSON object", config_path)
        return _EMPTY

    extra = raw.get("extra_pack_dirs")
    if extra is not None and not isinstance(extra, list):
        logger.warning("Ignoring extra_pack_dirs: expected list")
        extra = None

    model = raw.get("default_model")
    if model is not None and not isinstance(model, str):
        logger.warning("Ignoring default_model: expected string")
        model = None

    params = raw.get("default_llm_params")
    if params is not None and not isinstance(params, dict):
        logger.warning("Ignoring default_llm_params: expected object")
        params = None

    return UserConfig(
        extra_pack_dirs=tuple(str(p) for p in extra) if extra else (),
        default_model=model,
        default_llm_params=dict(params) if params else {},
    )


def save_user_config(
    user_dir: Path | None,
    field: str,
    value: Any,
) -> dict[str, Any]:
    """Update a single *field* in ``config.json`` and return the full config.

    Creates the user directory and config file if they do not exist.
    Only fields in :data:`_KNOWN_FIELDS` are accepted.

    Raises :class:`ValueError` for unknown field names.
    """
    if field not in _KNOWN_FIELDS:
        raise ValueError(
            f"Unknown config field '{field}'. "
            f"Accepted: {', '.join(sorted(_KNOWN_FIELDS))}"
        )

    if user_dir is None:
        user_dir = Path.home() / ".doc-based-coding"

    user_dir.mkdir(parents=True, exist_ok=True)
    config_path = user_dir / "config.json"

    # Load existing content
    raw: dict[str, Any] = {}
    if config_path.is_file():
        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raw = {}
        except (json.JSONDecodeError, OSError):
            raw = {}

    raw[field] = value

    config_path.write_text(
        json.dumps(raw, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    logger.info("Updated user config field '%s' in %s", field, config_path)

    # Return the loaded config as dict for confirmation
    return load_user_config(user_dir).to_dict()
