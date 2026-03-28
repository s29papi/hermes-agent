#!/usr/bin/env python3
"""Shared JSON-backed storage helpers for VAMM built-in tools."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home


def get_vamm_store_dir() -> Path:
    path = get_hermes_home() / "tools" / "vamm"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json_store(filename: str, default: Any) -> Any:
    path = get_vamm_store_dir() / filename
    if not path.exists():
        if isinstance(default, (dict, list)):
            return json.loads(json.dumps(default))
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        if isinstance(default, (dict, list)):
            return json.loads(json.dumps(default))
        return default


def save_json_store(filename: str, payload: Any) -> Path:
    path = get_vamm_store_dir() / filename
    fd, temp_path = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.tmp.")
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        Path(temp_path).replace(path)
    except Exception:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass
        raise
    return path
