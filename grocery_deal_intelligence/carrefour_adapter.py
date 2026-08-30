from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import Any

from grocery_deal_intelligence.carrefour_fixture import (
    CarrefourFixture,
    CarrefourOffer,
    parse_carrefour_fixture_text,
)

_EURO_AMOUNT = re.compile(r"€\s*([0-9]+(?:[.,][0-9]+)?)")
_CARREFOUR_MINIMUM_PRICE_EVIDENCE_COUNT = 2


def adapt_carrefour_fixture_text(
    text: str,
    *,
    observed_at: str,
    expected_sha256: str,
) -> list[dict[str, Any]]:
    """Translate one verified Carrefour fixture into deterministic source records."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(observed_at, str) or not observed_at.strip():
        raise ValueError("observed_at must be a non-empty string")
    if not isinstance(expected_sha256, str) or not re.fullmatch(
        r"[0-9a-fA-F]{64}", expected_sha256
    ):
        raise ValueError("expected_sha256 must be a 64-character SHA-256 hex digest")

    actual_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual_sha256 != expected_sha256.lower():
        raise ValueError("Carrefour fixture SHA-256 mismatch")

    fixture = parse_carrefour_fixture_text(text)
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
    fixture: CarrefourFixture,
    offer: CarrefourOffer,
    *,
    observed_at: str,
    fixture_sha256: str,
) -> dict[str, Any]:
    if not offer.price_texts:
        raise ValueError("Carrefour offer must contain price evidence")

    # The captured fixture preserves explicit source order:
    # base/original displayed price | current/promo price | unit price.
    # Canonical reference_price is the normalized numeric form of the first value.
    if len(offer.price_texts) < _CARREFOUR_MINIMUM_PRICE_EVIDENCE_COUNT:
        raise ValueError("Carrefour adapter requires explicit current price evidence")

    base_price_text = offer.price_texts[0]
    current_price_text = offer.price_texts[1]

    record: dict[str, Any] = {
        "retailer": "carrefour",
        "product_name": offer.product_name,
        "price": _decimal_to_number(_parse_euro_amount(current_price_text)),
        "currency": "EUR",
        "base_price_text": base_price_text,
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
            "flyer_id": fixture.flyer_id,
            "campaign_title": fixture.campaign_title,
        },
    }

    record["reference_price"] = _decimal_to_number(_parse_euro_amount(base_price_text))

    if offer.discount_text is not None:
        record["discount_text"] = offer.discount_text

    # The source explicitly marks SPESAMICA PAYBACK. Preserve the source wording
    # as the promotion type instead of inventing a retailer-neutral taxonomy.
    if offer.loyalty_text is not None:
        record["promotion_type"] = offer.loyalty_text
        record["requires_loyalty"] = True

    return record


def _parse_euro_amount(text: str) -> Decimal:
    match = _EURO_AMOUNT.search(text)
    if match is None:
        raise ValueError(f"Carrefour price evidence has no euro amount: {text!r}")
    return Decimal(match.group(1).replace(",", "."))


def _decimal_to_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)
