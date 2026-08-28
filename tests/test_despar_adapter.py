from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from grocery_deal_intelligence.despar_adapter import adapt_despar_fixture_text
from grocery_deal_intelligence.source_evidence import (
    SUPPORTED,
    project_source_evidence,
    verify_candidate_claims,
)
from grocery_deal_intelligence.validation import validate_offers


FIXTURE = Path("fixtures/despar/store-191-flyer-2026-08-13.txt")
EXPECTED_SHA256 = "54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17"
OBSERVED_AT = "2026-08-27T00:00:00Z"


def _records():
    return adapt_despar_fixture_text(
        FIXTURE.read_text(encoding="utf-8"),
        observed_at=OBSERVED_AT,
        expected_sha256=EXPECTED_SHA256,
    )


def test_maps_store_scoped_offer_without_inventing_promotion_semantics():
    record = _records()[0]

    assert record["retailer"] == "despar"
    assert record["product_name"] == "Riso Carnaroli Scotti"
    assert record["price"] == 2.49
    assert record["currency"] == "EUR"
    assert record["packaging_text"] == "1 kg"
    assert record["valid_from"] == "2026-08-13"
    assert record["valid_to"] == "2026-08-26"
    assert record["locality"] == {
        "scope": "store",
        "stores": ["191"],
        "store_name": "Interspar Montebelluna",
        "store_address": "Via Schiavonesca Priula, 64",
        "store_locality": "Montebelluna (TV)",
    }
    assert record["verification"] == {
        "locality_status": "verified",
        "evidence_status": "verified",
    }
    assert "promotion_type" not in record
    assert "requires_loyalty" not in record
    assert "discount_text" not in record


def test_maps_explicit_previous_current_price_and_promotion_text_only():
    record = _records()[2]

    assert record["price"] == 7.59
    assert record["reference_price"] == 9.49
    assert record["base_price_text"] == "9,49 €"
    assert record["discount_text"] == "Sconto extra App -20%"
    assert "promotion_type" not in record
    assert "requires_loyalty" not in record


def test_preserves_provenance_and_verified_fixture_identity():
    record = _records()[0]

    assert record["provenance"] == {
        "source_type": "official_store_scoped_flyer_fixture",
        "source_url": "https://www.despar.it/it/volantino-digitale/191/",
        "observed_at": OBSERVED_AT,
        "fixture_sha256": EXPECTED_SHA256,
        "campaign_title": "Sconti dal 20% al 50%",
    }


def test_rejects_fixture_hash_mismatch_before_mapping():
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        adapt_despar_fixture_text(
            FIXTURE.read_text(encoding="utf-8"),
            observed_at=OBSERVED_AT,
            expected_sha256="0" * 64,
        )


def test_rejects_missing_observation_metadata():
    with pytest.raises(ValueError, match="observed_at"):
        adapt_despar_fixture_text(
            FIXTURE.read_text(encoding="utf-8"),
            observed_at="",
            expected_sha256=EXPECTED_SHA256,
        )


def test_adapter_does_not_mutate_source_text():
    text = FIXTURE.read_text(encoding="utf-8")
    original = text[:]

    adapt_despar_fixture_text(
        text,
        observed_at=OBSERVED_AT,
        expected_sha256=EXPECTED_SHA256,
    )

    assert text == original


def test_fixture_to_evidence_projection_is_supported_and_validation_fails_closed():
    source_record = _records()[2]
    source_before = deepcopy(source_record)
    evidence = project_source_evidence(source_record, retailer="despar")

    assert evidence["retailer"] == "despar"
    assert evidence["product_name"] == source_record["product_name"]
    assert evidence["price"] == 7.59
    assert evidence["reference_price"] == 9.49
    assert evidence["promotion"] == {"discount_text": "Sconto extra App -20%"}
    assert evidence["validity"] == {
        "from": "2026-08-13",
        "to": "2026-08-26",
    }
    assert evidence["locality"]["scope"] == "store"
    assert evidence["locality"]["stores"] == ["191"]
    assert evidence["provenance"]["fixture_sha256"] == EXPECTED_SHA256

    supported_candidate = {
        "retailer": evidence["retailer"],
        "product_name": evidence["product_name"],
        "price": evidence["price"],
        "currency": evidence["currency"],
        "reference_price": evidence["reference_price"],
        "packaging_text": evidence["packaging_text"],
        "base_price_text": evidence["base_price_text"],
        "promotion": deepcopy(evidence["promotion"]),
        "validity": deepcopy(evidence["validity"]),
        "locality": deepcopy(evidence["locality"]),
        "verification": deepcopy(evidence["verification"]),
        "provenance": deepcopy(evidence["provenance"]),
    }
    verification = verify_candidate_claims(supported_candidate, evidence)
    assert verification
    assert all(item["status"] == SUPPORTED for item in verification)

    structural = validate_offers([supported_candidate])
    assert structural["valid"] is False
    assert source_record == source_before
