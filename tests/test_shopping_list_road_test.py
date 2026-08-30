import pytest

from grocery_deal_intelligence import shopping_list_road_test
from grocery_deal_intelligence.shopping_list import (
    NO_ELIGIBLE_OFFERS,
    SELECTION_SINGLETON,
    SELECTION_UNSELECTED,
)
from grocery_deal_intelligence.shopping_list_road_test import (
    _FIXTURE_SHA256,
    _load_fixture_records,
    render_report,
    run_shopping_list_road_test,
)


def test_fixture_sha256_identity_is_enforced(monkeypatch):
    monkeypatch.setattr(
        shopping_list_road_test,
        "_FIXTURE_SHA256",
        "0" * 64,
    )

    with pytest.raises(ValueError, match="Esselunga fixture SHA-256 mismatch"):
        _load_fixture_records()


def test_shopping_list_road_test_contract():
    result = run_shopping_list_road_test()
    shopping_list = result["result"]

    assert result["pass"] is True
    assert result["network_required"] is False
    assert result["ai_required"] is False
    assert result["fixture"]["sha256"] == _FIXTURE_SHA256
    assert result["fixture"]["sha256"] == (
        "2f4d9ad9015490f326cc95ba17243b9889b2a8f83caea224d3e2769552b5c717"
    )

    assert "as_of" not in result
    assert shopping_list["as_of"] == "2026-08-25"
    assert all("as_of" not in item["availability"] for item in shopping_list["items"])

    assert shopping_list["requested_item_count"] == 2
    assert shopping_list["resolved_item_count"] == 1
    assert shopping_list["unresolved_item_count"] == 1
    assert shopping_list["singleton_item_count"] == 1
    assert shopping_list["selected_item_count"] == 0
    assert shopping_list["unselected_item_count"] == 1


def test_caller_item_order_and_per_item_outcomes():
    result = run_shopping_list_road_test()["result"]

    assert [item["id"] for item in result["items"]] == [
        "caller-dark-chocolate",
        "caller-whole-milk",
    ]

    first = result["items"][0]
    second = result["items"][1]

    assert first["selection"]["status"] == SELECTION_SINGLETON
    assert first["selection"]["comparative_claim"] is None
    assert first["selection"]["sole_offer"]["product_name"] == (
        "Vanini fondente 95% 90 g"
    )

    assert second["availability"]["status"] == "unknown"
    assert second["selection"]["status"] == SELECTION_UNSELECTED
    assert second["selection"]["reason"] == {"code": NO_ELIGIBLE_OFFERS}


def test_provenance_remains_inspectable():
    result = run_shopping_list_road_test()["result"]
    offer = result["items"][0]["selection"]["sole_offer"]

    assert offer["provenance"]["source_type"] == "retailer_api"
    assert offer["provenance"]["store_code"] == "ARI"
    assert offer["provenance"]["campaign_id"] == "8260"
    assert offer["provenance"]["observed_at"] == "2026-08-25T17:18:07Z"


def test_human_renderer_and_json_main(capsys):
    result = run_shopping_list_road_test()
    report = render_report(result)

    assert "business/road test: PASS" in report
    assert "network required: NO" in report
