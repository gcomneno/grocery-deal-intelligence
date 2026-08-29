import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from grocery_deal_intelligence.comparison import COMPARABLE, UNKNOWN
from grocery_deal_intelligence.comparison_policy import (
    REQUIRED_FACT_UNAVAILABLE,
    evaluate_comparison_policy,
    resolve_comparison_policy,
)
from grocery_deal_intelligence.product_attributes import (
    FAMILY_EVIDENCE_MISMATCH,
    QUANTITY_AMBIGUOUS,
    QUANTITY_UNAVAILABLE,
    comparison_verification_from_attributes,
    normalize_product_attributes,
)


ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema/normalized-product-attributes-v0.1.schema.json"


def family(value="dark_chocolate", path=None):
    return {
        "value": value,
        "evidence_path": list(path or ["product_name"]),
    }


def test_100_g_normalizes_to_weight_g_with_provenance():
    offer = {"product_name": "Cioccolato fondente", "packaging_text": "100 g"}

    result = normalize_product_attributes(offer, product_family_candidate=family())

    assert result["values"]["product_family"] == "dark_chocolate"
    assert result["values"]["quantity"] == {
        "value": 100,
        "unit": "g",
        "dimension": "mass",
    }
    assert result["values"]["weight_g"] == 100
    weight_claim = next(item for item in result["claims"] if item["path"] == ["weight_g"])
    assert weight_claim["evidence_path"] == ["packaging_text"]
    assert weight_claim["raw_value"] == "100 g"
    assert weight_claim["status"] == "supported"
    assert result["reasons"] == []


def test_1_kg_normalizes_to_1000_g():
    result = normalize_product_attributes({"packaging_text": "1 kg"})

    assert result["values"]["weight_g"] == 1000
    assert result["values"]["quantity"] == {
        "value": 1000,
        "unit": "g",
        "dimension": "mass",
    }


def test_composite_pack_preserves_unit_and_total_quantity():
    result = normalize_product_attributes({"packaging_text": "2 x 100 g"})

    assert result["values"]["pack_count"] == 2
    assert result["values"]["unit_quantity"] == {
        "value": 100,
        "unit": "g",
        "dimension": "mass",
    }
    assert result["values"]["total_quantity"] == {
        "value": 200,
        "unit": "g",
        "dimension": "mass",
    }
    assert result["values"]["weight_g"] == 200


def test_volume_never_becomes_weight():
    result = normalize_product_attributes({"packaging_text": "1 l"})

    assert result["values"]["quantity"] == {
        "value": 1000,
        "unit": "ml",
        "dimension": "volume",
    }
    assert result["values"]["volume_ml"] == 1000
    assert "weight_g" not in result["values"]


def test_missing_quantity_fails_closed():
    result = normalize_product_attributes({"product_name": "Cioccolato fondente"})

    assert "weight_g" not in result["values"]
    assert result["reasons"] == [{"code": QUANTITY_UNAVAILABLE}]


def test_conflicting_observed_quantities_fail_closed():
    result = normalize_product_attributes(
        {"product_name": "Cioccolato fondente 100 g", "packaging_text": "200 g"}
    )

    assert "weight_g" not in result["values"]
    assert result["reasons"][0]["code"] == QUANTITY_AMBIGUOUS


def test_product_family_requires_matching_curated_evidence():
    result = normalize_product_attributes(
        {"product_name": "Cioccolato al latte", "packaging_text": "100 g"},
        product_family_candidate=family("dark_chocolate"),
    )

    assert "product_family" not in result["values"]
    assert any(item["code"] == FAMILY_EVIDENCE_MISMATCH for item in result["reasons"])


def test_ai_like_candidate_cannot_bypass_family_verification():
    candidate = {
        "value": "dark_chocolate",
        "evidence_path": ["product_name"],
        "confidence": 0.999,
        "model": "some-model",
    }

    result = normalize_product_attributes(
        {"product_name": "Tavoletta bianca", "packaging_text": "100 g"},
        product_family_candidate=candidate,
    )

    assert "product_family" not in result["values"]
    assert any(item["code"] == FAMILY_EVIDENCE_MISMATCH for item in result["reasons"])


def test_normalization_does_not_mutate_inputs_and_is_deterministic():
    offer = {"product_name": "Cioccolato fondente 100 g", "packaging_text": "100 g"}
    candidate = family()
    original_offer = copy.deepcopy(offer)
    original_candidate = copy.deepcopy(candidate)

    first = normalize_product_attributes(offer, product_family_candidate=candidate)
    second = normalize_product_attributes(offer, product_family_candidate=candidate)

    assert offer == original_offer
    assert candidate == original_candidate
    assert first == second


def test_result_conforms_to_normalized_attribute_schema():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    result = normalize_product_attributes(
        {"product_name": "Cioccolato fondente", "packaging_text": "100 g"},
        product_family_candidate=family(),
    )

    assert list(validator.iter_errors(result)) == []


def test_verified_attributes_feed_existing_comparison_policy():
    left = normalize_product_attributes(
        {"product_name": "Cioccolato fondente Novi", "packaging_text": "100 g"},
        product_family_candidate=family(),
    )
    right = normalize_product_attributes(
        {"product_name": "Cioccolato fondente Lindt", "packaging_text": "100 g"},
        product_family_candidate=family(),
    )

    verification = comparison_verification_from_attributes(left, right)
    policy = resolve_comparison_policy(category="chocolate_bar")
    result = evaluate_comparison_policy(verification, policy)

    assert result["relationship"] == COMPARABLE
    assert result["eligible"] is True


def test_missing_verified_family_stays_unknown_at_policy_boundary():
    left = normalize_product_attributes(
        {"product_name": "Tavoletta bianca", "packaging_text": "100 g"},
        product_family_candidate=family(),
    )
    right = normalize_product_attributes(
        {"product_name": "Cioccolato fondente", "packaging_text": "100 g"},
        product_family_candidate=family(),
    )

    verification = comparison_verification_from_attributes(left, right)
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
