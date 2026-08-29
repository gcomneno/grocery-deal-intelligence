from __future__ import annotations

import json

import pytest

from grocery_deal_intelligence import business_road_test
from grocery_deal_intelligence.business_road_test import (
    main,
    render_report,
    run_business_road_test,
)


def test_business_road_test_advances_to_normalized_attributes():
    result = run_business_road_test()

    assert result["pass"] is True
    assert result["final"] == "unknown"
    assert result["authorized_stopping_boundary"] == "normalized_attributes"
    assert result["network_required"] is False
    assert result["ai_required"] is False

    offers = {offer["retailer"]: offer for offer in result["offers"]}
    carrefour = offers["carrefour"]
    despar = offers["despar"]

    assert carrefour["source_evidence"]["status"] == "pass"
    assert despar["source_evidence"]["status"] == "pass"
    assert carrefour["canonical_admission"]["canonical_present"] is True
    assert despar["canonical_admission"]["canonical_present"] is True
    assert carrefour["canonical_admission"]["status"] == "pass"
    assert despar["canonical_admission"]["status"] == "pass"
    assert carrefour["canonical_admission"]["reasons"] == []
    assert despar["canonical_admission"]["reasons"] == []

    assert carrefour["normalized_attributes"]["status"] == "fail_closed"
    assert [
        reason["code"] for reason in carrefour["normalized_attributes"]["reasons"]
    ] == ["quantity_evidence_unavailable"]
    assert despar["normalized_attributes"]["status"] == "pass"
    assert despar["normalized_attributes"]["values"]["volume_ml"] == 500

    stages = {stage["id"]: stage for stage in result["stages"]}
    assert stages["source_evidence"]["status"] == "pass"
    assert stages["canonical_admission"]["status"] == "pass"
    assert stages["normalized_attributes"]["reached"] is True
    assert stages["normalized_attributes"]["status"] == "fail_closed"
    assert stages["normalized_attributes"]["sides"] == {
        "carrefour": "fail_closed",
        "despar": "pass",
    }
    for stage_id in (
        "semantic_comparability",
        "economic_normalization",
        "price_comparison",
    ):
        assert stages[stage_id] == {
            "id": stage_id,
            "reached": False,
            "status": "not_reached",
            "reason": "upstream_authority_unavailable",
        }


def test_business_road_test_selects_expected_verified_real_offers():
    result = run_business_road_test()
    offers = {offer["retailer"]: offer for offer in result["offers"]}

    assert offers["carrefour"]["product_name"] == (
        "Raffo Birra Raffo Originale Conf. 3 pz da 330 ml Cad. 990 ml"
    )
    assert offers["carrefour"]["price"] == 2.49
    assert offers["carrefour"]["fixture_sha256"] == (
        "25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571"
    )

    assert offers["despar"]["product_name"] == "Birra Speciale Pedavena"
    assert offers["despar"]["price"] == 1.29
    assert offers["despar"]["fixture_sha256"] == (
        "54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17"
    )

    assert all(offer["fixture_read_only"] is True for offer in offers.values())


def test_business_road_test_is_deterministic():
    assert run_business_road_test() == run_business_road_test()


def test_business_road_test_fixture_identity_is_enforced(monkeypatch):
    bad_specs = [dict(spec) for spec in business_road_test._SCENARIO]
    bad_specs[0]["sha256"] = "0" * 64
    monkeypatch.setattr(business_road_test, "_SCENARIO", tuple(bad_specs))

    with pytest.raises(ValueError, match="Carrefour fixture SHA-256 mismatch"):
        run_business_road_test()


def test_human_report_makes_authorized_stop_explicit():
    report = render_report(run_business_road_test())

    assert "=== GDI BUSINESS ROAD TEST ===" in report
    assert "SOURCE EVIDENCE" in report
    assert "carrefour: PASS" in report
    assert "despar: PASS" in report
    assert "CANONICAL ADMISSION" in report
    assert "NORMALIZED ATTRIBUTES" in report
    assert "carrefour: FAIL_CLOSED" in report
    assert "carrefour reasons: quantity_evidence_unavailable" in report
    assert "despar: PASS" in report
    assert "SEMANTIC COMPARABILITY\nNOT REACHED" in report
    assert "FINAL\nUNKNOWN" in report
    assert "Authorized stopping boundary: normalized_attributes" in report
    assert "Business road test: PASS" in report


def test_cli_human_report_exits_zero(capsys):
    assert main([]) == 0
    assert "Business road test: PASS" in capsys.readouterr().out


def test_cli_json_report_is_stable_and_machine_readable(capsys):
    assert main(["--json"]) == 0
    first = capsys.readouterr().out
    assert main(["--json"]) == 0
    second = capsys.readouterr().out

    assert first == second
    payload = json.loads(first)
    assert payload["pass"] is True
    assert payload["final"] == "unknown"
    assert payload["authorized_stopping_boundary"] == "normalized_attributes"
