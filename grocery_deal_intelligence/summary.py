from collections.abc import Mapping, Sequence
from typing import Any


def summarize_offers(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total_offers = len(records)

    retailers = sorted({record["retailer"] for record in records})
    currencies = sorted({record["currency"] for record in records})

    offers_by_retailer = {}
    promotion_types = {}
    locality_scopes = {}
    locality_verification_status = {}
    evidence_verification_status = {}

    prices = []
    loyalty_required_offers = 0
    offers_with_reference_price = 0
    offers_with_base_price_text = 0

    for record in records:
        retailer = record["retailer"]
        offers_by_retailer[retailer] = offers_by_retailer.get(retailer, 0) + 1

        prices.append(record["price"])

        promotion_type = record["promotion"]["type"]
        promotion_types[promotion_type] = promotion_types.get(promotion_type, 0) + 1

        if record["promotion"]["requires_loyalty"]:
            loyalty_required_offers += 1

        locality_scope = record["locality"]["scope"]
        locality_scopes[locality_scope] = locality_scopes.get(locality_scope, 0) + 1

        locality_status = record["verification"]["locality_status"]
        locality_verification_status[locality_status] = (
            locality_verification_status.get(locality_status, 0) + 1
        )

        evidence_status = record["verification"]["evidence_status"]
        evidence_verification_status[evidence_status] = (
            evidence_verification_status.get(evidence_status, 0) + 1
        )

        if record.get("reference_price") is not None:
            offers_with_reference_price += 1

        if record.get("base_price_text") is not None:
            offers_with_base_price_text += 1

    return {
        "total_offers": total_offers,
        "retailers": retailers,
        "offers_by_retailer": dict(sorted(offers_by_retailer.items())),
        "currencies": currencies,
        "minimum_price": min(prices) if prices else None,
        "maximum_price": max(prices) if prices else None,
        "promotion_types": dict(sorted(promotion_types.items())),
        "loyalty_required_offers": loyalty_required_offers,
        "locality_scopes": dict(sorted(locality_scopes.items())),
        "locality_verification_status": dict(
            sorted(locality_verification_status.items())
        ),
        "evidence_verification_status": dict(
            sorted(evidence_verification_status.items())
        ),
        "offers_with_reference_price": offers_with_reference_price,
        "offers_with_base_price_text": offers_with_base_price_text,
    }
