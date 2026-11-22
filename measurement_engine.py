"""PATHPROBE AI measurement engine.

This first version only records facts already exposed by the Packet Tracer
Script Module. It deliberately does not pretend to run ping, HTTP, throughput,
jitter, or other probes. Those tools will be added only after their execution
path is verified for the user's Packet Tracer environment.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import json
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def build_measurement_report(topology: dict[str, Any],
                             observations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Create a provenance-labelled report from a Packet Tracer snapshot."""
    topology = topology if isinstance(topology, dict) else {}
    observations = observations if isinstance(observations, list) else []

    devices = _as_list(topology.get("devices"))
    links = _as_list(topology.get("links"))
    collection_errors = []

    for item in observations:
        if isinstance(item, dict) and item.get("type") == "topology_snapshot":
            errs = item.get("collection_errors", [])
            if isinstance(errs, list):
                collection_errors.extend(str(x) for x in errs)

    up_links = 0
    down_links = 0
    unknown_links = 0
    port_up = 0
    port_down = 0
    port_unknown = 0
    connected_ports = 0

    link_records = []
    for index, link in enumerate(links):
        if not isinstance(link, dict):
            unknown_links += 1
            continue
        up = link.get("up")
        if up is True:
            up_links += 1
            status = "UP"
        elif up is False:
            down_links += 1
            status = "DOWN"
        else:
            unknown_links += 1
            status = "UNKNOWN"

        ep1 = link.get("endpoint1") if isinstance(link.get("endpoint1"), dict) else {}
        ep2 = link.get("endpoint2") if isinstance(link.get("endpoint2"), dict) else {}
        link_records.append({
            "link_id": link.get("id", index),
            "status": status,
            "endpoint1": {"device": ep1.get("device", "Unknown"),
                          "port": ep1.get("port", "Unknown"),
                          "reported_up": ep1.get("up")},
            "endpoint2": {"device": ep2.get("device", "Unknown"),
                          "port": ep2.get("port", "Unknown"),
                          "reported_up": ep2.get("up")},
            "source": "Packet Tracer Script Module link/port state API"
        })

    device_records = []
    for device in devices:
        if not isinstance(device, dict):
            continue
        ports = _as_list(device.get("ports"))
        for port in ports:
            if not isinstance(port, dict):
                continue
            if port.get("connected") is True:
                connected_ports += 1
            if port.get("up") is True:
                port_up += 1
            elif port.get("up") is False:
                port_down += 1
            else:
                port_unknown += 1
        device_records.append({
            "name": device.get("name", "Unknown"),
            "model": device.get("model", "Unknown"),
            "port_count_reported": len(ports),
            "connected_port_count_reported": sum(
                1 for p in ports if isinstance(p, dict) and p.get("connected") is True
            ),
            "source": "Packet Tracer Script Module device/port API"
        })

    raw_link_count = topology.get("rawLinkCount")
    reported_link_count = topology.get("linkCount", len(links))
    reported_device_count = topology.get("deviceCount", len(devices))

    metrics = [
        {
            "name": "device_count",
            "value": len(devices),
            "unit": "devices",
            "status": "OBSERVED",
            "source": "Packet Tracer Script Module snapshot",
            "limitations": "Count of devices returned by the collector; not a reachability test."
        },
        {
            "name": "collected_link_count",
            "value": len(links),
            "unit": "links",
            "status": "OBSERVED",
            "source": "Packet Tracer Script Module snapshot",
            "limitations": "Count of links returned by the collector."
        },
        {
            "name": "reported_up_link_count",
            "value": up_links,
            "unit": "links",
            "status": "OBSERVED",
            "source": "Link endpoint port states",
            "limitations": "Reported link state does not prove application/service reachability."
        },
        {
            "name": "reported_down_link_count",
            "value": down_links,
            "unit": "links",
            "status": "OBSERVED",
            "source": "Link endpoint port states",
            "limitations": "A down report does not by itself identify the root cause."
        },
        {
            "name": "unknown_link_state_count",
            "value": unknown_links,
            "unit": "links",
            "status": "DERIVED_FROM_OBSERVED_STATES",
            "source": "Derived by counting links whose up state is missing or invalid",
            "limitations": "Unknown is not treated as up or down."
        },
        {
            "name": "connected_port_count_reported",
            "value": connected_ports,
            "unit": "ports",
            "status": "OBSERVED",
            "source": "Packet Tracer Script Module port connected flag",
            "limitations": "Connected flag does not establish end-to-end connectivity."
        },
        {
            "name": "reported_up_port_count",
            "value": port_up,
            "unit": "ports",
            "status": "OBSERVED",
            "source": "Packet Tracer Script Module port state API",
            "limitations": "Port state only; not a packet delivery measurement."
        },
        {
            "name": "reported_down_port_count",
            "value": port_down,
            "unit": "ports",
            "status": "OBSERVED",
            "source": "Packet Tracer Script Module port state API",
            "limitations": "A port reported down may be intentionally disabled or unused."
        }
    ]

    unavailable = [
        {"name": "rtt_latency", "status": "NOT_MEASURED",
         "reason": "No verified active probe has been connected yet."},
        {"name": "jitter", "status": "NOT_MEASURED",
         "reason": "Requires repeated timestamped response measurements."},
        {"name": "packet_loss", "status": "NOT_MEASURED",
         "reason": "Requires a verified packet probe and count of sent/received probes."},
        {"name": "throughput", "status": "NOT_MEASURED",
         "reason": "Requires timed transfer counters or traffic measurements."},
        {"name": "http_service_reachability", "status": "NOT_MEASURED",
         "reason": "Requires a real HTTP test against a target service."},
        {"name": "dns_resolution", "status": "NOT_MEASURED",
         "reason": "Requires a DNS query through a verified execution path."},
        {"name": "routing_table", "status": "NOT_COLLECTED",
         "reason": "Device CLI/configuration collection is not yet connected."},
        {"name": "vlan_configuration", "status": "NOT_COLLECTED",
         "reason": "Switch CLI/configuration collection is not yet connected."}
    ]

    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "measurement_policy": "No synthetic values; unknown and unavailable values remain explicit.",
        "summary": {
            "reported_device_count": reported_device_count,
            "collected_device_count": len(devices),
            "reported_link_count": reported_link_count,
            "raw_link_count_reported_by_packet_tracer": raw_link_count,
            "collected_link_count": len(links),
            "up_links": up_links,
            "down_links": down_links,
            "unknown_links": unknown_links,
            "connected_ports_reported": connected_ports,
            "up_ports_reported": port_up,
            "down_ports_reported": port_down,
            "unknown_port_states": port_unknown,
            "collection_error_count": len(collection_errors)
        },
        "metrics": metrics,
        "unavailable_metrics": unavailable,
        "devices": device_records,
        "links": link_records,
        "collection_errors": collection_errors,
        "provenance": {
            "topology_source": "Packet Tracer Script Module",
            "ai_used_for_measurements": False,
            "active_probes_executed": False,
            "configuration_changed": False
        }
    }


def append_jsonl(report: dict[str, Any], log_path: str | Path) -> None:
    """Append a report as one JSON line for experiment history."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False) + "\n")
