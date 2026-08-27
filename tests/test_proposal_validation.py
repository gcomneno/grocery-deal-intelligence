import copy

from grocery_deal_intelligence.proposal_validation import validate_proposal
from grocery_deal_intelligence.validation import validate_offers


def test_minimal_partial_proposal_is_valid():
    assert validate_proposal({"price": 1.83}) == {"valid": True, "errors": []}


def test_nested_partial_proposal_is_valid():
    proposal = {
        "retailer": "esselunga",
        "product_name": "Example",
        "validity": {"from": "2026-08-24T00:00:00Z"},
        "promotion": {"discount_text": "-20%"},
        "locality": {"stores": ["IT00001"]},
        "provenance": {"source_url": "https://example.invalid/source"},
    }

    result = validate_proposal(proposal)

    assert result == {"valid": True, "errors": []}


def test_empty_proposal_is_valid_and_means_no_claims():
    assert validate_proposal({}) == {"valid": True, "errors": []}


def test_empty_nested_object_is_invalid():
    result = validate_proposal({"validity": {}})

    assert result["valid"] is False
    assert result["errors"][0]["path"] == ["validity"]


def test_unknown_top_level_field_is_invalid():
    result = validate_proposal({"confidence": 0.99})

    assert result["valid"] is False


def test_unknown_nested_field_is_invalid():
    result = validate_proposal({"provenance": {"observer": "model"}})

    assert result["valid"] is False
    assert result["errors"][0]["path"] == ["provenance"]


def test_wrong_type_is_invalid():
    result = validate_proposal({"price": "1.83"})

    assert result["valid"] is False
    assert result["errors"][0]["path"] == ["price"]


def test_invalid_enum_is_rejected():
    result = validate_proposal({"locality": {"scope": "planetary"}})

    assert result["valid"] is False
    assert result["errors"][0]["path"] == ["locality", "scope"]


def test_authority_like_fields_are_invalid():
    for field in ("canonical", "validated", "eligible", "admission", "is_canonical"):
        result = validate_proposal({field: True})
        assert result["valid"] is False, field


def test_validator_does_not_mutate_input():
    proposal = {
        "retailer": "lidl",
        "promotion": {"requires_loyalty": True},
        "locality": {"stores": ["IT01621", "IT00302"]},
    }
    before = copy.deepcopy(proposal)

    validate_proposal(proposal)

    assert proposal == before


def test_proposal_valid_does_not_imply_canonical_valid():
    proposal = {"price": 1.83}

    assert validate_proposal(proposal)["valid"] is True
    assert validate_offers([proposal])["valid"] is False


def test_partial_provenance_does_not_require_fabricated_completeness():
    proposal = {"provenance": {"source_url": "https://example.invalid/source"}}

    assert validate_proposal(proposal)["valid"] is True
