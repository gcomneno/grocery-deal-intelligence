import copy

import pytest

from grocery_deal_intelligence.comparison import (
    COMPARABLE,
    COMPARISON_CLAIM_UNSUPPORTED,
    INVALID_PROPOSAL,
    NO_COMPARISON_CLAIMS,
    RELATIONSHIP_POLICY_UNAVAILABLE,
    SAME_PRODUCT,
    UNKNOWN,
    compare_admitted_offers,
    validate_comparison_proposal,
)


def offer(*, retailer, product_name, price=1.79, packaging_text=None):
    result = {
        "retailer": retailer,
        "product_name": product_name,
        "price": price,
        "currency": "EUR",
        "promotion": {
            "type": "offer",
            "requires_loyalty": False,
        },
        "validity": {
            "from": "2026-08-28",
            "to": "2026-08-31",
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
            "source_type": "retailer",
            "source_url": f"https://example.test/{retailer}",
            "observed_at": "2026-08-28T12:00:00Z",
        },
    }
    if packaging_text is not None:
        result["packaging_text"] = packaging_text
    return result


def proposal(relationship, *claims):
    return {
        "relationship": relationship,
        "claims": list(claims),
    }


def claim(path, left_value, right_value):
    return {
        "path": path,
        "left_value": left_value,
        "right_value": right_value,
    }


def test_same_product_can_be_proposed_and_facts_verified_without_granting_authority():
    left = offer(
        retailer="carrefour",
        product_name="Novi Fondente 70% 100 g",
        packaging_text="100 g",
    )
    right = offer(
        retailer="despar",
        product_name="Novi Fondente 70% 100 g",
        packaging_text="100 g",
    )
    proposed = proposal(
        SAME_PRODUCT,
        claim(["product_name"], left["product_name"], right["product_name"]),
        claim(["packaging_text"], "100 g", "100 g"),
    )

    result = compare_admitted_offers(left, right, proposed)

    assert result["proposal"]["relationship"] == SAME_PRODUCT
    assert all(
        item["left"]["status"] == "supported"
        and item["right"]["status"] == "supported"
        for item in result["verification"]
    )
    assert result["admission"] == {
        "relationship": UNKNOWN,
        "eligible": False,
        "reasons": [
            {
                "code": RELATIONSHIP_POLICY_UNAVAILABLE,
                "proposed_relationship": SAME_PRODUCT,
            }
        ],
    }


def test_comparable_can_be_proposed_without_claiming_identity():
    left = offer(
        retailer="carrefour",
        product_name="Novi Fondente 70%",
        packaging_text="100 g",
    )
    right = offer(
        retailer="despar",
        product_name="Lindt Fondente 70%",
        packaging_text="100 g",
    )
    proposed = proposal(
        COMPARABLE,
        claim(["packaging_text"], "100 g", "100 g"),
    )

    result = compare_admitted_offers(left, right, proposed)

    assert result["proposal"]["relationship"] == COMPARABLE
    assert result["verification"][0]["left"]["status"] == "supported"
    assert result["verification"][0]["right"]["status"] == "supported"
    assert result["admission"]["relationship"] == UNKNOWN
    assert result["admission"]["reasons"] == [
        {
            "code": RELATIONSHIP_POLICY_UNAVAILABLE,
            "proposed_relationship": COMPARABLE,
        }
    ]


def test_missing_evidence_fails_closed_before_relationship_policy():
    left = offer(retailer="carrefour", product_name="Chocolate A")
    right = offer(retailer="despar", product_name="Chocolate B")
    proposed = proposal(
        COMPARABLE,
        claim(["packaging_text"], "100 g", "100 g"),
    )

    result = compare_admitted_offers(left, right, proposed)

    assert result["admission"]["relationship"] == UNKNOWN
    assert result["admission"]["eligible"] is False
    assert result["verification"][0]["left"]["status"] == "unverifiable"
    assert result["verification"][0]["right"]["status"] == "unverifiable"
    assert result["admission"]["reasons"][0]["code"] == COMPARISON_CLAIM_UNSUPPORTED


def test_contradicted_evidence_blocks_stronger_relationship():
    left = offer(
        retailer="carrefour",
        product_name="Chocolate",
        packaging_text="100 g",
    )
    right = offer(
        retailer="despar",
        product_name="Chocolate",
        packaging_text="75 g",
    )
    proposed = proposal(
        SAME_PRODUCT,
        claim(["packaging_text"], "100 g", "100 g"),
    )

    result = compare_admitted_offers(left, right, proposed)

    assert result["admission"]["relationship"] == UNKNOWN
    assert result["verification"][0]["left"]["status"] == "supported"
    assert result["verification"][0]["right"]["status"] == "contradicted"
    assert result["admission"]["reasons"][0]["code"] == COMPARISON_CLAIM_UNSUPPORTED


