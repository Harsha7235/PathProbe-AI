"""Deterministic, evidence-labelled PATHPROBE AI diagnostics.

This module never executes probes or changes device configuration. It analyses
only the supplied snapshot and observations.
"""
from __future__ import annotations

import ipaddress
from collections import defaultdict
from typing import Any


def _items(value: Any) -> list:
    return value if isinstance(value, list) else []


def _parse_ip(value: Any):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return ipaddress.ip_interface(value.strip())
    except ValueError:
        try:
            return ipaddress.ip_address(value.strip())
        except ValueError:
            return None


def _ip_records(value: Any, path: str = "") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if isinstance(child, str) and ("ip" in str(key).lower() or "address" in str(key).lower()):
                parsed = _parse_ip(child)
                if parsed is not None:
                    found.append({"path": child_path, "value": child.strip()})
            if isinstance(child, (dict, list)):
                found.extend(_ip_records(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            found.extend(_ip_records(child, f"{path}[{idx}]"))
    return found


def _device_ip_records(devices: list) -> list[dict[str, str]]:
    """Collect IPs per device so duplicate values on one device aren't overcounted."""
    records = []
    for device_index, device in enumerate(devices):
        if not isinstance(device, dict):
            continue
        name = str(device.get("name") or device.get("hostname") or f"device[{device_index}]")
        for record in _ip_records(device, name):
            records.append({"device": name, "path": record["path"], "value": record["value"]})
    return records


def analyze_snapshot(topology: dict[str, Any], observations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    topology = topology if isinstance(topology, dict) else {}
    observations = _items(observations)
    devices = _items(topology.get("devices"))
    links = _items(topology.get("links"))
    findings: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []

    def add(severity: str, code: str, title: str, detail: str, evidence: Any, next_step: str):
        findings.append({
            "id": f"PP-{len(findings)+1:03d}",
            "code": code,
            "severity": severity,
            "title": title,
            "detail": detail,
            "evidence": evidence,
            "status": "observed" if severity != "info" else "evidence_gap_or_info",
        })
        recommendations.append({
            "finding_id": f"PP-{len(findings):03d}",
            "priority": severity,
            "action": next_step,
            "requires_authorization": False,
            "execution_status": "not_executed",
        })

    down_links = []
    unknown_links = []
    for idx, link in enumerate(links):
        if not isinstance(link, dict):
            unknown_links.append({"index": idx, "reason": "link record is not an object"})
            continue
        state = link.get("up")
        record = {
            "link_id": link.get("id", idx),
            "endpoint1": link.get("endpoint1"),
            "endpoint2": link.get("endpoint2"),
            "raw": link.get("raw"),
        }
        if state is False or str(link.get("operational_state", "")).lower() == "down":
            down_links.append(record)
        elif state is True or str(link.get("operational_state", "")).lower() == "up":
            pass
        else:
            unknown_links.append(record)

    if down_links:
        add("high", "LINK_REPORTED_DOWN", "One or more links are reported down",
            "The snapshot explicitly marks these links down. This observation does not by itself establish the root cause.",
            down_links, "Inspect both endpoint interfaces, administrative state, cabling, and intended topology.")
    if unknown_links:
        add("medium", "LINK_STATE_UNKNOWN", "Link state is unavailable for some links",
            "Unknown link state is not treated as up or down.", unknown_links[:100],
            "Collect operational state for the affected interfaces before diagnosing reachability.")

    ip_records = _device_ip_records(devices)
    by_ip: dict[str, list[dict[str, str]]] = defaultdict(list)
    apipa = []
    invalid_ip_fields = []
    for rec in ip_records:
        parsed = _parse_ip(rec["value"])
        if parsed is None:
            invalid_ip_fields.append(rec)
            continue
        addr = parsed.ip if hasattr(parsed, "ip") else parsed
        if addr.version == 4 and addr in ipaddress.ip_network("169.254.0.0/16"):
            apipa.append(rec)
        by_ip[str(addr)].append(rec)

    repeated = {}
    for ip, recs in by_ip.items():
        distinct_devices = sorted({r["device"] for r in recs})
        if len(distinct_devices) > 1:
            repeated[ip] = recs
    if repeated:
        add("medium", "REPEATED_IP_CANDIDATE", "IP addresses repeat across multiple devices",
            "Repeated values are candidates for investigation, not confirmed conflicts; virtual gateways and redundancy may legitimately reuse addresses.",
            repeated, "Check interface roles, subnet, HSRP/VRRP/GLBP configuration, and ARP evidence before declaring a conflict.")
    if apipa:
        add("medium", "APIPA_ADDRESS", "IPv4 link-local addresses were found",
            "169.254.0.0/16 may indicate DHCP failure when the device is expected to use DHCP; this is not conclusive by itself.",
            apipa, "Confirm intended addressing, VLAN, DHCP scope, relay configuration, and DHCP-server reachability.")
    if invalid_ip_fields:
        add("low", "INVALID_IP_FIELD", "Some IP-like fields could not be parsed",
            "These values may be malformed or may not be address fields in the collector schema.",
            invalid_ip_fields, "Review the source fields and normalize valid addresses before using them for diagnosis.")

    evidence_types = set()
    for obs in observations:
        if isinstance(obs, dict):
            for key in ("type", "category", "evidence_type", "name"):
                val = obs.get(key)
                if val:
                    evidence_types.add(str(val).lower())
    routing_available = any("routing" in x for x in evidence_types)
    vlan_available = any("vlan" in x for x in evidence_types)
    connectivity_available = any("connectivity" in x or "ping" in x for x in evidence_types)
    ip_available = bool(ip_records)
    link_state_available = bool(links) and not unknown_links
    gaps = []
    if not devices and not links:
        gaps.append("topology")
    if not link_state_available:
        gaps.append("link_state")
    if not ip_available:
        gaps.append("ip_addressing")
    if not routing_available:
        gaps.append("routing_configuration")
    if not vlan_available:
        gaps.append("vlan_configuration")
    if not connectivity_available:
        gaps.append("active_connectivity_test")

    if gaps:
        add("info", "EVIDENCE_INCOMPLETE", "Diagnosis is limited by missing evidence",
            "The system must not claim a definitive root cause without the required evidence.",
            {"missing_categories": gaps}, "Collect the missing evidence categories before promoting hypotheses to confirmed diagnoses.")
    if not findings:
        add("info", "NO_RULE_MATCH", "No configured rule matched the supplied evidence",
            "This is not proof that the network is healthy.", {},
            "Run approved connectivity checks and collect routing/VLAN configuration where relevant.")

    weights = {
        "topology": 2.0, "link_state": 2.0, "ip_addressing": 1.5,
        "routing_configuration": 2.0, "vlan_configuration": 1.5,
        "active_connectivity_test": 2.0,
    }
    available = {
        "topology": bool(devices or links),
        "link_state": link_state_available,
        "ip_addressing": ip_available,
        "routing_configuration": routing_available,
        "vlan_configuration": vlan_available,
        "active_connectivity_test": connectivity_available,
    }
    total = sum(weights.values())
    completeness = round(100 * sum(weights[k] for k, v in available.items() if v) / total, 2)
    return {
        "engine": "PATHPROBE deterministic diagnostics",
        "engine_version": "1.0.0",
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "summary": {
            "device_count": len(devices), "link_count": len(links),
            "reported_down_links": len(down_links), "unknown_link_states": len(unknown_links),
            "repeated_ip_values_across_devices": len(repeated), "apipa_records": len(apipa),
            "finding_count": len(findings),
        },
        "evidence_completeness": {
            "score_percent": completeness,
            "is_diagnostic_confidence": False,
            "available_categories": [k for k, v in available.items() if v],
            "missing_categories": [k for k, v in available.items() if not v],
            "category_status": available, "weights": weights,
        },
        "findings": findings,
        "recommendations": recommendations,
        "policy": {
            "active_probes_executed": False,
            "device_configuration_changed": False,
            "unknown_state_means_fault": False,
            "llm_output_is_not_ground_truth": True,
        },
    }
