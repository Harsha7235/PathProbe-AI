"""Restricted client for the local Packet Tracer MCP server."""
from __future__ import annotations

import asyncio
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_SERVER_URL = "http://127.0.0.1:39400/mcp"

# Only explicitly approved read-only tools and a bounded connectivity test.
# No configuration/write/terminal command tools are exposed here.
TOOL_TIMEOUTS = {
    "pt_bridge_status": 20,
    "pt_export_topology": 30,
    "pt_health_check": 30,
    "pt_inspect_ports": 30,
    "pt_verify_connectivity": 75,
}


async def _call_mcp_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    if tool_name not in TOOL_TIMEOUTS:
        raise ValueError(f"Tool is not allow-listed: {tool_name}")
    args = arguments or {}
    if not isinstance(args, dict):
        raise TypeError("MCP tool arguments must be an object")

    async with asyncio.timeout(TOOL_TIMEOUTS[tool_name]):
        async with streamable_http_client(MCP_SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, args)
                text_parts = [
                    item.text for item in result.content if hasattr(item, "text")
                ]
                payload = {
                    "tool": tool_name,
                    "status": "error" if result.is_error else "success",
                    "result": text_parts,
                }
                if result.is_error:
                    payload["error"] = "MCP tool reported an error."
                return payload


async def get_bridge_status() -> dict[str, Any]:
    return await _call_mcp_tool("pt_bridge_status")


async def export_live_topology() -> dict[str, Any]:
    return await _call_mcp_tool("pt_export_topology")


async def get_live_health_check() -> dict[str, Any]:
    return await _call_mcp_tool("pt_health_check")


async def inspect_device_ports(device: str, only_linked: bool = False) -> dict[str, Any]:
    if not isinstance(device, str) or not device.strip() or len(device) > 120:
        raise ValueError("device must be a non-empty device name up to 120 characters")
    return await _call_mcp_tool("pt_inspect_ports", {
        "device": device.strip(), "only_linked": bool(only_linked)
    })


async def verify_connectivity(from_device: str, to_ip: str, timeout_s: int = 15) -> dict[str, Any]:
    import ipaddress
    if not isinstance(from_device, str) or not from_device.strip() or len(from_device) > 120:
        raise ValueError("from_device must be a non-empty device name up to 120 characters")
    try:
        ipaddress.ip_address(to_ip)
    except (ValueError, TypeError):
        raise ValueError("to_ip must be a valid IPv4 or IPv6 address") from None
    timeout_s = max(5, min(int(timeout_s), 60))
    try:
        result = await _call_mcp_tool("pt_verify_connectivity", {
            "from_device": from_device.strip(), "to_ip": to_ip, "timeout_s": timeout_s
        })
    except TimeoutError:
        return {
            "tool": "pt_verify_connectivity",
            "status": "timeout",
            "result": [],
            "error": "MCP call timed out before a definitive connectivity result was returned. This is not proof of packet loss.",
            "verified": False,
            "connectivity": "unknown",
        }

    # An MCP transport success is not the same as a completed ping.
    import re
    text = " ".join(str(x) for x in result.get("result", []))
    lowered = text.lower()
    if "no result after" in lowered or "may still be running" in lowered or "timed out before" in lowered:
        result.update({
            "status": "timeout",
            "verified": False,
            "connectivity": "unknown",
            "error": "No definitive ping statistics were returned. This is not proof of packet loss.",
        })
        return result

    # Recognize the MCP tool's IOS-style final statistics when present.
    match = re.search(r"success rate is (\d+) percent", text, re.IGNORECASE)
    received_match = re.search(r"Received\s*=\s*(\d+)", text, re.IGNORECASE)
    if match:
        rate = int(match.group(1))
        result.update({
            "status": "completed",
            "verified": True,
            "connectivity": "reachable" if rate == 100 else ("partial" if rate > 0 else "unreachable"),
            "success_rate_percent": rate,
        })
        return result
    if received_match:
        received = int(received_match.group(1))
        result.update({
            "status": "completed",
            "verified": True,
            "connectivity": "reachable" if received > 0 else "unreachable",
            "received_packets": received,
        })
        return result

    result.update({
        "status": "unverified",
        "verified": False,
        "connectivity": "unknown",
        "note": "The tool responded, but its text did not contain recognized final ping statistics.",
    })
    return result
