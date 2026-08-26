from copy import deepcopy

import pytest

from grocery_deal_intelligence.profiling import profile_offers


def make_record(
    retailer,
    product_name,
    price,
    *,
    currency="EUR",
    promotion_type="test",
    requires_loyalty=False,
    locality_scope="national",
    locality_status="verified",
    evidence_status="verified",
    reference_price=None,
    base_price_text=None,
):
    return {
        "retailer": retailer,
        "product_name": product_name,
        "price": price,
        "currency": currency,
        "reference_price": reference_price,
        "base_price_text": base_price_text,
        "promotion": {
            "type": promotion_type,
            "requires_loyalty": requires_loyalty,
        },
        "validity": {
            "from": "2026-08-01T00:00:00Z",
            "to": "2026-08-31T23:59:59Z",
        },
        "locality": {
            "scope": locality_scope,
            "stores": [],
        },
        "verification": {
            "locality_status": locality_status,
            "evidence_status": evidence_status,
        },
        "provenance": {
            "source_type": "test",
            "source_url": "https://example.test/offer",
            "observed_at": "2026-08-26T00:00:00Z",
        },
    }


@pytest.fixture
def offers():
    return [
        make_record(
            "lidl",
            "Latte Fresco",
            1.49,
            promotion_type="discount",
            requires_loyalty=True,
            locality_scope="regional",
        ),
        make_record(
            "esselunga",
            "Ananas",
            4.88,
            promotion_type="multibuy",
            locality_scope="store",
            reference_price=5.49,
            base_price_text="5.49 EUR",
        ),
        make_record(
            "lidl",
            "Pasta",
            0.99,
            promotion_type="discount",
            requires_loyalty=True,
            locality_status="unknown",
            evidence_status="partial",
            base_price_text="1.29 EUR",
        ),
        make_record(
            "esselunga",
            "Latte Intero",
            1.59,
        ),
    ]


def test_profile_contains_total_record_count_and_all_dimensions(offers):
    result = profile_offers(offers)

    assert result["total_records"] == 4

    assert result["retailers"] == {
        "esselunga": 2,
        "lidl": 2,
    }

    assert result["currencies"] == {
        "EUR": 4,
    }

    assert result["promotion_types"] == {
        "discount": 2,
        "multibuy": 1,
        "test": 1,
    }

    assert result["loyalty_distribution"] == {
        False: 2,
        True: 2,
    }

    assert result["locality_scope_distribution"] == {
        "national": 2,
        "regional": 1,
        "store": 1,
    }

    assert result["locality_verification_distribution"] == {
        "unknown": 1,
        "verified": 3,
    }

    assert result["evidence_verification_distribution"] == {
        "partial": 1,
        "verified": 3,
    }

    assert result["reference_price_presence"] == {
        "absent": 3,
        "present": 1,
    }

    assert result["base_price_text_presence"] == {
        "absent": 2,
        "present": 2,
    }


def test_profile_preserves_record_count_in_every_distribution(offers):
    result = profile_offers(offers)

    distributions = (
        result["retailers"],
        result["currencies"],
        result["promotion_types"],
        result["loyalty_distribution"],
        result["locality_scope_distribution"],
        result["locality_verification_distribution"],
        result["evidence_verification_distribution"],
        result["reference_price_presence"],
        result["base_price_text_presence"],
    )

    assert all(
        sum(distribution.values()) == result["total_records"]
        for distribution in distributions
    )


def test_profile_is_deterministic(offers):
    assert profile_offers(offers) == profile_offers(offers)


def test_source_order_does_not_affect_profile(offers):
    forward = profile_offers(offers)
    reverse = profile_offers(list(reversed(offers)))

    assert forward == reverse


def test_profiling_does_not_mutate_source_dataset(offers):
    original = deepcopy(offers)

    profile_offers(offers)

    assert offers == original


def test_empty_dataset_has_zero_count_and_empty_distributions():
    result = profile_offers([])

    assert result == {
        "total_records": 0,
        "retailers": {},
        "currencies": {},
        "promotion_types": {},
        "loyalty_distribution": {},
        "locality_scope_distribution": {},
        "locality_verification_distribution": {},
        "evidence_verification_distribution": {},
        "reference_price_presence": {},
        "base_price_text_presence": {},
    }


def test_profile_uses_presence_not_truthiness_for_optional_values():
    record = make_record(
        "lidl",
        "Test",
        1.00,
        reference_price=0,
        base_price_text="",
    )

    result = profile_offers([record])

    assert result["reference_price_presence"] == {"present": 1}
    assert result["base_price_text_presence"] == {"present": 1}


def test_profile_does_not_interpret_temporal_validity():
    with pytest.raises(TypeError):
        profile_offers(
            [make_record("lidl", "Test", 1.00)],
            active_at="2026-08-26T12:00:00Z",
        )
