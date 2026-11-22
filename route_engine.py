"""Evidence-aware candidate route analysis for PATHPROBE AI.

This module calculates candidate paths from Packet Tracer link descriptions.
It does not claim that a candidate is the route selected by Cisco.
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from typing import Any


LINK_RE = re.compile(
    r"^\s*(.*?)\s*<-->\s*(.*?)\s*$"
)

WIRELESS_RE = re.compile(
    r"\s+\)\)\)\s+\[wireless signal\]\s*$",
    re.IGNORECASE,
)


def _parse_endpoint(value: str) -> dict[str, str] | None:
    """Parse a device:interface endpoint, splitting only at the first colon."""
    value = value.strip()

    if ":" not in value:
        return None

    device, interface = value.split(":", 1)
    device = device.strip()
    interface = interface.strip()

    if not device or not interface:
        return None

    return {
        "device": device,
        "interface": interface,
    }


def parse_link_descriptions(
    export_text: str,
) -> dict[str, Any]:
    """Parse wired links while preserving wireless and unknown records."""

    wired_links = []
    wireless_links = []
    unparsed_links = []
    in_links_section = False

    for line_number, raw_line in enumerate(
        export_text.splitlines(), start=1
    ):
        line = raw_line.strip()

        if line.lower() == "--- links ---":
            in_links_section = True
            continue

        if not in_links_section or not line:
            continue

        if WIRELESS_RE.search(line):
            wireless_links.append({
                "line": line_number,
                "raw": line,
                "operational_state": "unknown",
            })
            continue

        match = LINK_RE.match(line)

        if not match:
            unparsed_links.append({
                "line": line_number,
                "raw": line,
                "reason": "Unrecognized link description",
            })
            continue

        endpoint_a = _parse_endpoint(match.group(1))
        endpoint_b = _parse_endpoint(match.group(2))

        if not endpoint_a or not endpoint_b:
            unparsed_links.append({
                "line": line_number,
                "raw": line,
                "reason": "Could not parse both endpoints",
            })
            continue

        if endpoint_a["device"] == endpoint_b["device"]:
            unparsed_links.append({
                "line": line_number,
                "raw": line,
                "reason": "Self-link requires manual review",
            })
            continue

        wired_links.append({
            "id": len(wired_links),
            "endpoint1": endpoint_a,
            "endpoint2": endpoint_b,
            "raw": line,
            "operational_state": "unknown",
        })

    return {
        "wired_link_count": len(wired_links),
        "wireless_record_count": len(wireless_links),
        "unparsed_record_count": len(unparsed_links),
        "wired_links": wired_links,
        "wireless_records": wireless_links,
        "unparsed_records": unparsed_links,
        "evidence_note": (
            "Exported connections are not proof of operational "
            "connectivity. Link states remain unknown."
        ),
    }


def build_graph(
    parsed_topology: dict[str, Any],
    device_names: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build an undirected graph, including isolated exported devices."""

    graph: dict[str, list[dict[str, Any]]] = defaultdict(list)

    # Include all devices from the topology export, even if isolated.
    for name in device_names or []:
        if isinstance(name, str) and name.strip():
            graph[name.strip()]

    for link in parsed_topology.get("wired_links", []):
        a = link["endpoint1"]["device"]
        b = link["endpoint2"]["device"]

        graph[a].append({
            "device": b,
            "link_id": link["id"],
            "local_interface": link["endpoint1"]["interface"],
            "remote_interface": link["endpoint2"]["interface"],
            "operational_state": link["operational_state"],
        })

        graph[b].append({
            "device": a,
            "link_id": link["id"],
            "local_interface": link["endpoint2"]["interface"],
            "remote_interface": link["endpoint1"]["interface"],
            "operational_state": link["operational_state"],
        })

    return dict(graph)


def find_candidate_paths(
    graph: dict[str, list[dict[str, Any]]],
    source: str,
    destination: str,
    max_paths: int = 5,
    max_hops: int = 30,
) -> dict[str, Any]:
    """Find shortest-hop candidate paths using breadth-first search.

    Returns paths based on the supplied graph, not verified routing tables.
    All connections must be explicitly supplied to this function.
    """

    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty device name")

    if not isinstance(destination, str) or not destination.strip():
        raise ValueError("destination must be a non-empty device name")

    if source == destination:
        return {
            "status": "success",
            "source": source,
            "destination": destination,
            "candidate_paths": [{
                "devices": [source],
                "hops": 0,
            }],
            "selection_basis": "source equals destination",
            "operationally_verified": False,
        }

    if source not in graph or destination not in graph:
        return {
            "status": "insufficient_topology",
            "source": source,
            "destination": destination,
            "candidate_paths": [],
            "message": "Source or destination is absent from the graph.",
            "operationally_verified": False,
        }

    if not 1 <= max_paths <= 20:
        raise ValueError("max_paths must be between 1 and 20")

    if not 1 <= max_hops <= 100:
        raise ValueError("max_hops must be between 1 and 100")

    queue = deque([(source, [source], [])])
    paths = []
    shortest_hops = None

    while queue and len(paths) < max_paths:
        current, devices, links = queue.popleft()
        hops = len(links)

        if shortest_hops is not None and hops > shortest_hops:
            break

        if hops >= max_hops:
            continue

        neighbors = sorted(
            graph.get(current, []),
            key=lambda item: item["device"].casefold(),
        )

        for edge in neighbors:
            next_device = edge["device"]

            if next_device in devices:
                continue

            next_devices = devices + [next_device]
            next_links = links + [{
                "link_id": edge["link_id"],
                "from_device": current,
                "to_device": next_device,
                "from_interface": edge["local_interface"],
                "to_interface": edge["remote_interface"],
                "operational_state": edge["operational_state"],
            }]

            if next_device == destination:
                shortest_hops = len(next_links)
                paths.append({
                    "devices": next_devices,
                    "hops": shortest_hops,
                    "links": next_links,
                    "operationally_verified": False,
                })
            else:
                queue.append((
                    next_device,
                    next_devices,
                    next_links,
                ))

    return {
        "status": "success" if paths else "no_candidate_path",
        "source": source,
        "destination": destination,
        "candidate_paths": paths,
        "paths_returned": len(paths),
        "selection_basis": "minimum hop count in exported graph",
        "operationally_verified": False,
        "limitations": [
            "Link operational state has not been verified.",
            "Routing tables and protocol metrics are not evaluated.",
            "ACLs, VLAN reachability, and routing policies are not evaluated.",
            "Candidate paths do not prove the route selected by Cisco.",
        ],
    }
