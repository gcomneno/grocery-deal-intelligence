from __future__ import annotations

import argparse
import json
from typing import Any

from grocery_deal_intelligence.comparison import UNKNOWN, compare_admitted_offers
from grocery_deal_intelligence.current_offers import list_current_offers
from grocery_deal_intelligence.filtering import filter_offers
from grocery_deal_intelligence.query import search_offers
from grocery_deal_intelligence.retailers import list_available_retailers
from grocery_deal_intelligence.road_test import _run_retailers_and_assemble_corpus
from grocery_deal_intelligence.shopping_availability import (
    resolve_shopping_item_availability,
)
from grocery_deal_intelligence.shopping_list import LOWEST_PRICE, resolve_shopping_list

_ALL_CURRENT_AS_OF = "2026-08-25"
_FILTERED_CURRENT_AS_OF = "2026-08-29"


def run_corpus_business_road_test() -> dict[str, Any]:
    """Exercise canonical consumers over one assembled deterministic corpus."""
    _, snapshot, upstream_pass = _run_retailers_and_assemble_corpus()
    records = snapshot.canonical_records

    represented_retailers = list_available_retailers(records)

    current_all = list_current_offers(records, as_of=_ALL_CURRENT_AS_OF)
    current_filtered = list_current_offers(records, as_of=_FILTERED_CURRENT_AS_OF)
    lidl_records = filter_offers(records, retailer="lidl")

    birra = search_offers(records, "birra")
    left = next(record for record in birra if record["retailer"] == "carrefour")
    right = next(record for record in birra if record["retailer"] == "despar")

    comparison = compare_admitted_offers(
        left,
        right,
        {
            "relationship": UNKNOWN,
            "claims": [
                {
                    "path": ["product_name"],
                    "left_value": left["product_name"],
                    "right_value": right["product_name"],
                },
                {
                    "path": ["currency"],
                    "left_value": left["currency"],
                    "right_value": right["currency"],
                },
            ],
        },
    )

    passata = resolve_shopping_item_availability(
        records,
        product_family="passata",
        as_of=_FILTERED_CURRENT_AS_OF,
    )

    shopping_list = resolve_shopping_list(
        records,
        items=[
            {
                "id": "passata",
                "product_family": "passata",
                "selection_policy": LOWEST_PRICE,
            },
            {
                "id": "missing-dark-chocolate",
                "product_family": "dark_chocolate",
                "selection_policy": LOWEST_PRICE,
                "comparison_category": "chocolate_bar",
            },
        ],
        as_of=_FILTERED_CURRENT_AS_OF,
    )

    invariants = {
        "upstream_pass": upstream_pass,
        "canonical_records": len(records) == 64,
        "represented_retailers": represented_retailers
        == ["carrefour", "despar", "lidl"],
        "all_current": len(current_all) == 64,
        "filtered_current": len(current_filtered) == 4,
        "lidl_filter": len(lidl_records) == 58,
        "birra_query": (
            len(birra) == 4
            and list_available_retailers(birra) == ["carrefour", "despar", "lidl"]
        ),
        "comparison_fail_closed": (
            comparison["admission"]["relationship"] == UNKNOWN
            and comparison["admission"]["eligible"] is True
            and len(comparison["verification"]) == 2
        ),
        "passata_available": (
            passata["status"] == "available"
            and passata["offer_count"] == 1
            and passata["offers"][0]["retailer"] == "carrefour"
        ),
        "shopping_list": (
            shopping_list["requested_item_count"] == 2
            and shopping_list["resolved_item_count"] == 1
            and shopping_list["unresolved_item_count"] == 1
            and shopping_list["singleton_item_count"] == 1
            and shopping_list["unselected_item_count"] == 1
        ),
        "no_ai": snapshot.ai_used is False,
        "no_network": snapshot.network_required is False,
    }

    return {
        "pass": all(invariants.values()),
        "network_required": False,
        "ai_required": False,
        "corpus": {
            "canonical_records": len(records),
            "represented_retailers": represented_retailers,
            "ai_used": snapshot.ai_used,
            "network_required": snapshot.network_required,
        },
        "current_offers": {
            _ALL_CURRENT_AS_OF: len(current_all),
            _FILTERED_CURRENT_AS_OF: len(current_filtered),
        },
        "lidl_filtered_count": len(lidl_records),
        "query": {
            "term": "birra",
            "offer_count": len(birra),
            "retailers": list_available_retailers(birra),
        },
        "comparison": comparison,
        "availability": passata,
        "shopping_list": shopping_list,
        "invariants": invariants,
    }


def render_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "=== GDI CORPUS BUSINESS ROAD TEST ===",
            f"canonical records: {result['corpus']['canonical_records']}",
            "represented retailers: "
            + ", ".join(result["corpus"]["represented_retailers"]),
            f"birra query matches: {result['query']['offer_count']}",
            f"passata offers: {result['availability']['offer_count']}",
            (
                "shopping-list resolved/unresolved: "
                f"{result['shopping_list']['resolved_item_count']}/"
                f"{result['shopping_list']['unresolved_item_count']}"
            ),
            f"AI required: {'YES' if result['ai_required'] else 'NO'}",
            f"network required: {'YES' if result['network_required'] else 'NO'}",
            f"result: {'PASS' if result['pass'] else 'FAIL'}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = run_corpus_business_road_test()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_report(result))

    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
