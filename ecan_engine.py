"""E-CAN: Evidence-Completeness-Aware Network Diagnosis.

This module analyzes an already-collected topology snapshot.
It does not run network probes, modify configurations, or claim
that a diagnosis has been experimentally verified.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any
import ipaddress


ENGINE_VERSION = "0.1.0"

EVIDENCE_CATEGORIES = {
    "topology": 2.0,
    "link_state": 2.0,
    "ip_addressing": 1.5,
    "routing_configuration": 2.0,
    "vlan_configuration": 1.5,
    "active_connectivity_test": 2.0,
}


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _valid_ip(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    try:
        ipaddress.ip_interface(value.strip())
        return True
    except ValueError:
        try:
            ipaddress.ip_address(value.strip())
            return True
        except ValueError:
            return False


def _extract_ips(value: Any, path: str = "") -> list[dict[str, str]]:
    """Extract IP-like fields from nested structured topology data."""
    found = []

    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            key_lower = str(key).lower()

            if isinstance(item, str) and (
                "ip" in key_lower or "address" in key_lower
            ):
                if _valid_ip(item):
                    found.append({
                        "path": child_path,
                        "value": item.strip(),
                    })

            if isinstance(item, (dict, list)):
                found.extend(_extract_ips(item, child_path))

    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_extract_ips(item, f"{path}[{index}]"))

    return found


def _has_evidence(observations: list, *keywords: str) -> bool:
    """Look for explicit evidence categories in structured observations."""
    for observation in observations:
        if not isinstance(observation, dict):
            continue

        text = " ".join(
            str(observation.get(key, ""))
            for key in ("type", "category", "name", "source")
        ).lower()

        if all(keyword.lower() in text for keyword in keywords):
            return True

    return False


def analyze_evidence(
    topology: dict[str, Any],
    observations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return evidence coverage, observations, hypotheses, and next steps."""

    topology = topology if isinstance(topology, dict) else {}
    observations = _list(observations)

    devices = _list(topology.get("devices"))
    links = _list(topology.get("links"))

    # Determine whether evidence is present, not whether the network is correct.
    evidence_available = {
        "topology": bool(devices or links),
        "link_state": bool(links) and any(
            isinstance(link, dict) and isinstance(link.get("up"), bool)
            for link in links
        ),
        "ip_addressing": bool(_extract_ips(topology)),
        "routing_configuration": _has_evidence(
            observations, "routing"
        ),
        "vlan_configuration": _has_evidence(
            observations, "vlan"
        ),
        "active_connectivity_test": _has_evidence(
            observations, "connectivity"
        ),
    }

    total_weight = sum(EVIDENCE_CATEGORIES.values())
    available_weight = sum(
        weight
        for category, weight in EVIDENCE_CATEGORIES.items()
        if evidence_available[category]
    )

    completeness = round(
        100.0 * available_weight / total_weight, 2
    )

    findings = []
    recommendations = []

    down_links = []
    unknown_links = []

    for index, link in enumerate(links):
        if not isinstance(link, dict):
            continue

        state = link.get("up")
        endpoints = {
            "endpoint1": link.get("endpoint1"),
            "endpoint2": link.get("endpoint2"),
        }

        record = {
            "link_id": link.get("id", index),
            "endpoints": endpoints,
        }

        if state is False:
            down_links.append(record)
        elif not isinstance(state, bool):
            unknown_links.append(record)

    if down_links:
        findings.append({
            "type": "observed_condition",
            "finding": "One or more links are explicitly reported down.",
            "count": len(down_links),
            "evidence": down_links,
        })
        recommendations.append({
            "priority": "high",
            "action": (
                "Inspect the affected link endpoints, interface states, "
                "cabling, and intended administrative configuration."
            ),
            "reason": "A reported down link is observed, but its cause is not established.",
        })

    if unknown_links:
        findings.append({
            "type": "evidence_gap",
            "finding": "Some collected links have unknown or invalid state.",
            "count": len(unknown_links),
            "evidence": unknown_links,
        })
        recommendations.append({
            "priority": "medium",
            "action": "Collect valid state information for the unknown links.",
            "reason": "Unknown state must not be treated as up or down.",
        })

    # Detect repeated IP values as candidates for investigation.
    # A repeated address alone is not proof of an IP conflict.
    ip_records = _extract_ips(topology)
    by_ip = defaultdict(list)

    for record in ip_records:
        by_ip[record["value"]].append(record["path"])

    repeated_ips = {
        ip: paths
        for ip, paths in by_ip.items()
        if len(paths) > 1
    }

    if repeated_ips:
        findings.append({
            "type": "candidate_issue",
            "finding": (
                "Repeated IP values occur in the exported structured data. "
                "They may be intentional; verify interface roles and redundancy."
            ),
            "count": len(repeated_ips),
            "evidence": repeated_ips,
        })
        recommendations.append({
            "priority": "medium",
            "action": (
                "Inspect each repeated IP, its interface, subnet, and any "
                "first-hop redundancy configuration before classifying it."
            ),
            "reason": "Repeated addresses can be intentional in redundant gateway designs.",
        })

    apipa_records = []

    for record in ip_records:
        try:
            address = ipaddress.ip_interface(record["value"]).ip
        except ValueError:
            try:
                address = ipaddress.ip_address(record["value"])
            except ValueError:
                continue

        if address.version == 4 and address in ipaddress.ip_network(
            "169.254.0.0/16"
        ):
            apipa_records.append(record)

    if apipa_records:
        findings.append({
            "type": "candidate_issue",
            "finding": (
                "IPv4 link-local addresses (169.254.0.0/16) were found. "
                "If these clients expect DHCP addressing, investigate DHCP reachability."
            ),
            "count": len(apipa_records),
            "evidence": apipa_records,
        })
        recommendations.append({
            "priority": "medium",
            "action": (
                "Check intended client addressing, VLAN membership, DHCP scope, "
                "and relay configuration where applicable."
            ),
            "reason": "Link-local addressing alone does not prove DHCP is the cause.",
        })

    missing_categories = [
        category
        for category, available in evidence_available.items()
        if not available
    ]

    if missing_categories:
        findings.append({
            "type": "evidence_gap",
            "finding": "Some diagnostic evidence categories are unavailable.",
            "categories": missing_categories,
        })

        recommendations.append({
            "priority": "medium",
            "action": (
                "Collect missing configuration and connectivity evidence "
                "before assigning a definitive root cause."
            ),
            "reason": "The diagnosis is limited by missing evidence.",
        })

    if not findings:
        findings.append({
            "type": "limited_observation",
            "finding": (
                "No specific issue was identified by these initial deterministic checks."
            ),
        })

    return {
        "engine": "E-CAN",
        "engine_version": ENGINE_VERSION,
        "evidence_completeness": {
            "score_percent": completeness,
            "interpretation": (
                "Weighted coverage of configured evidence categories; "
                "not diagnosis confidence or probability of correctness."
            ),
            "available_categories": [
                key for key, value in evidence_available.items() if value
            ],
            "missing_categories": missing_categories,
            "category_status": evidence_available,
            "weights": EVIDENCE_CATEGORIES,
        },
        "summary": {
            "device_records": len(devices),
            "link_records": len(links),
            "reported_down_links": len(down_links),
            "unknown_link_states": len(unknown_links),
            "repeated_ip_values": len(repeated_ips),
            "link_local_ipv4_records": len(apipa_records),
        },
        "findings": findings,
        "recommended_next_steps": recommendations,
        "limitations": [
            "Only supplied topology and observations were analyzed.",
            "No active probes were executed.",
            "No device configuration was changed.",
            "Repeated IP values are candidates, not automatically confirmed conflicts.",
            "Evidence completeness is not diagnosis accuracy.",
        ],
    }
