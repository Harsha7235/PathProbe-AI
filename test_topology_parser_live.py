import asyncio

from pathprobe_mcp import export_live_topology
from topology_parser import parse_topology_export


async def main():
    response = await export_live_topology()
    topology = parse_topology_export(response)

    print("Reported devices:", topology["device_count_reported"])
    print("Parsed devices:", len(topology["devices"]))
    print("Reported links:", topology["link_count_reported"])
    print("Parsed raw link records:", len(topology["links"]))

    print("\nFirst 3 devices:")
    for device in topology["devices"][:3]:
        print(
            device["name"],
            "| Model:", device["model"],
            "| Interfaces:", len(device["interfaces"]),
        )

    print("\nFirst 5 interfaces:")
    for device in topology["devices"][:3]:
        for interface in device["interfaces"][:5]:
            print(device["name"], interface)

    print("\nFirst 5 raw link descriptions:")
    for link in topology["links"][:5]:
        print(link["raw"])


if __name__ == "__main__":
    asyncio.run(main())
