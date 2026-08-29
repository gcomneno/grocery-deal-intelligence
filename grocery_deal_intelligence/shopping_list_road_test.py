from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from collections.abc import Mapping

from grocery_deal_intelligence.shopping_list import (
    LOWEST_PRICE,
    NO_ELIGIBLE_OFFERS,
    SELECTION_SINGLETON,
    SELECTION_UNSELECTED,
    resolve_shopping_list,
)
from grocery_deal_intelligence.validation import validate_offers


_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE_PATH = (
    _REPO_ROOT
    / "esselunga/data/output/esselunga-porcari-current-retailer-neutral.json"
)
_FIXTURE_ID = "esselunga/data/output/esselunga-porcari-current-retailer-neutral.json"
_FIXTURE_SHA256 = (
    "2f4d9ad9015490f326cc95ba17243b9889b2a8f83caea224d3e2769552b5c717"
)

_AS_OF = "2026-08-25"
_LOCALITY_SCOPE = "store"
_STORES = ("ARI",)
_SINGLETON_PRODUCT_NAME = "Vanini fondente 95% 90 g"
_ITEMS = (
    {
        "id": "caller-dark-chocolate",
        "product_family": "dark_chocolate",
        "selection_policy": LOWEST_PRICE,
    },
    {
        "id": "caller-whole-milk",
        "product_family": "whole_milk",
        "selection_policy": LOWEST_PRICE,
    },
)


def run_shopping_list_road_test() -> dict[str, Any]:
    fixture_records = _load_fixture_records()
    records = _selected_records(fixture_records, (_SINGLETON_PRODUCT_NAME,))
    structural_validation = _validate_selected_records(records)

    result = resolve_shopping_list(
        records,
        items=_ITEMS,
        as_of=_AS_OF,
        locality_scope=_LOCALITY_SCOPE,
        stores=_STORES,
    )

    passed = (
        structural_validation.get("valid") is True
        and result["requested_item_count"] == 2
        and result["resolved_item_count"] == 1
        and result["unresolved_item_count"] == 1
        and result["singleton_item_count"] == 1
        and result["selected_item_count"] == 0
        and result["unselected_item_count"] == 1
        and [item["id"] for item in result["items"]]
        == ["caller-dark-chocolate", "caller-whole-milk"]
        and result["items"][0]["selection"]["status"] == SELECTION_SINGLETON
        and result["items"][0]["selection"]["comparative_claim"] is None
        and result["items"][1]["availability"]["status"] == "unknown"
        and result["items"][1]["selection"]["status"] == SELECTION_UNSELECTED
        and result["items"][1]["selection"]["reason"] == {
            "code": NO_ELIGIBLE_OFFERS
        }
        and _provenance_is_inspectable(result)
    )

    return {
        "pass": passed,
        "network_required": False,
        "ai_required": False,
        "fixture": {
            "path": _FIXTURE_ID,
            "sha256": _FIXTURE_SHA256,
            "record_count": len(fixture_records),
        },
        "selected_product_names": [_SINGLETON_PRODUCT_NAME],
        "structural_validation": structural_validation,
        "result": result,
    }


def _load_fixture_records() -> list[dict[str, Any]]:
    raw = _FIXTURE_PATH.read_bytes()
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_sha256 != _FIXTURE_SHA256:
        raise ValueError(
            "Esselunga fixture SHA-256 mismatch: "
            f"expected {_FIXTURE_SHA256}, got {observed_sha256}"
        )

    records = json.loads(raw.decode("utf-8"))
    if not isinstance(records, list):
        raise ValueError("Esselunga retailer-neutral fixture must be a list")

    return deepcopy(records)


def _selected_records(
    records: list[Mapping[str, Any]],
    names: tuple[str, ...],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for name in names:
        matches = [
            record
            for record in records
            if record.get("product_name") == name
        ]
        if len(matches) != 1:
            raise ValueError(
                f"expected exactly one Esselunga fixture record for {name!r}"
            )
        selected.append(deepcopy(dict(matches[0])))
    return selected


def _validate_selected_records(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    validation = validate_offers(records)
    if validation["valid"] is not True:
        raise ValueError(
            "selected Esselunga records failed canonical structural validation"
        )
    return deepcopy(validation)


def _provenance_is_inspectable(result: Mapping[str, Any]) -> bool:
    first = result["items"][0]["selection"]["sole_offer"]
    provenance = first.get("provenance")
    return (
        isinstance(provenance, Mapping)
        and provenance.get("source_type") == "retailer_api"
        and provenance.get("store_code") == "ARI"
        and provenance.get("campaign_id") == "8260"
        and provenance.get("observed_at") == "2026-08-25T17:18:07Z"
    )


def render_report(result: Mapping[str, Any]) -> str:
    shopping_list = result["result"]
    return "\n".join(
        [
            "Shopping list road test",
            (
                "requested items: "
                f"{shopping_list['requested_item_count']}"
            ),
            (
                "resolved items: "
                f"{shopping_list['resolved_item_count']}"
            ),
            (
                "unresolved items: "
                f"{shopping_list['unresolved_item_count']}"
            ),
            (
                "business/road test: "
                f"{'PASS' if result['pass'] else 'FAIL'}"
            ),
            (
                "network required: "
                f"{'YES' if result['network_required'] else 'NO'}"
            ),
            (
                "AI required: "
                f"{'YES' if result['ai_required'] else 'NO'}"
            ),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = run_shopping_list_road_test()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_report(result))

    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
