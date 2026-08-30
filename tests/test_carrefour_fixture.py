import hashlib
from pathlib import Path

import pytest

from grocery_deal_intelligence.carrefour_fixture import (
    load_carrefour_fixture,
    parse_carrefour_fixture_text,
)

FIXTURE = Path("fixtures/carrefour/store-5190-flyer-56879.txt")
EXPECTED_SHA256 = "25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571"


def test_fixture_identity_is_stable():
    payload = FIXTURE.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_SHA256


def test_parse_store_scoped_metadata_and_offers():
    parsed = load_carrefour_fixture(FIXTURE)

    assert parsed.store_id == "5190"
    assert parsed.flyer_id == "56879"
    assert parsed.store_name == "Carrefour Express"
    assert parsed.store_address == "Viale Abruzzi, 54"
    assert parsed.store_locality == "Milano"
    assert parsed.valid_from == "2026-08-03"
    assert parsed.valid_to == "2026-08-31"
    assert len(parsed.offers) == 3


def test_parse_loyalty_discount_and_price_evidence():
    parsed = load_carrefour_fixture(FIXTURE)
    offer = parsed.offers[0]

    assert (
        offer.product_name
        == "Brescia Latte UHT Centrale Brescia Parzialmente Scremato 1 l"
    )
    assert offer.discount_text == "-30%"
    assert offer.loyalty_text == "SPESAMICA PAYBACK"
    assert offer.price_texts == ("€1,57", "€1,09", "€1,09 al Lt")

    assert [offer.price_texts[2] for offer in parsed.offers] == [
        "€1,09 al Lt",
        "€2,10 al Kg",
        "€2,52 al Lt",
    ]


def test_parse_is_deterministic_and_read_only():
    text = FIXTURE.read_text(encoding="utf-8")
    before = text[:]

    first = parse_carrefour_fixture_text(text)
    second = parse_carrefour_fixture_text(text)

    assert first == second
    assert text == before


def test_missing_required_metadata_is_rejected():
    text = FIXTURE.read_text(encoding="utf-8").replace("store_id: 5190\n", "")
    with pytest.raises(ValueError, match="Missing Carrefour fixture metadata"):
        parse_carrefour_fixture_text(text)


def test_malformed_offer_is_rejected():
    text = """source_url: x
store_id: 1
flyer_id: 2
store_name: x
store_address: x
store_locality: x
campaign_title: x
valid_from: 2026-08-01
valid_to: 2026-08-02
offer: product only
"""
    with pytest.raises(ValueError, match="must contain product and price evidence"):
        parse_carrefour_fixture_text(text)
