from ecan_engine import analyze_evidence
import json

# Test 1: A reported down link.
down_link_topology = {
    "devices": [{"name": "Router-A"}, {"name": "Switch-A"}],
    "links": [{
        "id": "L1",
        "up": False,
        "endpoint1": {"device": "Router-A", "port": "G0/0"},
        "endpoint2": {"device": "Switch-A", "port": "G0/1"}
    }]
}

# Test 2: An APIPA address.
apipa_topology = {
    "devices": [{
        "name": "Office-PC",
        "ports": [{
            "name": "FastEthernet0",
            "ipAddress": "169.254.20.10/16"
        }]
    }],
    "links": []
}

# Test 3: A repeated IP value.
duplicate_ip_topology = {
    "devices": [
        {"name": "Router-A", "ipAddress": "192.168.1.1"},
        {"name": "Router-B", "ipAddress": "192.168.1.1"}
    ],
    "links": []
}

tests = [
    ("DOWN LINK", down_link_topology),
    ("APIPA", apipa_topology),
    ("REPEATED IP", duplicate_ip_topology),
]

for name, topology in tests:
    result = analyze_evidence(topology)
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)
    print(json.dumps({
        "completeness": result["evidence_completeness"]["score_percent"],
        "summary": result["summary"],
        "findings": result["findings"]
    }, indent=2))
