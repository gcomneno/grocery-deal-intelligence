from __future__ import annotations

import json

from grocery_deal_intelligence.road_test import main, render_report, run_road_test


def test_road_test_preserves_expected_real_fixture_behavior():
    result = run_road_test()

    assert result["pass"] is True
    assert result["network_required"] is False
    assert result["ai_required"] is False
    assert result["unsupported_facts_invented"] == 0
    assert result["corpus"]["canonical_records"] == 64
    assert result["corpus"]["represented_retailers"] == [
        "carrefour",
        "despar",
        "lidl",
    ]
    assert result["corpus"]["ai_used"] is False
    assert result["corpus"]["network_required"] is False
    assert all(result["corpus"]["invariants"].values())

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

    lidl = by_retailer["lidl"]
    assert lidl["fixture"] == "lidl/data/output/lidl-lucca-current.json"
    assert lidl["offers_parsed"] == 58
    assert lidl["claims"]["supported"] == 1218
    assert lidl["claims"]["contradicted"] == 0
    assert lidl["claims"]["unverifiable"] == 0
    assert lidl["structurally_valid"] == 58
    assert lidl["admission_eligible"] == 58
    assert lidl["rejection_reasons"] == {}
    assert lidl["pass"] is True
    assert all(lidl["invariants"].values())


def test_report_makes_evidence_backed_admission_explicit():
    report = render_report(run_road_test())

    assert "=== GDI DETERMINISTIC ROAD TEST ===" in report
    assert "CARREFOUR" in report
    assert "canonical admission: 3/3 eligible" in report
    assert "DESPAR" in report
    assert report.count("canonical admission: 3/3 eligible") == 2
    assert "LIDL" in report
    assert "canonical admission: 58/58 eligible" in report
    assert "rejection reasons:    none" in report
    assert "CORPUS" in report
    assert "canonical records:           64" in report
    assert "represented retailers:       carrefour, despar, lidl" in report
    assert "AI used:                     NO" in report
    assert "network required by corpus:  NO" in report
    assert "pipeline behaves fail-closed: PASS" in report
    assert "unsupported facts invented:   0" in report
    assert "network required:              NO" in report
    assert "AI required:                   NO" in report


def test_cli_human_report_exits_zero(capsys):
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "pipeline behaves fail-closed: PASS" in output
    assert "canonical records:           64" in output


def test_cli_json_report_is_machine_readable(capsys):
    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pass"] is True
    assert payload["corpus"]["canonical_records"] == 64
    assert payload["corpus"]["represented_retailers"] == [
        "carrefour",
        "despar",
        "lidl",
    ]
    assert {item["retailer"] for item in payload["retailers"]} == {
        "carrefour",
        "despar",
        "lidl",
    }
