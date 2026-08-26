from copy import deepcopy

import pytest

from grocery_deal_intelligence.filtering import filter_offers


def make_record(
    retailer,
    product_name,
    price,
    *,
    locality_scope="national",
    locality_status="verified",
    evidence_status="verified",
    requires_loyalty=False,
):
    return {
        "retailer": retailer,
        "product_name": product_name,
        "price": price,
        "currency": "EUR",
        "promotion": {
            "type": "test",
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
            locality_scope="regional",
            requires_loyalty=True,
        ),
        make_record(
            "esselunga",
            "Ananas",
            4.88,
            locality_scope="store",
        ),
        make_record(
            "lidl",
            "Pasta",
            0.99,
            locality_status="unknown",
            evidence_status="partial",
            requires_loyalty=True,
        ),
        make_record(
            "esselunga",
            "Latte Intero",
            1.59,
            locality_scope="national",
        ),
    ]


def test_without_filters_returns_all_records_in_deterministic_order(offers):
    results = filter_offers(offers)

    assert [
        (record["retailer"], record["product_name"])
        for record in results
    ] == [
        ("esselunga", "Ananas"),
        ("esselunga", "Latte Intero"),
        ("lidl", "Latte Fresco"),
        ("lidl", "Pasta"),
    ]


def test_retailer_filter_is_exact_and_case_sensitive(offers):
    assert [
        record["product_name"]
        for record in filter_offers(offers, retailer="lidl")
    ] == ["Latte Fresco", "Pasta"]

    assert filter_offers(offers, retailer="LIDL") == []


def test_locality_scope_filter_is_exact(offers):
    results = filter_offers(offers, locality_scope="regional")

    assert [record["product_name"] for record in results] == [
        "Latte Fresco"
    ]


def test_locality_verification_status_filter_is_exact(offers):
    results = filter_offers(
        offers,
        locality_status="unknown",
    )

    assert [record["product_name"] for record in results] == ["Pasta"]


def test_evidence_verification_status_filter_is_exact(offers):
    results = filter_offers(
        offers,
        evidence_status="partial",
    )

    assert [record["product_name"] for record in results] == ["Pasta"]


def test_loyalty_filter_is_exact_boolean_filter(offers):
    results = filter_offers(
        offers,
        requires_loyalty=True,
    )

    assert [record["product_name"] for record in results] == [
        "Latte Fresco",
        "Pasta",
    ]

    assert [
        record["product_name"]
        for record in filter_offers(offers, requires_loyalty=False)
    ] == [
        "Ananas",
        "Latte Intero",
    ]


def test_multiple_filters_are_combined_conjunctively(offers):
    results = filter_offers(
        offers,
        retailer="lidl",
        locality_scope="regional",
        locality_status="verified",
        evidence_status="verified",
        requires_loyalty=True,
    )

    assert [record["product_name"] for record in results] == [
        "Latte Fresco"
    ]


def test_source_order_does_not_affect_result_order(offers):
    forward = filter_offers(offers, retailer="lidl")
    reverse = filter_offers(list(reversed(offers)), retailer="lidl")

    assert forward == reverse


def test_filtering_does_not_mutate_source_dataset(offers):
    original = deepcopy(offers)

    filter_offers(
        offers,
        retailer="lidl",
        locality_scope="regional",
    )

    assert offers == original


def test_validity_is_not_interpreted_by_version_01(offers):
    with pytest.raises(TypeError):
        filter_offers(
            offers,
            active_at="2026-08-26T12:00:00Z",
        )


def test_filtered_results_are_always_a_subset_of_source_records(offers):
    results = filter_offers(
        offers,
        retailer="lidl",
        requires_loyalty=True,
    )

    assert all(record in offers for record in results)
    assert len(results) <= len(offers)


def test_no_filters_preserve_all_source_records(offers):
    results = filter_offers(offers)

    assert sorted(
        results,
        key=lambda record: (
            record["retailer"],
            record["product_name"],
            record["price"],
            record["currency"],
        ),
    ) == sorted(
        offers,
        key=lambda record: (
            record["retailer"],
            record["product_name"],
            record["price"],
            record["currency"],
        ),
    )


def test_conjunctive_filters_never_return_a_record_matching_only_some_filters(
    offers,
):
    results = filter_offers(
        offers,
        retailer="lidl",
        locality_scope="regional",
        locality_status="verified",
        evidence_status="verified",
        requires_loyalty=True,
    )

    assert all(
        record["retailer"] == "lidl"
        and record["locality"]["scope"] == "regional"
        and record["verification"]["locality_status"] == "verified"
        and record["verification"]["evidence_status"] == "verified"
        and record["promotion"]["requires_loyalty"] is True
        for record in results
    )


def test_filtering_result_order_is_deterministic_for_every_filter_combination(
    offers,
):
    combinations = [
        {"retailer": "lidl"},
        {"locality_scope": "regional"},
        {"locality_status": "verified"},
        {"evidence_status": "partial"},
        {"requires_loyalty": True},
        {
            "retailer": "lidl",
            "requires_loyalty": True,
        },
    ]

    for filters in combinations:
        forward = filter_offers(offers, **filters)
        reverse = filter_offers(list(reversed(offers)), **filters)

        assert forward == reverse
