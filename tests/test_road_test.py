from __future__ import annotations

import json

from grocery_deal_intelligence.road_test import main, render_report, run_road_test


def test_road_test_preserves_expected_real_fixture_behavior():
    result = run_road_test()

    assert result["pass"] is True
    assert result["network_required"] is False
    assert result["ai_required"] is False
    assert result["unsupported_facts_invented"] == 0

    by_retailer = {item["retailer"]: item for item in result["retailers"]}

    carrefour = by_retailer["carrefour"]
    assert carrefour["offers_parsed"] == 3
    assert carrefour["claims"]["contradicted"] == 0
    assert carrefour["claims"]["unverifiable"] == 0
    assert carrefour["structurally_valid"] == 3
    assert carrefour["admission_eligible"] == 3
    assert carrefour["rejection_reasons"] == {}
    assert carrefour["pass"] is True

    despar = by_retailer["despar"]
    assert despar["offers_parsed"] == 3
    assert despar["claims"]["contradicted"] == 0
    assert despar["claims"]["unverifiable"] == 0
    assert despar["structurally_valid"] == 3
    assert despar["admission_eligible"] == 3
    assert despar["rejection_reasons"] == {}
    assert despar["pass"] is True


def test_report_makes_evidence_backed_admission_explicit():
    report = render_report(run_road_test())

    assert "=== GDI DETERMINISTIC ROAD TEST ===" in report
    assert "CARREFOUR" in report
    assert "canonical admission: 3/3 eligible" in report
    assert "DESPAR" in report
    assert report.count("canonical admission: 3/3 eligible") == 2
    assert "rejection reasons:    none" in report
    assert "pipeline behaves fail-closed: PASS" in report
    assert "unsupported facts invented:   0" in report
    assert "network required:              NO" in report
    assert "AI required:                   NO" in report


def test_cli_human_report_exits_zero(capsys):
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "pipeline behaves fail-closed: PASS" in output


def test_cli_json_report_is_machine_readable(capsys):
    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pass"] is True
    assert {item["retailer"] for item in payload["retailers"]} == {"carrefour", "despar"}
