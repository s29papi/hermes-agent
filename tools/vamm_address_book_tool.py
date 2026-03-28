#!/usr/bin/env python3
"""VAMM address book tool.

Stores mappings from names/Telegram handles to Aleo addresses in a JSON KV
store and returns markdown tables for read/list operations so chat can render
them cleanly.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from tools.registry import registry
from tools.vamm_store import load_json_store, save_json_store


STORE_FILE = "address_book.json"


def check_vamm_address_book_requirements() -> bool:
    return True


def _load_entries() -> Dict[str, str]:
    raw = load_json_store(STORE_FILE, {})
    if not isinstance(raw, dict):
        return {}
    cleaned: Dict[str, str] = {}
    for key, value in raw.items():
        k = str(key).strip()
        v = str(value).strip()
        if k and v:
            cleaned[k] = v
    return cleaned


def _save_entries(entries: Dict[str, str]) -> None:
    save_json_store(STORE_FILE, entries)


def _markdown_table(entries: Dict[str, str]) -> str:
    if not entries:
        return "| Name | Aleo Address |\n| --- | --- |\n| (empty) | - |"
    lines = ["| Name | Aleo Address |", "| --- | --- |"]
    for name in sorted(entries.keys(), key=str.lower):
        lines.append(f"| {name} | {entries[name]} |")
    return "\n".join(lines)


def vamm_address_book_tool(action: str = "list", name: str | None = None, address: str | None = None) -> str:
    action = str(action or "list").strip().lower()
    entries = _load_entries()

    if action in {"list", "read"}:
        return json.dumps({
            "ok": True,
            "tool": "vamm_address_book",
            "action": action,
            "count": len(entries),
            "entries": entries,
            "table_markdown": _markdown_table(entries),
        }, ensure_ascii=False)

    if action in {"add", "upsert", "set"}:
        key = str(name or "").strip()
        value = str(address or "").strip()
        if not key or not value:
            return json.dumps({
                "ok": False,
                "error": "Both 'name' and 'address' are required for add/upsert.",
            }, ensure_ascii=False)
        entries[key] = value
        _save_entries(entries)
        return json.dumps({
            "ok": True,
            "tool": "vamm_address_book",
            "action": action,
            "changed": True,
            "entry": {"name": key, "address": value},
            "count": len(entries),
            "table_markdown": _markdown_table(entries),
        }, ensure_ascii=False)

    if action in {"remove", "delete"}:
        key = str(name or "").strip()
        if not key:
            return json.dumps({"ok": False, "error": "'name' is required for remove/delete."}, ensure_ascii=False)
        if key not in entries:
            return json.dumps({"ok": False, "error": f"No address-book entry found for '{key}'."}, ensure_ascii=False)
        removed = entries.pop(key)
        _save_entries(entries)
        return json.dumps({
            "ok": True,
            "tool": "vamm_address_book",
            "action": action,
            "changed": True,
            "removed": {"name": key, "address": removed},
            "count": len(entries),
            "table_markdown": _markdown_table(entries),
        }, ensure_ascii=False)

    if action in {"get", "lookup"}:
        key = str(name or "").strip()
        if not key:
            return json.dumps({"ok": False, "error": "'name' is required for get/lookup."}, ensure_ascii=False)
        matches = {k: v for k, v in entries.items() if key.lower() in k.lower()}
        return json.dumps({
            "ok": True,
            "tool": "vamm_address_book",
            "action": action,
            "query": key,
            "count": len(matches),
            "entries": matches,
            "table_markdown": _markdown_table(matches),
        }, ensure_ascii=False)

    return json.dumps({
        "ok": False,
        "error": f"Unsupported action: {action}",
        "supported_actions": ["list", "read", "add", "upsert", "set", "remove", "delete", "get", "lookup"],
    }, ensure_ascii=False)


VAMM_ADDRESS_BOOK_SCHEMA = {
    "name": "vamm_address_book",
    "description": (
        "Manage the VAMM address book. Stores mappings from Telegram handles or "
        "normal names to Aleo addresses in JSON-backed storage. For list/read/get "
        "results, use the returned markdown table to present results cleanly in chat. "
        "Use this tool when the user asks to show, list, view, add, update, delete, "
        "look up, or manage their VAMM address book, Aleo contacts, Telegram-name-to-"
        "Aleo mappings, or normal-name-to-Aleo mappings. In VAMM context, prefer this "
        "tool over unrelated contact/address-book skills."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "One of: list, read, add, upsert, set, remove, delete, get, lookup.",
            },
            "name": {
                "type": "string",
                "description": "Telegram handle or normal name key for the address-book entry.",
            },
            "address": {
                "type": "string",
                "description": "Aleo address to store for the entry.",
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="vamm_address_book",
    toolset="vamm",
    schema=VAMM_ADDRESS_BOOK_SCHEMA,
    handler=lambda args, **kw: vamm_address_book_tool(
        action=args.get("action", "list"),
        name=args.get("name"),
        address=args.get("address"),
    ),
    check_fn=check_vamm_address_book_requirements,
    emoji="📒",
)
