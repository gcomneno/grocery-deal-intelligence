from copy import deepcopy

import pytest

from grocery_deal_intelligence.query import search_offers


def make_record(
    retailer,
    product_name,
    price,
    currency="EUR",
):
    return {
        "retailer": retailer,
        "product_name": product_name,
        "price": price,
        "currency": currency,
        "promotion": {
            "type": "test",
            "requires_loyalty": False,
        },
        "validity": {
            "from": None,
            "to": None,
        },
        "locality": {
            "scope": "national",
            "stores": [],
        },
        "verification": {
            "locality_status": "verified",
            "evidence_status": "verified",
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
        make_record("lidl", "Latte Fresco", 1.49),
        make_record("esselunga", "F.lli Orsero Ananas Tronchetto 500 g", 4.88),
        make_record("lidl", "Pasta di semola", 0.99),
        make_record("esselunga", "Latte Intero", 1.59),
    ]


def test_search_is_case_insensitive_substring_match(offers):
    results = search_offers(offers, "ANANAS")

    assert [record["product_name"] for record in results] == [
        "F.lli Orsero Ananas Tronchetto 500 g"
    ]


def test_search_uses_only_product_name(offers):
    results = search_offers(offers, "orsero 500g")

    assert results == []


def test_retailer_filter_is_exact(offers):
    results = search_offers(
        offers,
        "latte",
        retailer="lidl",
    )

    assert [record["product_name"] for record in results] == ["Latte Fresco"]


def test_retailer_filter_is_case_sensitive(offers):
    results = search_offers(
        offers,
        "latte",
        retailer="LIDL",
    )

    assert results == []


def test_without_retailer_filter_all_retailers_are_considered(offers):
    results = search_offers(offers, "latte")

    assert [(record["retailer"], record["product_name"]) for record in results] == [
        ("esselunga", "Latte Intero"),
        ("lidl", "Latte Fresco"),
    ]


def test_results_are_deterministically_sorted(offers):
    reordered = list(reversed(offers))

    results = search_offers(reordered, "latte")

    assert [(record["retailer"], record["product_name"]) for record in results] == [
        ("esselunga", "Latte Intero"),
        ("lidl", "Latte Fresco"),
    ]


def test_search_does_not_mutate_source_dataset(offers):
    original = deepcopy(offers)

    search_offers(offers, "latte")

    assert offers == original


def test_empty_query_is_rejected(offers):
    with pytest.raises(ValueError, match="query must not be empty"):
        search_offers(offers, "")

    with pytest.raises(ValueError, match="query must not be empty"):
        search_offers(offers, "   ")
