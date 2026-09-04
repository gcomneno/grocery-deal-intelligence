import copy

import pytest

from grocery_deal_intelligence.admission import (
    CONTRADICTED_CLAIM,
    CRITICAL_CLAIM_PATHS,
    CRITICAL_CLAIM_UNSUPPORTED,
    STRUCTURAL_INVALID,
    evaluate_canonical_admission,
)


def supported_claims():
    return [
        {
            "path": list(path),
            "status": "supported",
            "candidate_value": "x",
            "evidence_value": "x",
        }
        for path in CRITICAL_CLAIM_PATHS
    ]


def test_currency_is_not_a_critical_source_evidence_claim():
    assert ("currency",) not in CRITICAL_CLAIM_PATHS


def test_structurally_invalid_candidate_is_ineligible():
    result = evaluate_canonical_admission(
        structurally_valid=False,
        claim_verification=supported_claims(),
    )

    assert result["eligible"] is False
    assert result["reasons"] == [{"code": STRUCTURAL_INVALID}]


def test_any_contradicted_claim_blocks_admission_even_when_non_critical():
    claims = [
        *supported_claims(),
        {
            "path": ["promotion", "discount_text"],
            "status": "contradicted",
            "candidate_value": "-10%",
            "evidence_value": "-20%",
        },
    ]

    result = evaluate_canonical_admission(
        structurally_valid=True,
        claim_verification=claims,
    )

    assert result["eligible"] is False
    assert result["reasons"] == [
        {"code": CONTRADICTED_CLAIM, "path": ["promotion", "discount_text"]}
    ]


def test_non_critical_unverifiable_claim_is_tolerated():
    claims = [
        *supported_claims(),
        {
            "path": ["provenance", "observed_at"],
            "status": "unverifiable",
            "candidate_value": "2026-08-27T00:00:00Z",
        },
    ]

    result = evaluate_canonical_admission(
        structurally_valid=True,
        claim_verification=claims,
    )

    assert result["eligible"] is True
    assert result["reasons"] == []


def test_critical_unverifiable_claim_blocks_admission():
    claims = supported_claims()
    for claim in claims:
        if claim["path"] == ["price"]:
            claim["status"] = "unverifiable"
            claim.pop("evidence_value")

    result = evaluate_canonical_admission(
        structurally_valid=True,
        claim_verification=claims,
    )

    assert result["eligible"] is False
    assert result["reasons"] == [
        {"code": CRITICAL_CLAIM_UNSUPPORTED, "path": ["price"]}
    ]


def test_missing_critical_claim_is_treated_as_unsupported_not_contradicted():
    claims = [claim for claim in supported_claims() if claim["path"] != ["retailer"]]

    result = evaluate_canonical_admission(
        structurally_valid=True,
        claim_verification=claims,
    )

    assert result["eligible"] is False
    assert result["reasons"] == [
        {"code": CRITICAL_CLAIM_UNSUPPORTED, "path": ["retailer"]}
    ]
    retailer = next(
        claim for claim in result["critical_claims"] if claim["path"] == ["retailer"]
    )
    assert retailer["status"] == "unverifiable"


def test_critical_contradiction_is_reported_once_as_contradicted_claim():
    claims = supported_claims()
    for claim in claims:
        if claim["path"] == ["product_name"]:
            claim["status"] = "contradicted"
            claim["candidate_value"] = "Wrong"
            claim["evidence_value"] = "Right"

    result = evaluate_canonical_admission(
        structurally_valid=True,
        claim_verification=claims,
    )

    assert result["reasons"] == [{"code": CONTRADICTED_CLAIM, "path": ["product_name"]}]


def test_reason_order_is_stable_and_deterministic():
    claims = supported_claims()
    for claim in claims:
        if claim["path"] == ["validity", "to"]:
            claim["status"] = "unverifiable"
    claims.extend(
        [
            {"path": ["verification", "evidence_status"], "status": "contradicted"},
            {"path": ["currency"], "status": "contradicted"},
        ]
    )

    result = evaluate_canonical_admission(
        structurally_valid=False,
        claim_verification=claims,
    )

    assert result["reasons"] == [
        {"code": STRUCTURAL_INVALID},
        {"code": CONTRADICTED_CLAIM, "path": ["currency"]},
        {"code": CONTRADICTED_CLAIM, "path": ["verification", "evidence_status"]},
        {"code": CRITICAL_CLAIM_UNSUPPORTED, "path": ["validity", "to"]},
    ]


def test_inputs_are_not_mutated():
    claims = [
        *supported_claims(),
        {"path": ["currency"], "status": "unverifiable", "candidate_value": "EUR"},
    ]
    before = copy.deepcopy(claims)

    evaluate_canonical_admission(
        structurally_valid=True,
        claim_verification=claims,
    )

    assert claims == before


def test_duplicate_paths_are_rejected():
    claims = supported_claims()
    claims.append(copy.deepcopy(claims[0]))

    with pytest.raises(ValueError, match="duplicate claim path"):
        evaluate_canonical_admission(
            structurally_valid=True,
            claim_verification=claims,
        )


def test_unknown_status_is_rejected():
    claims = supported_claims()
    claims[0]["status"] = "maybe"

    with pytest.raises(ValueError, match="unknown claim verification status"):
        evaluate_canonical_admission(
            structurally_valid=True,
            claim_verification=claims,
        )
