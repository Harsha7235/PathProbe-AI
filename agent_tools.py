"""Allow-listed PATHPROBE tools for evidence inspection.

No shell execution, arbitrary CLI, device writes, or network probes are enabled
in this starter registry. Every tool consumes an already-collected snapshot.
"""
from __future__ import annotations

from typing import Any
from measurement_engine import build_measurement_report
from diagnostics_engine import analyze_snapshot
from remediation_engine import build_remediation_plan


def tool_registry() -> list[dict[str, Any]]:
    return [
        {
            "name": "summarize_topology",
            "description": "Summarize collected device/link counts and reported link states.",
            "side_effects": "read_only",
            "requires": ["topology"]
        },
        {
            "name": "list_reported_down_links",
            "description": "List links whose collected up flag is explicitly false.",
            "side_effects": "read_only",
            "requires": ["topology"]
        },
        {
            "name": "list_collection_errors",
            "description": "Return collector errors included in observations.",
            "side_effects": "read_only",
            "requires": ["observations"]
        },
        {
            "name": "analyze_snapshot",
            "description": "Run deterministic evidence-labelled diagnostics on a supplied snapshot.",
            "side_effects": "read_only",
            "requires": ["topology"]
        },
        {
            "name": "plan_remediation",
            "description": "Create a manual-approval remediation plan from deterministic findings; does not execute commands.",
            "side_effects": "plan_only",
            "requires": ["topology"]
        }
    ]


def run_tool(name: str, topology: dict[str, Any],
             observations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    observations = observations if isinstance(observations, list) else []

    if name == "summarize_topology":
        report = build_measurement_report(topology, observations)
        return {"tool": name, "status": "success", "summary": report["summary"]}

    if name == "list_reported_down_links":
        links = topology.get("links", []) if isinstance(topology, dict) else []
        down = []
        for index, link in enumerate(links if isinstance(links, list) else []):
            if not isinstance(link, dict) or link.get("up") is not False:
                continue
            ep1 = link.get("endpoint1") if isinstance(link.get("endpoint1"), dict) else {}
            ep2 = link.get("endpoint2") if isinstance(link.get("endpoint2"), dict) else {}
            down.append({
                "link_id": link.get("id", index),
                "endpoint1": ep1,
                "endpoint2": ep2,
                "source": "Packet Tracer Script Module link/port state API"
            })
        return {
            "tool": name,
            "status": "success",
            "count": len(down),
            "down_links": down,
            "note": "Reported down state does not independently establish root cause."
        }

    if name == "list_collection_errors":
        errors = []
        for item in observations:
            if isinstance(item, dict) and item.get("type") == "topology_snapshot":
                vals = item.get("collection_errors", [])
                if isinstance(vals, list):
                    errors.extend(str(v) for v in vals)
        return {"tool": name, "status": "success", "count": len(errors), "errors": errors}

    if name == "analyze_snapshot":
        return {"tool": name, "status": "success",
                "diagnostics": analyze_snapshot(topology, observations)}

    if name == "plan_remediation":
        diagnostics = analyze_snapshot(topology, observations)
        return {"tool": name, "status": "plan_only",
                "remediation": build_remediation_plan(diagnostics)}

    return {
        "tool": name,
        "status": "rejected",
        "error": "Tool is not allow-listed. No action was executed."
    }
