#!/usr/bin/env python3
"""
Validate a generated canonical handoff draft for project-handoff-generate.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_SCRIPTS_DIR = SCRIPT_DIR.parents[2] / "scripts"
if str(SHARED_SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SHARED_SCRIPTS_DIR))

from handoff_protocol import ValidationError, validate_canonical_handoff  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a canonical handoff draft.")
    parser.add_argument("handoff_path")
    args = parser.parse_args()

    path = Path(args.handoff_path)
    if not path.exists():
        print(f"[ERROR] file not found: {path}")
        return 1

    try:
        validate_canonical_handoff(path)
    except ValidationError as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] handoff is valid: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
