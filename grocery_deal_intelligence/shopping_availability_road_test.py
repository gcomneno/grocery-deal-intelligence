from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from grocery_deal_intelligence.shopping_availability import (
    AVAILABLE,
    NOT_CURRENT,
    PRODUCT_FAMILY_MISMATCH,
    UNKNOWN,
    resolve_shopping_item_availability,
)
from grocery_deal_intelligence.validation import validate_offers

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE_PATH = (
    _REPO_ROOT / "esselunga/data/output/esselunga-porcari-current-retailer-neutral.json"
)
_FIXTURE_ID = "esselunga/data/output/esselunga-porcari-current-retailer-neutral.json"
_FIXTURE_SHA256 = "2f4d9ad9015490f326cc95ba17243b9889b2a8f83caea224d3e2769552b5c717"

_PRODUCT_FAMILY = "dark_chocolate"
_LOCALITY_SCOPE = "store"
_STORES = ("ARI",)

_HISTORICAL_AS_OF = "2026-08-25"
_CURRENT_AS_OF = "2026-08-29"
_QUESTION = "Where can I buy dark chocolate, and how much does it cost?"

_HISTORICAL_SINGLETON_NAMES = ("Vanini fondente 95% 90 g",)

_CURRENT_GENUINE_DARK_CHOCOLATE_NAMES = (
    "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
    "Vanini fondente 91% 90 g",
    "Vanini fondente assoluto 100% 90 g",
    "Vanini fondente 95% 90 g",
)

_CURRENT_WRONG_FAMILY_NAMES = (
    "FITNESS Cioccolato Fondente Cereali Integrali con Fiocchi al Cioccolato 325g",
    (
        "NUII Mini Adventure Caramello Salato e Noci Macadamia e "
        "Cioccolato Fondente e Mirtilli 6 Gelati 253g"
    ),
)

_FORBIDDEN_COMPARATIVE_KEYS = frozenset(
    {
        "ranking",
        "winner",
        "cheapest",
        "recommendation",
        "semantic_comparison",
        "economic_normalization",
        "price_comparison",
        "comparison",
    }
)


def run_shopping_availability_road_test() -> dict[str, Any]:
    """Run the deterministic shopping-availability road test."""
    fixture_records = _load_fixture_records()

    historical_records = _selected_records(
        fixture_records,
        _HISTORICAL_SINGLETON_NAMES,
    )
    current_records = _selected_records(
        fixture_records,
        (
            *_CURRENT_GENUINE_DARK_CHOCOLATE_NAMES,
            *_CURRENT_WRONG_FAMILY_NAMES,
        ),
    )

    historical_validation = _validate_selected_records(historical_records)
    current_validation = _validate_selected_records(current_records)

    historical_availability = resolve_shopping_item_availability(
        historical_records,
        product_family=_PRODUCT_FAMILY,
        as_of=_HISTORICAL_AS_OF,
        locality_scope=_LOCALITY_SCOPE,
        stores=_STORES,
    )
    current_availability = resolve_shopping_item_availability(
        current_records,
        product_family=_PRODUCT_FAMILY,
        as_of=_CURRENT_AS_OF,
        locality_scope=_LOCALITY_SCOPE,
        stores=_STORES,
    )

    historical_pass = _historical_singleton_pass(
        historical_availability,
        historical_validation,
    )
    current_pass = _current_availability_pass(
        current_availability,
        current_validation,
    )

    return {
        "pass": historical_pass and current_pass,
        "question": _QUESTION,
        "final": UNKNOWN,
        "authorized_stopping_boundary": "availability",
        "network_required": False,
        "ai_required": False,
        "fixture": {
            "path": _FIXTURE_ID,
            "sha256": _FIXTURE_SHA256,
            "record_count": len(fixture_records),
        },
        "historical_singleton_probe": {
            "pass": historical_pass,
            "purpose": "historical_contract_probe_not_current_availability_claim",
            "cardinality_contract": "1_eligible_where_price",
            "as_of": _HISTORICAL_AS_OF,
            "selected_product_names": list(_HISTORICAL_SINGLETON_NAMES),
            "structural_validation": historical_validation,
            "availability": historical_availability,
        },
        "current_availability": {
            "pass": current_pass,
            "question": _QUESTION,
            "cardinality_contract": "0_eligible_unknown",
            "as_of": _CURRENT_AS_OF,
            "selected_product_names": [
                *_CURRENT_GENUINE_DARK_CHOCOLATE_NAMES,
                *_CURRENT_WRONG_FAMILY_NAMES,
            ],
            "genuine_dark_chocolate_names": list(_CURRENT_GENUINE_DARK_CHOCOLATE_NAMES),
            "wrong_family_names": list(_CURRENT_WRONG_FAMILY_NAMES),
            "structural_validation": current_validation,
            "availability": current_availability,
            "final": UNKNOWN,
        },
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
        matches = [record for record in records if record.get("product_name") == name]
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


def _historical_singleton_pass(
    availability: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> bool:
    if validation.get("valid") is not True:
        return False
    if availability.get("status") != AVAILABLE:
        return False
    if availability.get("offer_count") != 1:
        return False
    offers = availability.get("offers")
    if not isinstance(offers, list) or len(offers) != 1:
        return False
    offer = offers[0]
    return (
        offer.get("retailer") == "esselunga"
        and offer.get("price") == 2.19
        and offer.get("currency") == "EUR"
        and offer.get("locality")
        == {
            "scope": "store",
            "stores": ["ARI"],
        }
        and isinstance(offer.get("provenance"), Mapping)
        and offer["provenance"].get("store_code") == "ARI"
        and not _contains_forbidden_comparative_key(availability)
    )


def _current_availability_pass(
    availability: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> bool:
    if validation.get("valid") is not True:
        return False
    if availability.get("status") != UNKNOWN:
        return False
    if availability.get("offer_count") != 0:
        return False
    if availability.get("offers") != []:
        return False

    rejections = availability.get("rejections")
    if not isinstance(rejections, list):
        return False

    reasons_by_product = {
        rejection.get("product_name"): rejection.get("code") for rejection in rejections
    }
    expected = {
        **dict.fromkeys(_CURRENT_GENUINE_DARK_CHOCOLATE_NAMES, NOT_CURRENT),
        **dict.fromkeys(_CURRENT_WRONG_FAMILY_NAMES, PRODUCT_FAMILY_MISMATCH),
    }

    return reasons_by_product == expected and not _contains_forbidden_comparative_key(
        availability
    )


def _contains_forbidden_comparative_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in _FORBIDDEN_COMPARATIVE_KEYS:
                return True
            if _contains_forbidden_comparative_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_comparative_key(child) for child in value)

    return False


def render_report(result: Mapping[str, Any]) -> str:
    historical = result["historical_singleton_probe"]
    current = result["current_availability"]

    return "\n".join(
        [
            "Shopping availability road test",
            (f"historical singleton probe: {'PASS' if historical['pass'] else 'FAIL'}"),
            (
                "historical eligible offers: "
                f"{historical['availability']['offer_count']}"
            ),
            (f"current availability: {str(current['final']).upper()}"),
            (f"current eligible offers: {current['availability']['offer_count']}"),
            (f"business/road test: {'PASS' if result['pass'] else 'FAIL'}"),
            (f"network required: {'YES' if result['network_required'] else 'NO'}"),
            (f"AI required: {'YES' if result['ai_required'] else 'NO'}"),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic shopping availability road test."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    args = parser.parse_args(argv)

    result = run_shopping_availability_road_test()

    if args.json:
        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
        )
    else:
        print(render_report(result))

    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
