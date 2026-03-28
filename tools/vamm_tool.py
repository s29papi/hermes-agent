#!/usr/bin/env python3
"""
Minimal VAMM tool for Hermes.

This first version only toggles Hermes CLI branding between Hermes mode and
VAMM mode. It is intentionally narrow so later VAMM wallet/quote/settlement
actions can be added without changing the integration surface.
"""

import json
import re

from tools.vamm_config import (
    get_vamm_agent_mode,
    get_vamm_banner_colors,
    get_vamm_hero_text,
    get_vamm_ui_colors,
    set_vamm_agent_mode,
    set_vamm_banner_colors,
    set_vamm_hero_text,
    set_vamm_ui_colors,
)


_ACTIONS = {
    "enter_vamm": "vamm",
    "switch_to_vamm": "vamm",
    "enter": "vamm",
    "vamm": "vamm",
    "exit_vamm": "hermes",
    "switch_to_hermes": "hermes",
    "exit": "hermes",
    "hermes": "hermes",
}

_HEX_COLOR_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")
_DEFAULT_BANNER_COLORS = ["#2563EB", "#FFFFFF", "#2563EB"]


def _read_agent_mode() -> str:
    return get_vamm_agent_mode()


def _write_agent_mode(mode: str) -> str:
    return set_vamm_agent_mode(mode)


def _read_vamm_theme() -> dict:
    colors = get_vamm_banner_colors()
    ui_colors = get_vamm_ui_colors()
    hero_text = get_vamm_hero_text()
    normalized = []
    for color in colors:
        token = str(color).strip().upper()
        if not token.startswith("#"):
            token = f"#{token}"
        normalized.append(token)
    return {"banner_colors": normalized, "ui_colors": dict(ui_colors), "hero_text": hero_text}


def _write_vamm_banner_colors(colors: list[str]) -> list[str]:
    return set_vamm_banner_colors(colors)


def _write_vamm_hero_text(text: str) -> str:
    return set_vamm_hero_text(text)


def _write_vamm_ui_colors(colors: dict[str, str]) -> dict[str, str]:
    return set_vamm_ui_colors(colors)


def _normalize_banner_colors(colors) -> list[str]:
    if not isinstance(colors, list) or len(colors) < 3:
        raise ValueError("banner_colors must be a list of exactly 3 hex colors")
    normalized = []
    for raw in colors[:3]:
        token = str(raw).strip()
        if not _HEX_COLOR_RE.fullmatch(token):
            raise ValueError(f"Invalid hex color: {raw}")
        if not token.startswith("#"):
            token = f"#{token}"
        normalized.append(token.upper())
    return normalized


def vamm_tool(action: str = "status", banner_colors=None, hero_text=None) -> str:
    normalized = str(action or "status").strip().lower()

    if normalized == "status":
        mode = _read_agent_mode()
        theme = _read_vamm_theme()
        return json.dumps({
            "ok": True,
            "tool": "vamm",
            "action": "status",
            "agent_mode": mode,
            "changed": False,
            "banner_title": "VAMM Agent" if mode == "vamm" else "Hermes Agent",
            "banner_colors": theme["banner_colors"],
            "ui_colors": theme["ui_colors"],
            "hero_text": theme["hero_text"],
        }, ensure_ascii=False)

    if normalized == "set_banner_colors":
        try:
            colors = _normalize_banner_colors(banner_colors)
        except ValueError as exc:
            return json.dumps({
                "ok": False,
                "error": str(exc),
                "expected": list(_DEFAULT_BANNER_COLORS),
            }, ensure_ascii=False)
        updated = _write_vamm_banner_colors(colors)
        return json.dumps({
            "ok": True,
            "tool": "vamm",
            "action": normalized,
            "changed": True,
            "banner_colors": updated,
            "message": f"Updated VAMM banner colors to {', '.join(updated)}.",
        }, ensure_ascii=False)

    if normalized == "set_hero_text":
        updated = _write_vamm_hero_text("" if hero_text is None else str(hero_text))
        return json.dumps({
            "ok": True,
            "tool": "vamm",
            "action": normalized,
            "changed": True,
            "hero_text": updated,
            "message": f"Updated VAMM hero text to {updated!r}.",
        }, ensure_ascii=False)

    if normalized == "set_blue_theme":
        updated = _write_vamm_ui_colors({
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
        })
        return json.dumps({
            "ok": True,
            "tool": "vamm",
            "action": normalized,
            "changed": True,
            "ui_colors": updated,
            "message": "Updated VAMM UI colors to the blue palette.",
        }, ensure_ascii=False)

    mode = _ACTIONS.get(normalized)
    if mode is None:
        return json.dumps({
            "ok": False,
            "error": f"Unsupported action: {action}",
            "supported_actions": sorted(set(_ACTIONS.keys()) | {"status", "set_banner_colors", "set_hero_text", "set_blue_theme"}),
        }, ensure_ascii=False)

    current_mode = _read_agent_mode()
    changed = current_mode != mode
    updated_mode = _write_agent_mode(mode) if changed else current_mode
    return json.dumps({
        "ok": True,
        "tool": "vamm",
        "action": normalized,
        "agent_mode": updated_mode,
        "changed": changed,
        "banner_title": "VAMM Agent" if updated_mode == "vamm" else "Hermes Agent",
        "message": (
            "VAMM session mode enabled. Hermes CLI branding now uses VAMM Agent."
            if changed and updated_mode == "vamm"
            else "Returned to Hermes session mode."
            if changed
            else "Already in VAMM mode."
            if updated_mode == "vamm"
            else "Already in Hermes mode."
        ),
    }, ensure_ascii=False)


def check_vamm_requirements() -> bool:
    return True


VAMM_SCHEMA = {
    "name": "vamm",
    "description": (
        "Switch the current Hermes session branding between Hermes mode and "
        "VAMM mode. Call this immediately when the user asks to switch to "
        "VAMM, enter VAMM mode, enter a VAMM session, return to Hermes, or "
        "check which mode is active. Do not ask a clarifying question for "
        "phrases like 'switch to vamm', 'enter vamm', 'use vamm mode', or "
        "'go back to hermes' because this tool handles those requests "
        "directly."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
            "description": (
                    "One of: status, enter_vamm, switch_to_vamm, enter, vamm, "
                    "exit_vamm, switch_to_hermes, exit, hermes, set_banner_colors, set_hero_text, set_blue_theme."
                ),
            },
            "banner_colors": {
                "type": "array",
                "description": "Three hex colors for the VAMM ASCII banner rows, top to bottom groups.",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3,
            },
            "hero_text": {
                "type": "string",
                "description": "Custom hero text/markup for the VAMM banner. If set, it replaces the left-side hero art inside the panel.",
            },
        },
        "required": ["action"],
    },
}


from tools.registry import registry

registry.register(
    name="vamm",
    toolset="vamm",
    schema=VAMM_SCHEMA,
    handler=lambda args, **kw: vamm_tool(
        args.get("action", "status"),
        banner_colors=args.get("banner_colors"),
        hero_text=args.get("hero_text"),
    ),
    check_fn=check_vamm_requirements,
    emoji="◈",
)
