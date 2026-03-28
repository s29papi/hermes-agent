#!/usr/bin/env python3
"""Tool-owned VAMM configuration.

This keeps VAMM session/theme state outside Hermes' global CLI config so the
tool can evolve independently and other tools can follow the same pattern.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from hermes_constants import get_hermes_home


DEFAULT_VAMM_CONFIG: dict[str, Any] = {
    "agent_mode": "hermes",
    "theme": {
        "banner_colors": ["#2563EB", "#FFFFFF", "#2563EB"],
        "ui_colors": {
            "banner_border": "#2563EB",
            "banner_title": "#60A5FA",
            "banner_accent": "#3B82F6",
            "banner_dim": "#1D4ED8",
            "banner_text": "#EAF4FF",
            "prompt": "#EAF4FF",
            "input_rule": "#2563EB",
            "response_border": "#60A5FA",
            "session_label": "#60A5FA",
            "session_border": "#93C5FD",
        },
        "hero_text": "",
        "hero_file": "",
    },
    "execution": {
        "settlement_strategy": "coingecko",
        "network": "testnet",
        "prover_mode": "remote",
        "prover_url": "https://api.provable.com/prove/testnet",
        "settlement_route": "public-usdcx-to-private-maker / private-aleo-to-private-requester",
    },
}


def get_vamm_config_dir() -> Path:
    path = get_hermes_home() / "tools"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_vamm_config_path() -> Path:
    return get_vamm_config_dir() / "vamm.yaml"


def load_vamm_config() -> dict[str, Any]:
    path = get_vamm_config_path()
    if not path.exists():
        migrated = _migrate_legacy_vamm_config()
        if migrated is not None:
            return migrated
        return {
            "agent_mode": DEFAULT_VAMM_CONFIG["agent_mode"],
            "theme": {
                "banner_colors": list(DEFAULT_VAMM_CONFIG["theme"]["banner_colors"]),
                "ui_colors": dict(DEFAULT_VAMM_CONFIG["theme"]["ui_colors"]),
                "hero_text": DEFAULT_VAMM_CONFIG["theme"]["hero_text"],
                "hero_file": DEFAULT_VAMM_CONFIG["theme"]["hero_file"],
            },
            "execution": dict(DEFAULT_VAMM_CONFIG["execution"]),
        }
    try:
        raw = yaml.safe_load(path.read_text()) or {}
    except Exception:
        raw = {}

    config = {
        "agent_mode": str(raw.get("agent_mode", DEFAULT_VAMM_CONFIG["agent_mode"])).strip().lower() or "hermes",
        "theme": {
            "banner_colors": list(
                (raw.get("theme") or {}).get(
                    "banner_colors",
                    DEFAULT_VAMM_CONFIG["theme"]["banner_colors"],
                )
            ),
            "ui_colors": dict(
                (raw.get("theme") or {}).get(
                    "ui_colors",
                    DEFAULT_VAMM_CONFIG["theme"]["ui_colors"],
                )
            ),
            "hero_text": str(
                (raw.get("theme") or {}).get(
                    "hero_text",
                    DEFAULT_VAMM_CONFIG["theme"]["hero_text"],
                )
            ),
            "hero_file": str(
                (raw.get("theme") or {}).get(
                    "hero_file",
                    DEFAULT_VAMM_CONFIG["theme"]["hero_file"],
                )
            ),
        },
        "execution": dict(
            raw.get("execution", DEFAULT_VAMM_CONFIG["execution"])
            if isinstance(raw.get("execution"), dict)
            else DEFAULT_VAMM_CONFIG["execution"]
        ),
    }
    merged_execution = dict(DEFAULT_VAMM_CONFIG["execution"])
    for key, value in config["execution"].items():
        merged_execution[str(key)] = str(value)
    config["execution"] = merged_execution
    return config


def _migrate_legacy_vamm_config() -> dict[str, Any] | None:
    """Import legacy VAMM state from Hermes global config once, if present."""
    try:
        from hermes_cli.config import load_config

        display = load_config().get("display", {})
        if not isinstance(display, dict):
            return None

        has_legacy_mode = "agent_mode" in display
        has_legacy_theme = isinstance(display.get("vamm_theme"), dict)
        if not has_legacy_mode and not has_legacy_theme:
            return None

        theme = display.get("vamm_theme") if isinstance(display.get("vamm_theme"), dict) else {}
        colors = theme.get("banner_colors", DEFAULT_VAMM_CONFIG["theme"]["banner_colors"])
        if not isinstance(colors, list) or len(colors) < 3:
            colors = DEFAULT_VAMM_CONFIG["theme"]["banner_colors"]

        config = {
            "agent_mode": str(display.get("agent_mode", DEFAULT_VAMM_CONFIG["agent_mode"])).strip().lower() or "hermes",
            "theme": {
                "banner_colors": list(colors[:3]),
                "ui_colors": dict(DEFAULT_VAMM_CONFIG["theme"]["ui_colors"]),
                "hero_text": DEFAULT_VAMM_CONFIG["theme"]["hero_text"],
                "hero_file": DEFAULT_VAMM_CONFIG["theme"]["hero_file"],
            },
            "execution": dict(DEFAULT_VAMM_CONFIG["execution"]),
        }
        save_vamm_config(config)
        return config
    except Exception:
        return None


def save_vamm_config(config: dict[str, Any]) -> None:
    path = get_vamm_config_path()
    path.write_text(yaml.safe_dump(config, sort_keys=False))


def get_vamm_agent_mode() -> str:
    return load_vamm_config().get("agent_mode", "hermes")


def set_vamm_agent_mode(mode: str) -> str:
    config = load_vamm_config()
    config["agent_mode"] = str(mode).strip().lower() or "hermes"
    save_vamm_config(config)
    return config["agent_mode"]


def get_vamm_banner_colors() -> list[str]:
    config = load_vamm_config()
    theme = config.get("theme", {})
    colors = theme.get("banner_colors", DEFAULT_VAMM_CONFIG["theme"]["banner_colors"])
    if not isinstance(colors, list) or len(colors) < 3:
        return list(DEFAULT_VAMM_CONFIG["theme"]["banner_colors"])
    return list(colors[:3])


def set_vamm_banner_colors(colors: list[str]) -> list[str]:
    config = load_vamm_config()
    theme = config.get("theme")
    if not isinstance(theme, dict):
        theme = {}
        config["theme"] = theme
    theme["banner_colors"] = list(colors[:3])
    save_vamm_config(config)
    return list(theme["banner_colors"])


def get_vamm_ui_colors() -> dict[str, str]:
    config = load_vamm_config()
    theme = config.get("theme", {})
    colors = theme.get("ui_colors", DEFAULT_VAMM_CONFIG["theme"]["ui_colors"])
    if not isinstance(colors, dict):
        return dict(DEFAULT_VAMM_CONFIG["theme"]["ui_colors"])
    merged = dict(DEFAULT_VAMM_CONFIG["theme"]["ui_colors"])
    for key, value in colors.items():
        merged[str(key)] = str(value)
    return merged


def set_vamm_ui_colors(colors: dict[str, str]) -> dict[str, str]:
    config = load_vamm_config()
    theme = config.get("theme")
    if not isinstance(theme, dict):
        theme = {}
        config["theme"] = theme
    merged = dict(DEFAULT_VAMM_CONFIG["theme"]["ui_colors"])
    for key, value in (colors or {}).items():
        merged[str(key)] = str(value)
    theme["ui_colors"] = merged
    save_vamm_config(config)
    return dict(theme["ui_colors"])


def get_vamm_hero_text() -> str:
    config = load_vamm_config()
    theme = config.get("theme", {})
    return str(theme.get("hero_text", DEFAULT_VAMM_CONFIG["theme"]["hero_text"]))


def set_vamm_hero_text(text: str) -> str:
    config = load_vamm_config()
    theme = config.get("theme")
    if not isinstance(theme, dict):
        theme = {}
        config["theme"] = theme
    theme.pop("logo_text", None)
    theme["hero_text"] = str(text)
    save_vamm_config(config)
    return str(theme["hero_text"])


def get_vamm_hero_file() -> str:
    config = load_vamm_config()
    theme = config.get("theme", {})
    return str(theme.get("hero_file", DEFAULT_VAMM_CONFIG["theme"]["hero_file"]))


def set_vamm_hero_file(path: str) -> str:
    config = load_vamm_config()
    theme = config.get("theme")
    if not isinstance(theme, dict):
        theme = {}
        config["theme"] = theme
    theme["hero_file"] = str(path)
    save_vamm_config(config)
    return str(theme["hero_file"])


def get_vamm_execution_config() -> dict[str, str]:
    config = load_vamm_config()
    execution = config.get("execution", DEFAULT_VAMM_CONFIG["execution"])
    if not isinstance(execution, dict):
        return dict(DEFAULT_VAMM_CONFIG["execution"])
    merged = dict(DEFAULT_VAMM_CONFIG["execution"])
    for key, value in execution.items():
        merged[str(key)] = str(value)
    return merged


def set_vamm_execution_config(values: dict[str, Any]) -> dict[str, str]:
    config = load_vamm_config()
    execution = config.get("execution")
    if not isinstance(execution, dict):
        execution = {}
        config["execution"] = execution
    merged = dict(DEFAULT_VAMM_CONFIG["execution"])
    for key, value in execution.items():
        merged[str(key)] = str(value)
    for key, value in (values or {}).items():
        if value is None:
            continue
        merged[str(key)] = str(value)
    config["execution"] = merged
    save_vamm_config(config)
    return dict(merged)
