import asyncio
import json

from pathprobe_mcp import export_live_topology
from topology_parser import parse_topology_export
from ecan_engine import analyze_evidence


async def main():
    response = await export_live_topology()
    topology = parse_topology_export(response)
    report = analyze_evidence(topology)

    print("=" * 60)
    print("PATHPROBE AI — LIVE E-CAN ANALYSIS")
    print("=" * 60)

    print("\nTOPOLOGY VALIDATION")
    print("Reported devices:", topology["device_count_reported"])
    print("Parsed devices:", len(topology["devices"]))
    print("Reported links:", topology["link_count_reported"])
    print("Parsed link descriptions:", len(topology["links"]))

    print("\nE-CAN ENGINE")
    print("Version:", report["engine_version"])

    print("\nEVIDENCE COMPLETENESS")
    print(json.dumps(report["evidence_completeness"], indent=2))

    print("\nSUMMARY")
    print(json.dumps(report["summary"], indent=2))

    print("\nFINDINGS")
    for index, finding in enumerate(report["findings"], 1):
        print(f"\n{index}. {finding['finding']}")
        print("Type:", finding["type"])

        if "count" in finding:
            print("Count:", finding["count"])

        if "categories" in finding:
            print("Categories:", finding["categories"])

    print("\nRECOMMENDED NEXT STEPS")
    for index, item in enumerate(
        report["recommended_next_steps"], 1
    ):
        print(f"\n{index}. Priority: {item['priority']}")
        print("Action:", item["action"])
        print("Reason:", item["reason"])

    print("\nLIMITATIONS")
    for item in report["limitations"]:
        print("-", item)


if __name__ == "__main__":
    asyncio.run(main())
