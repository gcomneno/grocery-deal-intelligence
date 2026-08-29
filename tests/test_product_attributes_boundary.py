from grocery_deal_intelligence.comparison import UNKNOWN
from grocery_deal_intelligence.comparison_policy import (
    REQUIRED_FACT_UNAVAILABLE,
    evaluate_comparison_policy,
    resolve_comparison_policy,
)
from grocery_deal_intelligence.product_attributes import (
    QUANTITY_UNSUPPORTED,
    comparison_verification_from_attributes,
    normalize_product_attributes,
)


def _family():
    return {
        "value": "dark_chocolate",
        "evidence_path": ["product_name"],
    }


def _dark_chocolate(weight="100 g"):
    return normalize_product_attributes(
        {
            "product_name": "Cioccolato fondente",
            "packaging_text": weight,
        },
        product_family_candidate=_family(),
    )


def test_comparison_projection_rejects_value_changed_after_supported_claim():
    left = _dark_chocolate()
    right = _dark_chocolate()

    left["values"]["product_family"] = "milk_chocolate"

    verification = comparison_verification_from_attributes(left, right)
    family_fact = next(item for item in verification if item["path"] == ["product_family"])

    assert family_fact["left"] == {"status": "unverifiable"}
    assert family_fact["right"]["status"] == "supported"

    result = evaluate_comparison_policy(
        verification,
        resolve_comparison_policy(category="chocolate_bar"),
    )

    assert result["relationship"] == UNKNOWN
    assert result["eligible"] is False
    assert result["reasons"] == [
        {
            "code": REQUIRED_FACT_UNAVAILABLE,
            "rule_id": "same_product_family",
            "path": ["product_family"],
        }
    ]


def test_comparison_projection_rejects_conflicting_duplicate_supported_claims():
    left = _dark_chocolate()
    right = _dark_chocolate()

    left["claims"].append(
        {
            "path": ["weight_g"],
            "status": "supported",
            "evidence_path": ["packaging_text"],
            "raw_value": "forged",
            "normalized_value": 200,
            "normalization": "forged",
        }
    )

    verification = comparison_verification_from_attributes(left, right)
    weight_fact = next(item for item in verification if item["path"] == ["weight_g"])

    assert weight_fact["left"] == {"status": "unverifiable"}
    assert weight_fact["right"]["status"] == "supported"


def test_supported_and_unsupported_units_in_same_text_fail_closed():
    result = normalize_product_attributes({"packaging_text": "100 g + 20 cl"})

    assert "quantity" not in result["values"]
    assert "weight_g" not in result["values"]
    assert result["reasons"] == [{"code": QUANTITY_UNSUPPORTED}]


def test_composite_with_additional_quantity_expression_fails_closed():
    result = normalize_product_attributes({"packaging_text": "2 x 100 g + 50 g"})

    assert "quantity" not in result["values"]
    assert "weight_g" not in result["values"]
