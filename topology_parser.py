"""Parse the text export produced by the Packet Tracer MCP bridge."""

from __future__ import annotations

import re
from typing import Any


HEADER_RE = re.compile(
    r"^\s*(.*?)\s+\[([^\]]+)\]\s+@\s*\((-?\d+),\s*(-?\d+)\)\s*$"
)

INTERFACE_RE = re.compile(
    r"^\s{2,}(\S+)"
    r"(?:\s+IP=(\S+))?"
    r"(?:\s+\[(linked|unlinked)\])?\s*$",
    re.IGNORECASE,
)


def _extract_export_text(response: Any) -> str:
    """Extract export text from the MCP wrapper or a direct text string."""

    if isinstance(response, str):
        return response

    if isinstance(response, dict):
        result = response.get("result", response)

        if isinstance(result, str):
            return result

        if isinstance(result, list):
            return "\n".join(
                item for item in result if isinstance(item, str)
            )

    raise TypeError(
        "Unsupported topology export format. "
        "Expected text or an MCP wrapper containing text."
    )


def parse_topology_export(response: Any) -> dict[str, Any]:
    """Convert the Packet Tracer text export into structured records.

    Link/interface operational state is not inferred from '[linked]'.
    """

    text = _extract_export_text(response)

    devices: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    current_device: dict[str, Any] | None = None
    in_links_section = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if line.strip().lower() == "--- links ---":
            in_links_section = True
            current_device = None
            continue

        if not line.strip():
            continue

        if not in_links_section:
            header = HEADER_RE.match(line)

            if header:
                name, model, x, y = header.groups()
                current_device = {
                    "name": name.strip(),
                    "model": model.strip(),
                    "position": {"x": int(x), "y": int(y)},
                    "interfaces": [],
                }
                devices.append(current_device)
                continue

            if current_device is not None:
                interface_match = INTERFACE_RE.match(line)

                if interface_match:
                    interface_name, ip_address, link_marker = (
                        interface_match.groups()
                    )

                    interface = {
                        "name": interface_name,
                        "ip_address": ip_address,
                        "linked": (
                            link_marker.lower() == "linked"
                            if link_marker
                            else None
                        ),
                        "operational_state": "unknown",
                    }

                    current_device["interfaces"].append(interface)

        else:
            # Preserve each raw link description until its exact format
            # can be mapped reliably to both endpoints.
            links.append({
                "id": len(links),
                "raw": line.strip(),
                "endpoint1": None,
                "endpoint2": None,
                "up": None,
                "operational_state": "unknown",
            })

    return {
        "source": "Packet Tracer MCP text export",
        "device_count_reported": _reported_count(text, "devices"),
        "link_count_reported": _reported_count(text, "links"),
        "devices": devices,
        "links": links,
        "metadata": {
            "operational_link_states_measured": False,
            "raw_link_descriptions_preserved": True,
        },
    }


def _reported_count(text: str, label: str) -> int | None:
    match = re.search(
        rf"Topology Export:\s*(\d+)\s+devices,\s*(\d+)\s+links",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    return int(match.group(1 if label == "devices" else 2))
