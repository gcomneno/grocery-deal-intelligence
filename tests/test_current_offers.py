from copy import deepcopy
from types import MappingProxyType

import pytest

from grocery_deal_intelligence.current_offers import list_current_offers

AS_OF = "2026-08-29"


def make_record(
    retailer,
    product_name,
    price,
    *,
    valid_from="2026-08-01",
    valid_to="2026-08-31",
    provenance_extra=None,
):
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
            "from": valid_from,
            "to": valid_to,
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
            **dict(provenance_extra or {}),
        },
    }


def test_without_retailer_returns_current_offers_across_retailers():
    records = [
        make_record("lidl", "Latte Fresco", 1.49),
        make_record("esselunga", "Ananas", 4.88),
    ]

    results = list_current_offers(records, as_of=AS_OF)

    assert [(record["retailer"], record["product_name"]) for record in results] == [
        ("esselunga", "Ananas"),
        ("lidl", "Latte Fresco"),
    ]


def test_retailer_filter_is_exact_and_case_sensitive():
    records = [
        make_record("lidl", "Latte Fresco", 1.49),
        make_record("esselunga", "Latte Intero", 1.59),
    ]

    assert [
        record["product_name"]
        for record in list_current_offers(records, as_of=AS_OF, retailer="lidl")
    ] == ["Latte Fresco"]

    assert list_current_offers(records, as_of=AS_OF, retailer="LIDL") == []


def test_expired_and_future_offers_are_excluded():
    records = [
        make_record("lidl", "Current", 1.00),
        make_record("lidl", "Expired", 1.00, valid_to="2026-08-28"),
        make_record("lidl", "Future", 1.00, valid_from="2026-08-30"),
    ]

    results = list_current_offers(records, as_of=AS_OF)

    assert [record["product_name"] for record in results] == ["Current"]


def test_malformed_missing_and_incomplete_validity_fail_closed():
    records = [
        make_record("lidl", "Current", 1.00),
        make_record("lidl", "Malformed", 1.00, valid_from="not-a-date"),
        make_record("lidl", "Missing To", 1.00, valid_to=None),
        {
            **make_record("lidl", "Missing Validity", 1.00),
            "validity": None,
        },
    ]

    results = list_current_offers(records, as_of=AS_OF)

    assert [record["product_name"] for record in results] == ["Current"]


def test_unknown_retailer_returns_empty_result():
    records = [make_record("lidl", "Latte Fresco", 1.49)]

    assert list_current_offers(records, as_of=AS_OF, retailer="unknown") == []


def test_result_order_is_deterministic_across_input_permutations():
    records = [
        make_record(
            "lidl",
            "Latte Fresco",
            1.49,
            provenance_extra={"fixture_sha256": "b"},
        ),
        make_record("esselunga", "Ananas", 4.88),
        make_record(
            "lidl",
            "Latte Fresco",
            1.49,
            provenance_extra={"fixture_sha256": "a"},
        ),
    ]

    forward = list_current_offers(records, as_of=AS_OF)
    reverse = list_current_offers(list(reversed(records)), as_of=AS_OF)

    assert forward == reverse
    assert [record["provenance"].get("fixture_sha256") for record in forward] == [
        None,
        "a",
        "b",
    ]


def test_mappingproxy_canonical_record_is_supported():
    record = make_record("lidl", "Latte Fresco", 1.49)
    canonical_record = MappingProxyType(record)

    results = list_current_offers([canonical_record], as_of=AS_OF)

    assert results == [record]
    assert isinstance(results[0], dict)
    assert results[0] is not canonical_record
    assert results[0]["provenance"] == record["provenance"]


def test_listing_does_not_mutate_source_records():
    records = [make_record("lidl", "Latte Fresco", 1.49)]
    original = deepcopy(records)

    list_current_offers(records, as_of=AS_OF)

    assert records == original


def test_complete_canonical_record_and_provenance_are_retained():
    record = make_record(
        "lidl",
        "Latte Fresco",
        1.49,
        provenance_extra={"fixture_sha256": "abc123"},
    )

    results = list_current_offers([record], as_of=AS_OF)

    assert results == [record]
    assert results[0] is not record
    assert results[0]["provenance"] == record["provenance"]


def test_invalid_as_of_raises_explicitly():
    with pytest.raises(ValueError, match="as_of must be an ISO date or datetime"):
        list_current_offers([], as_of="not-a-date")


def test_invalid_retailer_argument_raises_explicitly():
    with pytest.raises(TypeError, match="retailer must be a string when provided"):
        list_current_offers([], as_of=AS_OF, retailer=123)

    with pytest.raises(ValueError, match="retailer must be a non-empty string"):
        list_current_offers([], as_of=AS_OF, retailer=" ")
