from grocery_deal_intelligence.comparison import UNKNOWN
from grocery_deal_intelligence.comparison_policy import (
    REQUIRED_FACT_UNAVAILABLE,
    evaluate_comparison_policy,
    resolve_comparison_policy,
)


def test_supported_status_does_not_override_proposed_evidence_mismatch():
    policy = resolve_comparison_policy(category="chocolate_bar")
    verification = [
        {
            "path": ["product_family"],
            "left": {
                "status": "supported",
                "proposed_value": "dark_chocolate",
                "evidence_value": "milk_chocolate",
            },
            "right": {
                "status": "supported",
                "proposed_value": "dark_chocolate",
                "evidence_value": "dark_chocolate",
            },
        },
        {
            "path": ["weight_g"],
            "left": {
                "status": "supported",
                "proposed_value": 100,
                "evidence_value": 100,
            },
            "right": {
                "status": "supported",
                "proposed_value": 100,
                "evidence_value": 100,
            },
        },
    ]

    result = evaluate_comparison_policy(verification, policy)

    assert result["relationship"] == UNKNOWN
    assert result["eligible"] is False
    assert result["reasons"] == [
        {
            "code": REQUIRED_FACT_UNAVAILABLE,
            "rule_id": "same_product_family",
            "path": ["product_family"],
        }
    ]
