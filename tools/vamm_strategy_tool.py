#!/usr/bin/env python3
"""VAMM settlement-strategy configuration tool."""

from __future__ import annotations

import json

from tools.vamm_config import get_vamm_execution_config, set_vamm_execution_config


_DEFAULTS = {
    "settlement_strategy": "coingecko",
    "network": "testnet",
    "prover_mode": "remote",
}


def check_vamm_strategy_requirements() -> bool:
    return True


def vamm_strategy_tool(
    action: str = "status",
    settlement_strategy: str | None = None,
    network: str | None = None,
    prover_mode: str | None = None,
    prover_url: str | None = None,
    settlement_route: str | None = None,
) -> str:
    normalized = str(action or "status").strip().lower()

    if normalized == "status":
        execution = get_vamm_execution_config()
        return json.dumps({
            "ok": True,
            "tool": "vamm_strategy",
            "action": "status",
            "changed": False,
            "execution": execution,
        }, ensure_ascii=False)

    if normalized in {"set", "configure", "update"}:
        payload = {}
        if settlement_strategy is not None:
            payload["settlement_strategy"] = settlement_strategy
        if network is not None:
            payload["network"] = network
        if prover_mode is not None:
            payload["prover_mode"] = prover_mode
        if prover_url is not None:
            payload["prover_url"] = prover_url
        if settlement_route is not None:
            payload["settlement_route"] = settlement_route
        updated = set_vamm_execution_config(payload)
        return json.dumps({
            "ok": True,
            "tool": "vamm_strategy",
            "action": normalized,
            "changed": True,
            "execution": updated,
            "message": (
                f"VAMM execution updated: strategy={updated['settlement_strategy']}, "
                f"network={updated['network']}, prover={updated['prover_mode']}."
            ),
        }, ensure_ascii=False)

    if normalized in {"set_coingecko", "coingecko"}:
        updated = set_vamm_execution_config({"settlement_strategy": "coingecko"})
        return json.dumps({
            "ok": True,
            "tool": "vamm_strategy",
            "action": normalized,
            "changed": True,
            "execution": updated,
            "message": "VAMM settlement strategy set to CoinGecko.",
        }, ensure_ascii=False)

    return json.dumps({
        "ok": False,
        "error": f"Unsupported action: {action}",
        "supported_actions": ["status", "set", "configure", "update", "set_coingecko", "coingecko"],
        "defaults": _DEFAULTS,
    }, ensure_ascii=False)


VAMM_STRATEGY_SCHEMA = {
    "name": "vamm_strategy",
    "description": (
        "Read or configure the VAMM settlement strategy and execution posture. "
        "Use this in VAMM mode when the user asks about settlement strategy, "
        "pricing source, remote prover, or testnet execution configuration."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "One of: status, set, configure, update, set_coingecko, coingecko.",
            },
            "settlement_strategy": {
                "type": "string",
                "description": "Settlement/pricing strategy name, e.g. coingecko.",
            },
            "network": {
                "type": "string",
                "description": "Target execution network, e.g. testnet.",
            },
            "prover_mode": {
                "type": "string",
                "description": "Execution prover mode, e.g. remote.",
            },
            "prover_url": {
                "type": "string",
                "description": "Remote prover URL.",
            },
            "settlement_route": {
                "type": "string",
                "description": "Human-readable settlement route description.",
            },
        },
        "required": ["action"],
    },
}


from tools.registry import registry

registry.register(
    name="vamm_strategy",
    toolset="vamm",
    schema=VAMM_STRATEGY_SCHEMA,
    handler=lambda args, **kw: vamm_strategy_tool(
        action=args.get("action", "status"),
        settlement_strategy=args.get("settlement_strategy"),
        network=args.get("network"),
        prover_mode=args.get("prover_mode"),
        prover_url=args.get("prover_url"),
        settlement_route=args.get("settlement_route"),
    ),
    check_fn=check_vamm_strategy_requirements,
    emoji="◈",
)