def test_unsupported_proposed_attribute_cannot_become_comparison_fact():
    left = offer(retailer="carrefour", product_name="Chocolate")
    right = offer(retailer="despar", product_name="Chocolate")
    proposed = proposal(
        SAME_PRODUCT,
        claim(["brand"], "Novi", "Novi"),
    )

    result = compare_admitted_offers(left, right, proposed)

    assert result["admission"]["relationship"] == UNKNOWN
    assert result["verification"][0]["left"]["status"] == "unverifiable"
    assert result["verification"][0]["right"]["status"] == "unverifiable"


def test_one_side_cannot_supply_missing_evidence_for_the_other():
    left = offer(
        retailer="carrefour",
        product_name="Chocolate",
        packaging_text="100 g",
    )
    right = offer(retailer="despar", product_name="Chocolate")
    proposed = proposal(
        COMPARABLE,
        claim(["packaging_text"], "100 g", "100 g"),
    )

    result = compare_admitted_offers(left, right, proposed)

    assert result["verification"][0]["left"]["status"] == "supported"
    assert result["verification"][0]["right"]["status"] == "unverifiable"
    assert result["admission"]["relationship"] == UNKNOWN


def test_explicit_unknown_is_a_valid_fail_closed_relationship():
    result = compare_admitted_offers(
        offer(retailer="carrefour", product_name="Chocolate A"),
        offer(retailer="despar", product_name="Chocolate B"),
        proposal(UNKNOWN),
    )

    assert result["admission"] == {
        "relationship": UNKNOWN,
        "eligible": True,
        "reasons": [],
    }


def test_malformed_relationship_is_rejected_fail_closed():
    proposed = proposal("probably_same")

    assert validate_comparison_proposal(proposed)["valid"] is False

    result = compare_admitted_offers(
        offer(retailer="carrefour", product_name="Chocolate"),
        offer(retailer="despar", product_name="Chocolate"),
        proposed,
    )

    assert result["admission"]["relationship"] == UNKNOWN
    assert result["admission"]["eligible"] is False
    assert result["admission"]["reasons"][0]["code"] == INVALID_PROPOSAL


def test_inputs_are_not_mutated_and_result_is_detached():
    left = offer(
        retailer="carrefour",
        product_name="Chocolate",
        packaging_text="100 g",
    )
    right = offer(
        retailer="despar",
        product_name="Chocolate",
        packaging_text="100 g",
    )
    proposed = proposal(
        COMPARABLE,
        claim(["packaging_text"], "100 g", "100 g"),
    )

    left_before = copy.deepcopy(left)
    right_before = copy.deepcopy(right)
    proposal_before = copy.deepcopy(proposed)

    result = compare_admitted_offers(left, right, proposed)
    result["proposal"]["claims"][0]["left_value"] = "changed"

    assert left == left_before
    assert right == right_before
    assert proposed == proposal_before


def test_reversing_inputs_preserves_authoritative_relationship_semantics():
    left = offer(
        retailer="carrefour",
        product_name="Chocolate A",
        packaging_text="100 g",
    )
    right = offer(
        retailer="despar",
        product_name="Chocolate B",
        packaging_text="100 g",
    )

    forward = compare_admitted_offers(
        left,
        right,
        proposal(COMPARABLE, claim(["packaging_text"], "100 g", "100 g")),
    )
    reverse = compare_admitted_offers(
        right,
        left,
        proposal(COMPARABLE, claim(["packaging_text"], "100 g", "100 g")),
    )

    assert forward["admission"]["relationship"] == UNKNOWN
    assert reverse["admission"]["relationship"] == UNKNOWN
    assert forward["admission"]["reasons"] == reverse["admission"]["reasons"]


def test_canonical_shape_alone_does_not_establish_comparability():
    left = offer(retailer="carrefour", product_name="Milk")
    right = offer(retailer="despar", product_name="Dark Chocolate")

    result = compare_admitted_offers(
        left,
        right,
        proposal(COMPARABLE),
    )

    assert result["admission"] == {
        "relationship": UNKNOWN,
        "eligible": False,
        "reasons": [{"code": NO_COMPARISON_CLAIMS}],
    }


