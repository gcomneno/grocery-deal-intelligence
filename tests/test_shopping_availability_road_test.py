from __future__ import annotations

import json

import pytest

from grocery_deal_intelligence import shopping_availability_road_test
from grocery_deal_intelligence.shopping_availability import (
    AVAILABLE,
    NOT_CURRENT,
    PRODUCT_FAMILY_MISMATCH,
    UNKNOWN,
)
from grocery_deal_intelligence.shopping_availability_road_test import (
    _CURRENT_GENUINE_DARK_CHOCOLATE_NAMES,
    _CURRENT_WRONG_FAMILY_NAMES,
    _HISTORICAL_SINGLETON_NAMES,
    _contains_forbidden_comparative_key,
    _load_fixture_records,
    _selected_records,
    _validate_selected_records,
    main,
    render_report,
    run_shopping_availability_road_test,
)


def test_fixture_sha256_identity_is_enforced(monkeypatch):
    monkeypatch.setattr(
        shopping_availability_road_test,
        "_FIXTURE_SHA256",
        "0" * 64,
    )

    with pytest.raises(ValueError, match="Esselunga fixture SHA-256 mismatch"):
        _load_fixture_records()


def test_selected_records_structurally_validate():
    records = _load_fixture_records()
    selected = _selected_records(
        records,
        (
            *_HISTORICAL_SINGLETON_NAMES,
            *_CURRENT_GENUINE_DARK_CHOCOLATE_NAMES,
            *_CURRENT_WRONG_FAMILY_NAMES,
        ),
    )

    validation = _validate_selected_records(selected)

    assert validation["valid"] is True
    assert validation["valid_records"] == len(selected)
    assert validation["invalid_records"] == 0
    assert validation["errors"] == []


def test_historical_singleton_probe_is_available_with_one_offer():
    result = run_shopping_availability_road_test()
    probe = result["historical_singleton_probe"]
    availability = probe["availability"]

    assert probe["pass"] is True
    assert probe["as_of"] == "2026-08-25"
    assert availability["status"] == AVAILABLE
    assert availability["offer_count"] == 1
    assert len(availability["offers"]) == 1
    assert availability["offers"][0]["product_name"] == ("Vanini fondente 95% 90 g")


def test_historical_singleton_preserves_store_price_currency_and_provenance():
    result = run_shopping_availability_road_test()
    offer = result["historical_singleton_probe"]["availability"]["offers"][0]

    assert offer["retailer"] == "esselunga"
    assert offer["locality"] == {
        "scope": "store",
        "stores": ["ARI"],
    }
    assert offer["price"] == 2.19
    assert offer["currency"] == "EUR"
    assert offer["provenance"]["source_type"] == "retailer_api"
    assert offer["provenance"]["store_code"] == "ARI"
    assert offer["provenance"]["campaign_id"] == "8260"
    assert offer["provenance"]["observed_at"] == "2026-08-25T17:18:07Z"


def test_historical_singleton_contains_no_comparative_superiority_claim():
    result = run_shopping_availability_road_test()
    availability = result["historical_singleton_probe"]["availability"]

    assert _contains_forbidden_comparative_key(availability) is False

    keys = _recursive_keys(availability)
    assert "ranking" not in keys
    assert "winner" not in keys
    assert "cheapest" not in keys
    assert "recommendation" not in keys
    assert "semantic_comparison" not in keys
    assert "economic_normalization" not in keys
    assert "price_comparison" not in keys
    assert "comparison" not in keys


def test_current_availability_is_unknown_with_zero_offers():
    result = run_shopping_availability_road_test()
    current = result["current_availability"]
    availability = current["availability"]

    assert current["pass"] is True
    assert current["as_of"] == "2026-08-29"
    assert current["final"] == UNKNOWN
    assert availability["status"] == UNKNOWN
    assert availability["offer_count"] == 0
    assert availability["offers"] == []
    assert result["final"] == UNKNOWN
    assert result["pass"] is True


def test_genuine_expired_dark_chocolate_records_reject_as_not_current():
    result = run_shopping_availability_road_test()
    rejections = {
        item["product_name"]: item["code"]
        for item in result["current_availability"]["availability"]["rejections"]
    }

    assert {
        name: rejections[name] for name in _CURRENT_GENUINE_DARK_CHOCOLATE_NAMES
    } == dict.fromkeys(_CURRENT_GENUINE_DARK_CHOCOLATE_NAMES, NOT_CURRENT)


def test_wrong_family_records_reject_as_product_family_mismatch():
    result = run_shopping_availability_road_test()
    rejections = {
        item["product_name"]: item["code"]
        for item in result["current_availability"]["availability"]["rejections"]
    }

    assert {
        name: rejections[name] for name in _CURRENT_WRONG_FAMILY_NAMES
    } == dict.fromkeys(_CURRENT_WRONG_FAMILY_NAMES, PRODUCT_FAMILY_MISMATCH)


def test_shopping_availability_road_test_is_deterministic():
    assert (
        run_shopping_availability_road_test() == run_shopping_availability_road_test()
    )


def test_human_renderer_contains_expected_distinction():
    report = render_report(run_shopping_availability_road_test())

    assert "historical singleton probe: PASS" in report
    assert "current availability: UNKNOWN" in report
    assert "current eligible offers: 0" in report
    assert "business/road test: PASS" in report
    assert "network required: NO" in report
    assert "AI required: NO" in report


def test_main_human_report_returns_zero(capsys):
    assert main([]) == 0
    assert "business/road test: PASS" in capsys.readouterr().out


def test_main_json_report_returns_zero_and_emits_machine_readable_json(capsys):
    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["pass"] is True
    assert payload["final"] == UNKNOWN
    assert payload["network_required"] is False
    assert payload["ai_required"] is False
    assert payload["historical_singleton_probe"]["availability"]["status"] == (
        AVAILABLE
    )
    assert payload["current_availability"]["availability"]["status"] == UNKNOWN


def _recursive_keys(value):
    if isinstance(value, dict):
        keys = {str(key).lower() for key in value}
        for child in value.values():
            keys.update(_recursive_keys(child))
        return keys

    if isinstance(value, list):
        keys = set()
        for child in value:
            keys.update(_recursive_keys(child))
        return keys

    return set()
