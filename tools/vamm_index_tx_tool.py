#!/usr/bin/env python3
"""VAMM transaction history tool.

Stores transaction history as a JSON list and returns markdown tables for list
operations so chat can display them cleanly.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from tools.registry import registry
from tools.vamm_store import load_json_store, save_json_store


STORE_FILE = "transaction_history.json"


def check_vamm_index_tx_requirements() -> bool:
    return True


def _load_entries() -> List[Dict[str, str]]:
    raw = load_json_store(STORE_FILE, [])
    if not isinstance(raw, list):
        return []
    cleaned: List[Dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        cleaned.append({
            "index": str(item.get("index", "")).strip(),
            "tx_hash": str(item.get("tx_hash", "")).strip(),
            "asset_in": str(item.get("asset_in", "")).strip(),
            "asset_out": str(item.get("asset_out", "")).strip(),
            "amount_in": str(item.get("amount_in", "")).strip(),
            "amount_out": str(item.get("amount_out", "")).strip(),
            "recipient_address": str(item.get("recipient_address", "")).strip(),
        })
    return cleaned


def _save_entries(entries: List[Dict[str, str]]) -> None:
    save_json_store(STORE_FILE, entries)


def _markdown_table(entries: List[Dict[str, str]]) -> str:
    if not entries:
        return (
            "| Index | Tx Hash | Asset In | Asset Out | Amount In | Amount Out | Recipient Address |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            "| (empty) | - | - | - | - | - | - |"
        )
    lines = [
        "| Index | Tx Hash | Asset In | Asset Out | Amount In | Amount Out | Recipient Address |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            "| {index} | {tx_hash} | {asset_in} | {asset_out} | {amount_in} | {amount_out} | {recipient_address} |".format(**entry)
        )
    return "\n".join(lines)


def _sort_entries(entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    def _key(item: Dict[str, str]):
        try:
            return (0, int(item["index"]))
        except Exception:
            return (1, item["index"])
    return sorted(entries, key=_key)


def vamm_index_tx_tool(
    action: str = "list",
    index: str | None = None,
    tx_hash: str | None = None,
    asset_in: str | None = None,
    asset_out: str | None = None,
    amount_in: str | None = None,
    amount_out: str | None = None,
    recipient_address: str | None = None,
) -> str:
    action = str(action or "list").strip().lower()
    entries = _load_entries()

    if action in {"list", "read"}:
        sorted_entries = _sort_entries(entries)
        return json.dumps({
            "ok": True,
            "tool": "vamm_index_tx",
            "action": action,
            "count": len(sorted_entries),
            "entries": sorted_entries,
            "table_markdown": _markdown_table(sorted_entries),
        }, ensure_ascii=False)

    if action in {"add", "upsert"}:
        normalized = {
            "index": str(index or "").strip(),
            "tx_hash": str(tx_hash or "").strip(),
            "asset_in": str(asset_in or "").strip(),
            "asset_out": str(asset_out or "").strip(),
            "amount_in": str(amount_in or "").strip(),
            "amount_out": str(amount_out or "").strip(),
            "recipient_address": str(recipient_address or "").strip(),
        }
        if not normalized["index"] or not normalized["tx_hash"]:
            return json.dumps({
                "ok": False,
                "error": "'index' and 'tx_hash' are required for add/upsert.",
            }, ensure_ascii=False)
        replaced = False
        for idx, existing in enumerate(entries):
            if existing.get("index") == normalized["index"]:
                entries[idx] = normalized
                replaced = True
                break
        if not replaced:
            entries.append(normalized)
        entries = _sort_entries(entries)
        _save_entries(entries)
        return json.dumps({
            "ok": True,
            "tool": "vamm_index_tx",
            "action": action,
            "changed": True,
            "replaced": replaced,
            "entry": normalized,
            "count": len(entries),
            "table_markdown": _markdown_table(entries),
        }, ensure_ascii=False)

    if action in {"remove", "delete"}:
        key = str(index or "").strip()
        if not key:
            return json.dumps({"ok": False, "error": "'index' is required for remove/delete."}, ensure_ascii=False)
        remaining = [entry for entry in entries if entry.get("index") != key]
        if len(remaining) == len(entries):
            return json.dumps({"ok": False, "error": f"No transaction history entry found for index '{key}'."}, ensure_ascii=False)
        _save_entries(remaining)
        return json.dumps({
            "ok": True,
            "tool": "vamm_index_tx",
            "action": action,
            "changed": True,
            "removed_index": key,
            "count": len(remaining),
            "table_markdown": _markdown_table(_sort_entries(remaining)),
        }, ensure_ascii=False)

    if action in {"get", "lookup"}:
        query_index = str(index or "").strip()
        query_hash = str(tx_hash or "").strip().lower()
        matches = []
        for entry in entries:
            if query_index and entry.get("index") == query_index:
                matches.append(entry)
            elif query_hash and query_hash in entry.get("tx_hash", "").lower():
                matches.append(entry)
        matches = _sort_entries(matches)
        return json.dumps({
            "ok": True,
            "tool": "vamm_index_tx",
            "action": action,
            "count": len(matches),
            "entries": matches,
            "table_markdown": _markdown_table(matches),
        }, ensure_ascii=False)

    return json.dumps({
        "ok": False,
        "error": f"Unsupported action: {action}",
        "supported_actions": ["list", "read", "add", "upsert", "remove", "delete", "get", "lookup"],
    }, ensure_ascii=False)


VAMM_INDEX_TX_SCHEMA = {
    "name": "vamm_index_tx",
    "description": (
        "Manage VAMM transaction history in JSON-backed storage. Records include "
        "index, Aleo tx hash, asset in/out, amount in/out, and recipient address. "
        "For list/read/get results, use the returned markdown table to present the "
        "history cleanly in chat. Use this tool when the user asks to show, list, "
        "view, add, update, delete, or look up VAMM transaction history, swaps, "
        "transfers, indexed transactions, or Aleo transaction records in VAMM mode."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "One of: list, read, add, upsert, remove, delete, get, lookup.",
            },
            "index": {"type": "string", "description": "Transaction index key."},
            "tx_hash": {"type": "string", "description": "Aleo transaction hash."},
            "asset_in": {"type": "string", "description": "Input asset symbol or identifier."},
            "asset_out": {"type": "string", "description": "Output asset symbol or identifier."},
            "amount_in": {"type": "string", "description": "Input amount."},
            "amount_out": {"type": "string", "description": "Output amount."},
            "recipient_address": {"type": "string", "description": "Recipient Aleo address."},
        },
        "required": ["action"],
    },
}


registry.register(
    name="vamm_index_tx",
    toolset="vamm",
    schema=VAMM_INDEX_TX_SCHEMA,
    handler=lambda args, **kw: vamm_index_tx_tool(
        action=args.get("action", "list"),
        index=args.get("index"),
        tx_hash=args.get("tx_hash"),
        asset_in=args.get("asset_in"),
        asset_out=args.get("asset_out"),
        amount_in=args.get("amount_in"),
        amount_out=args.get("amount_out"),
        recipient_address=args.get("recipient_address"),
    ),
    check_fn=check_vamm_index_tx_requirements,
    emoji="📄",
)
