from copy import deepcopy

import pytest

from grocery_deal_intelligence.aggregation import aggregate_offers


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
        **({"reference_price": reference_price} if reference_price is not None else {}),
        **({"base_price_text": base_price_text} if base_price_text is not None else {}),
    }


@pytest.fixture
def offers():
    return [
        make_record(
            "lidl",
            "Latte Fresco",
            1.49,
            promotion_type="lidl_plus",
            requires_loyalty=True,
            locality_scope="regional",
            reference_price=1.99,
            base_price_text="1 kg = 2.98 €",
        ),
        make_record(
            "esselunga",
            "Ananas",
            4.88,
            promotion_type="Sconto %",
            locality_scope="store",
        ),
        make_record(
            "lidl",
            "Pasta",
            0.99,
            promotion_type="lidl_plus",
            requires_loyalty=True,
            locality_status="unknown",
            evidence_status="partial",
        ),
        make_record(
            "esselunga",
            "Latte Intero",
            1.59,
        ),
    ]


def test_aggregate_by_retailer(offers):
    assert aggregate_offers(offers, dimension="retailer") == {
        "dimension": "retailer",
        "groups": {
            "esselunga": 2,
            "lidl": 2,
        },
    }


def test_aggregate_by_currency(offers):
    assert aggregate_offers(offers, dimension="currency") == {
        "dimension": "currency",
        "groups": {
            "EUR": 4,
        },
    }


def test_aggregate_by_promotion_type(offers):
    assert aggregate_offers(offers, dimension="promotion.type") == {
        "dimension": "promotion.type",
        "groups": {
            "Sconto %": 1,
            "lidl_plus": 2,
            "test": 1,
        },
    }


def test_aggregate_by_loyalty_requirement(offers):
    assert aggregate_offers(
        offers,
        dimension="promotion.requires_loyalty",
    ) == {
        "dimension": "promotion.requires_loyalty",
        "groups": {
            False: 2,
            True: 2,
        },
    }


def test_aggregate_by_locality_scope(offers):
    assert aggregate_offers(
        offers,
        dimension="locality.scope",
    ) == {
        "dimension": "locality.scope",
        "groups": {
            "national": 2,
            "regional": 1,
            "store": 1,
        },
    }


def test_aggregate_by_locality_verification_status(offers):
    assert aggregate_offers(
        offers,
        dimension="verification.locality_status",
    ) == {
        "dimension": "verification.locality_status",
        "groups": {
            "unknown": 1,
            "verified": 3,
        },
    }


def test_aggregate_by_evidence_verification_status(offers):
    assert aggregate_offers(
        offers,
        dimension="verification.evidence_status",
    ) == {
        "dimension": "verification.evidence_status",
        "groups": {
            "partial": 1,
            "verified": 3,
        },
    }


def test_aggregate_reference_price_presence(offers):
    assert aggregate_offers(
        offers,
        dimension="reference_price",
    ) == {
        "dimension": "reference_price",
        "groups": {
            "absent": 3,
            "present": 1,
        },
    }


def test_aggregate_base_price_text_presence(offers):
    assert aggregate_offers(
        offers,
        dimension="base_price_text",
    ) == {
        "dimension": "base_price_text",
        "groups": {
            "absent": 3,
            "present": 1,
        },
    }


def test_empty_dataset_produces_empty_groups():
    assert aggregate_offers([], dimension="retailer") == {
        "dimension": "retailer",
        "groups": {},
    }


def test_source_order_does_not_affect_result(offers):
    forward = aggregate_offers(offers, dimension="retailer")
    reverse = aggregate_offers(
        list(reversed(offers)),
        dimension="retailer",
    )

    assert forward == reverse


def test_duplicate_records_are_preserved_as_separate_counts():
    record = make_record("lidl", "Pasta", 0.99)

    assert aggregate_offers(
        [record, deepcopy(record)],
        dimension="retailer",
    ) == {
        "dimension": "retailer",
        "groups": {
            "lidl": 2,
        },
    }


def test_aggregation_does_not_mutate_source_dataset(offers):
    original = deepcopy(offers)

    aggregate_offers(offers, dimension="retailer")

    assert offers == original


def test_unknown_dimension_is_rejected():
    with pytest.raises(ValueError, match="unsupported aggregation dimension: price"):
        aggregate_offers(
            offers,
            dimension="price",
        )


def test_missing_dimension_argument_is_rejected():
    with pytest.raises(TypeError):
        aggregate_offers(offers)


def test_temporal_dimension_is_not_supported():
    with pytest.raises(
        ValueError, match=r"unsupported aggregation dimension: validity\.from"
    ):
        aggregate_offers(
            offers,
            dimension="validity.from",
        )
