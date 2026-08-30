from __future__ import annotations

import json

from grocery_deal_intelligence.corpus_business_road_test import (
    main,
    render_report,
    run_corpus_business_road_test,
)


def test_corpus_business_vertical_slice():
    result = run_corpus_business_road_test()

    assert result["pass"] is True
    assert result["corpus"] == {
        "canonical_records": 64,
        "represented_retailers": ["carrefour", "despar", "lidl"],
        "ai_used": False,
        "network_required": False,
    }

    assert result["query"] == {
        "term": "birra",
        "offer_count": 4,
        "retailers": ["carrefour", "despar", "lidl"],
    }

    assert result["availability"]["status"] == "available"
    assert result["availability"]["offer_count"] == 1
    assert result["availability"]["offers"][0]["retailer"] == "carrefour"

    shopping = result["shopping_list"]
    assert shopping["requested_item_count"] == 2
    assert shopping["resolved_item_count"] == 1
    assert shopping["unresolved_item_count"] == 1
    assert shopping["singleton_item_count"] == 1
    assert shopping["unselected_item_count"] == 1

    assert result["ai_required"] is False
    assert result["network_required"] is False
    assert all(result["invariants"].values())


def test_comparison_remains_explicitly_fail_closed():
    result = run_corpus_business_road_test()
    comparison = result["comparison"]

    assert comparison["admission"]["relationship"] == "unknown"
    assert comparison["admission"]["eligible"] is True
    assert len(comparison["verification"]) == 2
    assert all(
        side["status"] == "supported"
        for item in comparison["verification"]
        for side in (item["left"], item["right"])
    )


def test_shopping_list_preserves_explicit_no_match():
    result = run_corpus_business_road_test()
    items = result["shopping_list"]["items"]

    assert [item["id"] for item in items] == [
        "passata",
        "missing-dark-chocolate",
    ]

    assert items[0]["selection"]["status"] == "singleton"

    assert items[1]["availability"]["status"] == "unknown"
    assert items[1]["availability"]["offer_count"] == 0
    assert items[1]["selection"]["status"] == "unselected"
    assert items[1]["selection"]["reason"] == {"code": "no_eligible_offers"}


def test_corpus_business_road_test_is_deterministic():
    assert run_corpus_business_road_test() == run_corpus_business_road_test()


def test_human_and_json_cli(capsys):
    result = run_corpus_business_road_test()
    report = render_report(result)

    assert "canonical records: 64" in report
    assert "represented retailers: carrefour, despar, lidl" in report
    assert "result: PASS" in report

    assert main([]) == 0
    assert "result: PASS" in capsys.readouterr().out

    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pass"] is True
    assert payload["corpus"]["canonical_records"] == 64
