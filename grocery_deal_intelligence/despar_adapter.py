from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from decimal import Decimal

from grocery_deal_intelligence.despar_fixture import (
    DesparFixture,
    DesparOffer,
    parse_despar_fixture_text,
    parse_euro_price,
)

_SHA256_HEX_DIGEST_LENGTH = 64


def adapt_despar_fixture_text(
    text: str,
    *,
    observed_at: str,
    expected_sha256: str,
) -> list[dict[str, Any]]:
    """Translate one verified Despar fixture into deterministic source records.

    The adapter verifies fixture identity before parsing and maps only facts that
    are explicitly present in the fixture or deterministically implied by its
    source notation (for example, the euro currency symbol).
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(observed_at, str) or not observed_at.strip():
        raise ValueError("observed_at must be a non-empty string")
    if (
        not isinstance(expected_sha256, str)
        or len(expected_sha256) != _SHA256_HEX_DIGEST_LENGTH
    ):
        raise ValueError("expected_sha256 must be a 64-character SHA-256 hex digest")

    actual_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual_sha256 != expected_sha256.lower():
        raise ValueError("Despar fixture SHA-256 mismatch")

    fixture = parse_despar_fixture_text(text)
    return [
        _adapt_offer(
            fixture,
            offer,
            observed_at=observed_at.strip(),
            fixture_sha256=actual_sha256,
        )
        for offer in fixture.offers
    ]


def _adapt_offer(
    fixture: DesparFixture,
    offer: DesparOffer,
    *,
    observed_at: str,
    fixture_sha256: str,
) -> dict[str, Any]:
    if not offer.price_texts:
        raise ValueError("Despar offer must contain at least one price")

    price = _decimal_to_number(parse_euro_price(offer.price_texts[-1]))

    record: dict[str, Any] = {
        "retailer": "despar",
        "product_name": offer.product_name,
        "price": price,
        "currency": "EUR",
        "packaging_text": offer.package_text,
        "valid_from": fixture.valid_from,
        "valid_to": fixture.valid_to,
        "locality": {
            "scope": "store",
            "stores": [fixture.store_id],
            "store_name": fixture.store_name,
            "store_address": fixture.store_address,
            "store_locality": fixture.store_locality,
        },
        "verification": {
            "locality_status": "verified",
            "evidence_status": "verified",
        },
        "provenance": {
            "source_type": "official_store_scoped_flyer_fixture",
            "source_url": fixture.source_url,
            "observed_at": observed_at,
            "fixture_sha256": fixture_sha256,
            "campaign_title": fixture.campaign_title,
        },
    }

    if len(offer.price_texts) > 1:
        record["base_price_text"] = offer.price_texts[0]

    if offer.promotion_text is not None:
        record["discount_text"] = offer.promotion_text

    return record


def _decimal_to_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)