@pytest.mark.parametrize(
    ("path", "left_value", "right_value", "relationship"),
    [
        (["retailer"], "carrefour", "despar", SAME_PRODUCT),
        (["price"], 1.79, 1.79, COMPARABLE),
        (
            ["product_name"],
            "Novi Fondente 70%",
            "Lindt Fondente 70%",
            SAME_PRODUCT,
        ),
    ],
)
def test_bilateral_fact_support_does_not_become_relationship_authority(
    path,
    left_value,
    right_value,
    relationship,
):
    left = offer(
        retailer="carrefour",
        product_name="Novi Fondente 70%",
        price=1.79,
    )
    right = offer(
        retailer="despar",
        product_name="Lindt Fondente 70%",
        price=1.79,
    )

    result = compare_admitted_offers(
        left,
        right,
        proposal(relationship, claim(path, left_value, right_value)),
    )

    assert result["verification"][0]["left"]["status"] == "supported"
    assert result["verification"][0]["right"]["status"] == "supported"
    assert result["admission"] == {
        "relationship": UNKNOWN,
        "eligible": False,
        "reasons": [
            {
                "code": RELATIONSHIP_POLICY_UNAVAILABLE,
                "proposed_relationship": relationship,
            }
        ],
    }


def test_duplicate_comparison_claim_paths_are_rejected():
    left = offer(retailer="carrefour", product_name="Chocolate")
    right = offer(retailer="despar", product_name="Chocolate")
    proposed = proposal(
        SAME_PRODUCT,
        claim(["product_name"], "Chocolate", "Chocolate"),
        claim(["product_name"], "Chocolate", "Chocolate"),
    )

    with pytest.raises(ValueError, match="duplicate comparison claim path"):
        compare_admitted_offers(left, right, proposed)


def test_comparison_does_not_duplicate_canonical_admission_authority():
    result = compare_admitted_offers(
        offer(retailer="carrefour", product_name="Chocolate A"),
        offer(retailer="despar", product_name="Chocolate B"),
        proposal(UNKNOWN),
    )

    assert "canonical" not in result
    assert "validated" not in result
    assert "structurally_valid" not in result
    assert "canonical_admission" not in result


def test_missing_verification_claim_is_rejected():
    from grocery_deal_intelligence.comparison import (
        VERIFICATION_PROPOSAL_MISMATCH,
        evaluate_comparison_admission,
    )

    proposed = proposal(
        SAME_PRODUCT,
        claim(["product_name"], "Chocolate", "Chocolate"),
        claim(["packaging_text"], "100 g", "100 g"),
    )
    verification = [
        {
            "path": ["product_name"],
            "left": {"status": "supported"},
            "right": {"status": "supported"},
        }
    ]

    result = evaluate_comparison_admission(proposed, verification)

    assert result == {
        "relationship": UNKNOWN,
        "eligible": False,
        "reasons": [
            {
                "code": VERIFICATION_PROPOSAL_MISMATCH,
                "missing_paths": [["packaging_text"]],
                "extra_paths": [],
            }
        ],
    }


def test_extra_verification_claim_is_rejected():
    from grocery_deal_intelligence.comparison import (
        VERIFICATION_PROPOSAL_MISMATCH,
        evaluate_comparison_admission,
    )

    proposed = proposal(
        SAME_PRODUCT,
        claim(["product_name"], "Chocolate", "Chocolate"),
    )
    verification = [
        {
            "path": ["product_name"],
            "left": {"status": "supported"},
            "right": {"status": "supported"},
        },
        {
            "path": ["currency"],
            "left": {"status": "supported"},
            "right": {"status": "supported"},
        },
    ]

    result = evaluate_comparison_admission(proposed, verification)

    assert result == {
        "relationship": UNKNOWN,
        "eligible": False,
        "reasons": [
            {
                "code": VERIFICATION_PROPOSAL_MISMATCH,
                "missing_paths": [],
                "extra_paths": [["currency"]],
            }
        ],
    }


def test_mismatched_verification_claim_is_rejected():
    from grocery_deal_intelligence.comparison import (
        VERIFICATION_PROPOSAL_MISMATCH,
        evaluate_comparison_admission,
    )

    proposed = proposal(
        COMPARABLE,
        claim(["packaging_text"], "100 g", "100 g"),
    )
    verification = [
        {
            "path": ["currency"],
            "left": {"status": "supported"},
            "right": {"status": "supported"},
        }
    ]

    result = evaluate_comparison_admission(proposed, verification)

    assert result == {
        "relationship": UNKNOWN,
        "eligible": False,
        "reasons": [
            {
                "code": VERIFICATION_PROPOSAL_MISMATCH,
                "missing_paths": [["packaging_text"]],
                "extra_paths": [["currency"]],
            }
        ],
    }


def test_duplicate_verification_claim_paths_are_rejected():
    from grocery_deal_intelligence.comparison import evaluate_comparison_admission

    proposed = proposal(
        SAME_PRODUCT,
        claim(["product_name"], "Chocolate", "Chocolate"),
    )
    verification = [
        {
            "path": ["product_name"],
            "left": {"status": "supported"},
            "right": {"status": "supported"},
        },
        {
            "path": ["product_name"],
            "left": {"status": "supported"},
            "right": {"status": "supported"},
        },
    ]

    with pytest.raises(ValueError, match="duplicate verification claim path"):
        evaluate_comparison_admission(proposed, verification)
