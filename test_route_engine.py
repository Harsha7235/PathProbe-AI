import unittest

from route_engine import (
    build_graph,
    find_candidate_paths,
    parse_link_descriptions,
)


class TestParseLinkDescriptions(unittest.TestCase):

    def test_parses_wired_link(self):
        text = """--- Links ---
Router1:GigabitEthernet0/0 <--> Switch1:GigabitEthernet0/1
"""
        result = parse_link_descriptions(text)

        self.assertEqual(result["wired_link_count"], 1)
        self.assertEqual(result["wireless_record_count"], 0)
        self.assertEqual(result["unparsed_record_count"], 0)

        link = result["wired_links"][0]
        self.assertEqual(
            link["endpoint1"],
            {"device": "Router1", "interface": "GigabitEthernet0/0"},
        )
        self.assertEqual(
            link["endpoint2"],
            {"device": "Switch1", "interface": "GigabitEthernet0/1"},
        )
        self.assertEqual(link["operational_state"], "unknown")

    def test_interface_name_can_contain_colon(self):
        text = """--- Links ---
Device1:Interface:Subinterface <--> Device2:Ethernet0
"""
        result = parse_link_descriptions(text)

        self.assertEqual(result["wired_link_count"], 1)
        self.assertEqual(
            result["wired_links"][0]["endpoint1"]["interface"],
            "Interface:Subinterface",
        )

    def test_preserves_wireless_observation_without_association(self):
        text = """--- Links ---
Laptop0:Wireless0  )))  [wireless signal]
Research-AP:Port 1  )))  [wireless signal]
"""
        result = parse_link_descriptions(text)

        self.assertEqual(result["wireless_record_count"], 2)
        self.assertEqual(result["wired_link_count"], 0)
        self.assertEqual(len(result["wireless_records"]), 2)

        for record in result["wireless_records"]:
            self.assertEqual(record["operational_state"], "unknown")
            self.assertIn("raw", record)

        # Wireless observations must not be converted into client-to-AP links.
        self.assertEqual(result["wired_links"], [])

    def test_malformed_and_self_links_are_preserved_as_unparsed(self):
        text = """--- Links ---
Malformed connection
Router1:GigabitEthernet0/0 <--> Router1:GigabitEthernet0/1
"""
        result = parse_link_descriptions(text)

        self.assertEqual(result["wired_link_count"], 0)
        self.assertEqual(result["unparsed_record_count"], 2)

    def test_ignores_records_before_links_section(self):
        text = """Router1:GigabitEthernet0/0 <--> Switch1:GigabitEthernet0/1
--- Links ---
Router1:GigabitEthernet0/0 <--> Switch1:GigabitEthernet0/1
"""
        result = parse_link_descriptions(text)

        self.assertEqual(result["wired_link_count"], 1)


class TestBuildGraph(unittest.TestCase):

    def setUp(self):
        text = """--- Links ---
A:Eth0 <--> B:Eth0
B:Eth1 <--> C:Eth0
"""
        self.parsed = parse_link_descriptions(text)

    def test_includes_isolated_devices(self):
        graph = build_graph(
            self.parsed,
            device_names=["A", "B", "C", "Isolated", "  "],
        )

        self.assertEqual(set(graph), {"A", "B", "C", "Isolated"})
        self.assertEqual(graph["Isolated"], [])

    def test_wired_graph_is_undirected(self):
        graph = build_graph(self.parsed, ["A", "B", "C"])

        self.assertEqual(
            [edge["device"] for edge in graph["A"]],
            ["B"],
        )
        self.assertEqual(
            {edge["device"] for edge in graph["B"]},
            {"A", "C"},
        )
        self.assertEqual(
            [edge["device"] for edge in graph["C"]],
            ["B"],
        )

    def test_graph_preserves_unknown_operational_state(self):
        graph = build_graph(self.parsed, ["A", "B", "C"])

        for edges in graph.values():
            for edge in edges:
                self.assertEqual(edge["operational_state"], "unknown")


class TestFindCandidatePaths(unittest.TestCase):

    def setUp(self):
        text = """--- Links ---
A:Eth0 <--> B:Eth0
B:Eth1 <--> D:Eth0
A:Eth1 <--> C:Eth0
C:Eth1 <--> D:Eth1
"""
        self.parsed = parse_link_descriptions(text)
        self.graph = build_graph(
            self.parsed,
            ["A", "B", "C", "D", "Isolated"],
        )

    def test_finds_shortest_hop_candidate_paths(self):
        result = find_candidate_paths(self.graph, "A", "D")

        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(len(result["candidate_paths"]), 1)

        for path in result["candidate_paths"]:
            self.assertEqual(path["hops"], 2)
            self.assertEqual(path["devices"][0], "A")
            self.assertEqual(path["devices"][-1], "D")
            self.assertFalse(path["operationally_verified"])

        self.assertFalse(result["operationally_verified"])

    def test_returns_no_candidate_path_for_disconnected_devices(self):
        result = find_candidate_paths(self.graph, "A", "Isolated")

        self.assertEqual(result["status"], "no_candidate_path")
        self.assertEqual(result["candidate_paths"], [])
        self.assertFalse(result["operationally_verified"])

    def test_returns_insufficient_topology_for_missing_endpoint(self):
        result = find_candidate_paths(self.graph, "A", "Missing")

        self.assertEqual(result["status"], "insufficient_topology")
        self.assertEqual(result["candidate_paths"], [])
        self.assertFalse(result["operationally_verified"])

    def test_same_source_and_destination_has_zero_hops(self):
        result = find_candidate_paths(self.graph, "A", "A")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["candidate_paths"][0]["hops"], 0)
        self.assertEqual(result["candidate_paths"][0]["devices"], ["A"])
        self.assertFalse(result["operationally_verified"])

    def test_rejects_empty_source_or_destination(self):
        with self.assertRaises(ValueError):
            find_candidate_paths(self.graph, "", "D")

        with self.assertRaises(ValueError):
            find_candidate_paths(self.graph, "A", " ")

    def test_rejects_invalid_path_limits(self):
        with self.assertRaises(ValueError):
            find_candidate_paths(self.graph, "A", "D", max_paths=0)

        with self.assertRaises(ValueError):
            find_candidate_paths(self.graph, "A", "D", max_hops=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
