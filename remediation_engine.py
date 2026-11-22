"""Safe remediation planning. Plans are never executed by this module."""
from __future__ import annotations
from typing import Any


def build_remediation_plan(diagnostics: dict[str, Any]) -> dict[str, Any]:
    findings = diagnostics.get("findings", []) if isinstance(diagnostics, dict) else []
    plans = []
    templates = {
        "LINK_REPORTED_DOWN": (
            "Inspect both endpoints and determine whether the interface should be enabled.",
            ["Collect show interfaces status / show ip interface brief evidence.",
             "Check cabling and intended topology.",
             "Only propose 'no shutdown' if administrative shutdown is confirmed and enabling the port is approved."],
            "high",
        ),
        "REPEATED_IP_CANDIDATE": (
            "Validate repeated addresses before changing anything.",
            ["Map each address to its device and interface.",
             "Check HSRP/VRRP/GLBP or virtual gateway intent.",
             "Compare subnet and ARP evidence; do not remove an address solely because it repeats."],
            "medium",
        ),
        "APIPA_ADDRESS": (
            "Investigate DHCP and client addressing.",
            ["Confirm the endpoint is intended to use DHCP.",
             "Verify VLAN membership and DHCP scope.",
             "Check relay configuration and server reachability."],
            "medium",
        ),
        "LINK_STATE_UNKNOWN": (
            "Collect link state before selecting a repair.",
            ["Inspect both link endpoints using the supported Packet Tracer interface.",
             "Record administrative and operational state.",
             "Re-run diagnostics with the returned evidence."],
            "medium",
        ),
        "EVIDENCE_INCOMPLETE": (
            "Collect missing evidence before taking corrective action.",
            ["Collect routing configuration for routing-related faults.",
             "Collect VLAN/access/trunk evidence for switching-related faults.",
             "Run an approved connectivity test and preserve its actual result."],
            "medium",
        ),
        "INVALID_IP_FIELD": (
            "Validate and normalize the source IP field.",
            ["Check the collector's source value and field semantics.",
             "Re-collect the field from the device before changing network settings."],
            "low",
        ),
    }
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        code = finding.get("code")
        if code not in templates:
            continue
        title, steps, priority = templates[code]
        plans.append({
            "plan_id": f"PLAN-{len(plans)+1:03d}",
            "finding_id": finding.get("id"),
            "finding_code": code,
            "title": title,
            "priority": priority,
            "steps": steps,
            "execution_mode": "manual_approval_required",
            "commands_executed": [],
            "configuration_changed": False,
            "preconditions": [
                "Confirm device identity and platform.",
                "Capture current configuration/state and establish rollback.",
                "Obtain explicit operator approval before any configuration change.",
            ],
        })
    return {
        "status": "plan_only",
        "plan_count": len(plans),
        "plans": plans,
        "policy": {
            "automatic_execution_enabled": False,
            "reason": "No authenticated, device-specific write path and rollback workflow have been verified.",
            "configuration_changed": False,
        },
    }
