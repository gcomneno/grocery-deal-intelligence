from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

import pytest

from grocery_deal_intelligence.despar_fixture import (
    load_despar_fixture,
    parse_despar_fixture_text,
    parse_euro_price,
)


FIXTURE = Path("fixtures/despar/store-191-flyer-2026-08-13.txt")
EXPECTED_SHA256 = "54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17"


def test_fixture_hash_is_stable():
    payload = FIXTURE.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_SHA256


def test_parses_store_scope_and_campaign_metadata():
    parsed = load_despar_fixture(FIXTURE)

    assert parsed.source_url == "https://www.despar.it/it/volantino-digitale/191/"
    assert parsed.store_id == "191"
    assert parsed.store_name == "Interspar Montebelluna"
    assert parsed.store_address == "Via Schiavonesca Priula, 64"
    assert parsed.store_locality == "Montebelluna (TV)"
    assert parsed.campaign_title == "Sconti dal 20% al 50%"
    assert parsed.valid_from == "2026-08-13"
    assert parsed.valid_to == "2026-08-26"


def test_parses_real_offer_without_inventing_fields():
    parsed = load_despar_fixture(FIXTURE)
    offer = parsed.offers[0]

    assert offer.product_name == "Riso Carnaroli Scotti"
    assert offer.package_text == "1 kg"
    assert offer.price_texts == ("2,49 € al pz.",)
    assert offer.promotion_text is None
    assert parse_euro_price(offer.price_texts[0]) == Decimal("2.49")


def test_preserves_multiple_prices_and_promotion_text():
    parsed = load_despar_fixture(FIXTURE)
    offer = parsed.offers[2]

    assert offer.product_name == "Olio Extra Vergine di oliva Grezzo Il Casolare Farchioni"
    assert offer.package_text == "1 L"
    assert offer.price_texts == ("9,49 €", "7,59 € al pz.")
    assert offer.promotion_text == "Sconto extra App -20%"
    assert parse_euro_price(offer.price_texts[0]) == Decimal("9.49")
    assert parse_euro_price(offer.price_texts[1]) == Decimal("7.59")


def test_parser_is_read_only_for_source_text():
    text = FIXTURE.read_text(encoding="utf-8")
    original = text[:]

    parse_despar_fixture_text(text)

    assert text == original


def test_rejects_missing_required_metadata():
    with pytest.raises(ValueError, match="Missing Despar fixture metadata"):
        parse_despar_fixture_text("offer: Example | 1 kg | 1,00 € al pz.\n")


def test_rejects_offer_without_price():
    text = """source_url: https://example.test/
store_id: 1
store_name: Test
store_address: Test
store_locality: Test
campaign_title: Test
valid_from: 2026-01-01
valid_to: 2026-01-02
offer: Product | 1 kg
"""
    with pytest.raises(ValueError, match="product, package, and price"):
        parse_despar_fixture_text(text)
