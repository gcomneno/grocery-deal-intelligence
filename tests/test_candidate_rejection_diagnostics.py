from copy import deepcopy

import pytest

from grocery_deal_intelligence.diagnostics import diagnose_candidate_rejection
from grocery_deal_intelligence.validation import validate_offers

VALID_CANDIDATE = {
    "retailer": "Example Retailer",
    "product_name": "Example Product",
    "price": 1.99,
    "currency": "EUR",
    "reference_price": None,
    "packaging_text": "500 g",
    "base_price_text": None,
    "promotion": {
        "type": "discount",
        "requires_loyalty": False,
        "discount_text": "-20%",
    },
    "validity": {"from": "2026-08-24", "to": "2026-09-20"},
    "locality": {"scope": "store", "stores": ["Example Store"]},
    "verification": {
        "locality_status": "verified",
        "evidence_status": "verified",
    },
    "provenance": {
        "source_type": "retailer_api",
        "source_url": "https://example.invalid/offer",
        "observed_at": "2026-08-26T12:00:00Z",
    },
}


ISSUE_20_CANDIDATE = {
    "base_price_text": "Pils 3 x 0,33 l",
    "currency": "EUR",
    "locality": "Italy",
    "packaging_text": "Pils 3 x 0,33 l",
    "price": 2.33,
    "product_name": "Pils 3 x 0,33 l",
    "promotion": "M014",
    "provenance": "Supplier",
    "reference_price": 2.33,
    "retailer": "Forst",
    "validity": "2026-08-24T00:00:00Z/2026-09-20T00:00:00Z",
    "verification": "true",
}


def test_valid_candidate_has_no_rejection_diagnostics():
    assert validate_offers([VALID_CANDIDATE])["valid"] is True
    assert diagnose_candidate_rejection(VALID_CANDIDATE) == []


def test_issue_20_candidate_is_classified_by_structural_schema_failures():
    assert validate_offers([ISSUE_20_CANDIDATE])["valid"] is False

    diagnostics = diagnose_candidate_rejection(ISSUE_20_CANDIDATE)

    assert diagnostics == [
        {
            "category": "wrong_canonical_shape",
            "path": ["locality"],
            "validator": "type",
            "message": "expected object; got string",
        },
        {
            "category": "wrong_canonical_shape",
            "path": ["promotion"],
            "validator": "type",
            "message": "expected object; got string",
        },
        {
            "category": "wrong_canonical_shape",
            "path": ["provenance"],
            "validator": "type",
            "message": "expected object; got string",
        },
        {
            "category": "wrong_canonical_shape",
            "path": ["validity"],
            "validator": "type",
            "message": "expected object; got string",
        },
        {
            "category": "wrong_canonical_shape",
            "path": ["verification"],
            "validator": "type",
            "message": "expected object; got string",
        },
    ]


def test_missing_unexpected_and_invalid_value_failures_are_preserved():
    candidate = deepcopy(VALID_CANDIDATE)
    del candidate["currency"]
    candidate["unexpected"] = "value"
    candidate["locality"]["scope"] = "planet"

    diagnostics = diagnose_candidate_rejection(candidate)

    assert {(item["category"], tuple(item["path"])) for item in diagnostics} == {
        ("missing_required_field", ("currency",)),
        ("unexpected_field", ("unexpected",)),
        ("invalid_enum_or_value", ("locality", "scope")),
    }


def test_scalar_type_failure_is_distinct_from_object_shape_failure():
    candidate = deepcopy(VALID_CANDIDATE)
    candidate["price"] = "1.99"

    assert diagnose_candidate_rejection(candidate) == [
        {
            "category": "wrong_field_type",
            "path": ["price"],
            "validator": "type",
            "message": "expected number; got string",
        }
    ]


def test_diagnostics_are_read_only_and_repeatably_ordered():
    candidate = deepcopy(ISSUE_20_CANDIDATE)
    before = deepcopy(candidate)

    first = diagnose_candidate_rejection(candidate)
    second = diagnose_candidate_rejection(candidate)

    assert candidate == before
    assert first == second


def test_diagnostics_do_not_repair_or_promote_invalid_candidate():
    candidate = deepcopy(ISSUE_20_CANDIDATE)

    diagnostics = diagnose_candidate_rejection(candidate)
    validation_after = validate_offers([candidate])

    assert diagnostics
    assert validation_after["valid"] is False
    assert validation_after["valid_records"] == 0


def test_non_mapping_candidate_is_rejected_explicitly():
    with pytest.raises(TypeError, match="candidate must be a mapping"):
        diagnose_candidate_rejection(["not", "a", "mapping"])
