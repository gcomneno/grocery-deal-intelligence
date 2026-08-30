from copy import deepcopy
from types import MappingProxyType

import pytest

from grocery_deal_intelligence.retailers import list_available_retailers


def make_record(retailer, product_name="Latte Fresco", price=1.49):
    return {
        "retailer": retailer,
        "product_name": product_name,
        "price": price,
        "currency": "EUR",
        "promotion": {
            "type": "test",
            "requires_loyalty": False,
        },
        "validity": {
            "from": "2026-08-01T00:00:00Z",
            "to": "2026-08-31T23:59:59Z",
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


def test_multiple_retailers_return_sorted_unique_list():
    records = [
        make_record("lidl", "Pasta", 0.99),
        make_record("carrefour", "Caffe", 3.49),
        make_record("esselunga", "Ananas", 4.88),
    ]

    assert list_available_retailers(records) == [
        "carrefour",
        "esselunga",
        "lidl",
    ]


def test_duplicate_retailers_are_deduplicated():
    records = [
        make_record("lidl", "Pasta", 0.99),
        make_record("lidl", "Latte", 1.49),
    ]

    assert list_available_retailers(records) == ["lidl"]


def test_result_is_independent_of_input_order():
    records = [
        make_record("lidl", "Pasta", 0.99),
        make_record("carrefour", "Caffe", 3.49),
        make_record("esselunga", "Ananas", 4.88),
        make_record("lidl", "Latte", 1.49),
    ]

    assert list_available_retailers(records) == list_available_retailers(
        list(reversed(records)),
    )


def test_empty_corpus_returns_empty_list():
    assert list_available_retailers([]) == []


def test_exact_retailer_identity_and_case_are_preserved():
    records = [
        make_record("lidl", "Pasta", 0.99),
        make_record("LIDL", "Latte", 1.49),
        make_record("Lidl Italia", "Pane", 1.29),
    ]

    assert list_available_retailers(records) == [
        "LIDL",
        "Lidl Italia",
        "lidl",
    ]


def test_mappingproxy_canonical_record_is_supported():
    record = make_record("lidl")

    assert list_available_retailers([MappingProxyType(record)]) == ["lidl"]


def test_missing_retailer_fails_explicitly():
    record = make_record("lidl")
    del record["retailer"]

    with pytest.raises(ValueError, match="canonical offer retailer is required"):
        list_available_retailers([record])


def test_non_string_retailer_fails_explicitly():
    with pytest.raises(TypeError, match="canonical offer retailer must be a string"):
        list_available_retailers([make_record(123)])


def test_blank_retailer_fails_explicitly():
    with pytest.raises(
        ValueError,
        match="canonical offer retailer must be a non-empty string",
    ):
        list_available_retailers([make_record("   ")])


def test_non_mapping_record_fails_explicitly():
    with pytest.raises(TypeError, match="canonical offer records must be mappings"):
        list_available_retailers([object()])


def test_listing_does_not_mutate_source_records():
    records = [make_record("lidl")]
    original = deepcopy(records)

    list_available_retailers(records)

    assert records == original
