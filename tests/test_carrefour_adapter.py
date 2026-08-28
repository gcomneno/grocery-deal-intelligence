from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from grocery_deal_intelligence.admission import evaluate_canonical_admission
from grocery_deal_intelligence.carrefour_adapter import adapt_carrefour_fixture_text
from grocery_deal_intelligence.source_evidence import (
    SUPPORTED,
    project_source_evidence,
    verify_candidate_claims,
)
from grocery_deal_intelligence.validation import validate_offers


FIXTURE = Path("fixtures/carrefour/store-5190-flyer-56879.txt")
EXPECTED_SHA256 = "25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571"
OBSERVED_AT = "2026-08-27T00:00:00Z"


def _records():
    return adapt_carrefour_fixture_text(
        FIXTURE.read_text(encoding="utf-8"),
        observed_at=OBSERVED_AT,
        expected_sha256=EXPECTED_SHA256,
    )


def test_maps_explicit_current_base_unit_and_loyalty_semantics():
    record = _records()[0]

    assert record["retailer"] == "carrefour"
    assert record["product_name"] == "Brescia Latte UHT Centrale Brescia Parzialmente Scremato 1 l"
    assert record["price"] == 1.09
    assert record["reference_price"] == 1.09
    assert record["base_price_text"] == "€1,57"
    assert record["currency"] == "EUR"
    assert record["discount_text"] == "-30%"
    assert record["promotion_type"] == "SPESAMICA PAYBACK"
    assert record["requires_loyalty"] is True


def test_preserves_store_flyer_campaign_and_fixture_provenance():
    record = _records()[0]

    assert record["locality"] == {
        "scope": "store",
        "stores": ["5190"],
        "store_name": "Carrefour Express",
        "store_address": "Viale Abruzzi, 54",
        "store_locality": "Milano",
    }
    assert record["provenance"] == {
        "source_type": "official_store_scoped_flyer_fixture",
        "source_url": (
            "https://www.carrefour.it/volantino/"
            "supermercato-carrefour-express-milano-viale-abruzzi-54/5190/"
            "-volantino-supermercato-carrefour-express-milano-viale-abruzzi-54-"
            "5190-offerte-d-estate-carrefour-express-56879-carrefour-express/56879"
        ),
        "observed_at": OBSERVED_AT,
        "fixture_sha256": EXPECTED_SHA256,
        "flyer_id": "56879",
        "campaign_title": "Offerte d'estate",
    }


def test_rejects_hash_mismatch_before_mapping():
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        adapt_carrefour_fixture_text(
            FIXTURE.read_text(encoding="utf-8"),
            observed_at=OBSERVED_AT,
            expected_sha256="0" * 64,
        )


def test_rejects_missing_observation_timestamp():
    with pytest.raises(ValueError, match="observed_at"):
        adapt_carrefour_fixture_text(
            FIXTURE.read_text(encoding="utf-8"),
            observed_at="",
            expected_sha256=EXPECTED_SHA256,
        )


def test_rejects_offer_without_explicit_current_price_role():
    text = """source_url: https://example.test/
store_id: 1
flyer_id: 2
store_name: Test
store_address: Test
store_locality: Test
campaign_title: Test
valid_from: 2026-01-01
valid_to: 2026-01-02
offer: Product | €1,00
"""
    import hashlib

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    with pytest.raises(ValueError, match="explicit current price evidence"):
        adapt_carrefour_fixture_text(
            text,
            observed_at=OBSERVED_AT,
            expected_sha256=digest,
        )


def test_adapter_is_read_only_for_source_text():
    text = FIXTURE.read_text(encoding="utf-8")
    before = text[:]

    adapt_carrefour_fixture_text(
        text,
        observed_at=OBSERVED_AT,
        expected_sha256=EXPECTED_SHA256,
    )

    assert text == before


def test_fixture_to_evidence_to_admission_is_fully_deterministic():
    source_record = _records()[0]
    source_before = deepcopy(source_record)
    evidence = project_source_evidence(source_record, retailer="carrefour")

    assert evidence["promotion"] == {
        "type": "SPESAMICA PAYBACK",
        "requires_loyalty": True,
        "discount_text": "-30%",
    }
    assert evidence["price"] == 1.09
    assert evidence["reference_price"] == 1.09
    assert evidence["base_price_text"] == "€1,57"
    assert evidence["validity"] == {"from": "2026-08-03", "to": "2026-08-31"}
    assert evidence["locality"]["stores"] == ["5190"]
    assert evidence["provenance"]["flyer_id"] == "56879"

    candidate = {
        "retailer": evidence["retailer"],
        "product_name": evidence["product_name"],
        "price": evidence["price"],
        "currency": evidence["currency"],
        "reference_price": evidence["reference_price"],
        "base_price_text": evidence["base_price_text"],
        "promotion": deepcopy(evidence["promotion"]),
        "validity": deepcopy(evidence["validity"]),
        "locality": deepcopy(evidence["locality"]),
        "verification": deepcopy(evidence["verification"]),
        "provenance": deepcopy(evidence["provenance"]),
    }

    verification = verify_candidate_claims(candidate, evidence)
    assert verification
    assert all(item["status"] == SUPPORTED for item in verification)

    structural = validate_offers([candidate])
    assert structural["valid"] is True

    admission = evaluate_canonical_admission(
        structurally_valid=True,
        claim_verification=verification,
    )
    assert admission["eligible"] is True
    assert admission["reasons"] == []
    assert source_record == source_before
