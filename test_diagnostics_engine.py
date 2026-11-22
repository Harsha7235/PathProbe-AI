from diagnostics_engine import analyze_snapshot
from remediation_engine import build_remediation_plan


def test_unknown_link_is_not_reported_as_down():
    result = analyze_snapshot({"devices": [{"name": "R1"}], "links": [{"id": "L1"}]})
    codes = {f["code"] for f in result["findings"]}
    assert "LINK_STATE_UNKNOWN" in codes
    assert "LINK_REPORTED_DOWN" not in codes
    assert result["summary"]["reported_down_links"] == 0


def test_explicitly_down_link_is_reported():
    result = analyze_snapshot({"devices": [], "links": [{"id": "L1", "up": False}]})
    assert any(f["code"] == "LINK_REPORTED_DOWN" for f in result["findings"])


def test_repeated_ip_across_distinct_devices_is_candidate_not_proven_conflict():
    topology = {"devices": [
        {"name": "R1", "ipAddress": "192.0.2.1"},
        {"name": "R2", "ipAddress": "192.0.2.1"},
    ], "links": []}
    result = analyze_snapshot(topology)
    finding = next(f for f in result["findings"] if f["code"] == "REPEATED_IP_CANDIDATE")
    assert "not confirmed conflicts" in finding["detail"]


def test_same_device_duplicate_field_does_not_create_cross_device_conflict():
    topology = {"devices": [
        {"name": "R1", "managementIp": "192.0.2.1", "loopbackAddress": "192.0.2.1"},
    ], "links": []}
    result = analyze_snapshot(topology)
    assert not any(f["code"] == "REPEATED_IP_CANDIDATE" for f in result["findings"])


def test_apipa_detected_without_claiming_root_cause():
    topology = {"devices": [{"name": "PC1", "ipAddress": "169.254.2.3/16"}], "links": []}
    result = analyze_snapshot(topology)
    finding = next(f for f in result["findings"] if f["code"] == "APIPA_ADDRESS")
    assert "not conclusive" in finding["detail"]


def test_evidence_completeness_is_not_confidence():
    result = analyze_snapshot({"devices": [{"name": "PC1"}], "links": []})
    assert result["evidence_completeness"]["is_diagnostic_confidence"] is False
    assert "active_connectivity_test" in result["evidence_completeness"]["missing_categories"]


def test_remediation_is_plan_only_and_never_executes_commands():
    diagnostics = analyze_snapshot({"devices": [], "links": [{"id": "L1", "up": False}]})
    plan = build_remediation_plan(diagnostics)
    assert plan["status"] == "plan_only"
    assert plan["policy"]["automatic_execution_enabled"] is False
    assert all(p["commands_executed"] == [] for p in plan["plans"])
    assert plan["policy"]["configuration_changed"] is False
