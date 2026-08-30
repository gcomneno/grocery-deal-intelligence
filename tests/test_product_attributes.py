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
    weight_claim = next(
        item for item in result["claims"] if item["path"] == ["weight_g"]
    )
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


def test_word_composite_pack_derives_exact_total():
    result = normalize_product_attributes({"packaging_text": "3 pz da 330 ml"})

    assert result["values"]["pack_count"] == 3
    assert result["values"]["unit_quantity"] == {
        "value": 330,
        "unit": "ml",
        "dimension": "volume",
    }
    assert result["values"]["total_quantity"] == {
        "value": 990,
        "unit": "ml",
        "dimension": "volume",
    }
    assert result["values"]["quantity"] == {
        "value": 990,
        "unit": "ml",
        "dimension": "volume",
    }
    assert result["values"]["volume_ml"] == 990
    assert result["reasons"] == []

    claims = {tuple(item["path"]): item for item in result["claims"]}
    assert claims[("pack_count",)]["normalization"] == ("explicit_composite_relation")
    assert claims[("unit_quantity",)]["normalization"] == (
        "explicit_composite_relation"
    )
    assert claims[("total_quantity",)]["normalization"] == (
        "exact_composite_arithmetic"
    )
    assert claims[("volume_ml",)]["normalization"] == ("exact_composite_arithmetic")


def test_word_composite_pack_accepts_compatible_explicit_total():
    raw = "Conf. 3 pz da 330 ml Cad. 990 ml"
    result = normalize_product_attributes({"product_name": raw})

    assert result["values"]["pack_count"] == 3
    assert result["values"]["unit_quantity"]["value"] == 330
    assert result["values"]["total_quantity"]["value"] == 990
    assert result["values"]["volume_ml"] == 990
    assert result["reasons"] == []

    claims = {tuple(item["path"]): item for item in result["claims"]}
    assert claims[("pack_count",)]["raw_value"] == raw
    assert claims[("pack_count",)]["evidence_path"] == ["product_name"]
    assert claims[("total_quantity",)]["normalization"] == (
        "exact_composite_arithmetic_corroborated"
    )
    assert claims[("quantity",)]["normalization"] == (
        "exact_composite_arithmetic_corroborated"
    )


def test_word_composite_pack_conflicting_total_fails_closed():
    result = normalize_product_attributes(
        {"product_name": ("Birra Conf. 3 pz da 330 ml totale 1 l")}
    )

    assert result["values"] == {}
    assert result["claims"] == []
    assert result["reasons"] == [{"code": QUANTITY_AMBIGUOUS}]


def test_multiple_simple_quantities_without_relation_fail_closed():
    result = normalize_product_attributes(
        {"product_name": "Birra 330 ml confezione 990 ml"}
    )

    assert result["values"] == {}
    assert result["claims"] == []
    assert result["reasons"] == [{"code": QUANTITY_AMBIGUOUS}]


def test_word_composite_quantity_is_retailer_neutral():
    raw = "Conf. 3 pezzi da 330 ml 990 ml"

    carrefour = normalize_product_attributes(
        {
            "retailer": "carrefour",
            "product_name": raw,
        }
    )
    other = normalize_product_attributes(
        {
            "retailer": "any-other-retailer",
            "product_name": raw,
        }
    )

    assert carrefour == other
    assert carrefour["values"]["volume_ml"] == 990


def test_real_raffo_quantity_normalizes_from_generic_relation():
    result = normalize_product_attributes(
        {
            "product_name": (
                "Raffo Birra Raffo Originale Conf. 3 pz da 330 ml Cad. 990 ml"
            )
        }
    )

    assert result["values"] == {
        "pack_count": 3,
        "quantity": {
            "value": 990,
            "unit": "ml",
            "dimension": "volume",
        },
        "total_quantity": {
            "value": 990,
            "unit": "ml",
            "dimension": "volume",
        },
        "unit_quantity": {
            "value": 330,
            "unit": "ml",
            "dimension": "volume",
        },
        "volume_ml": 990,
    }
    assert result["reasons"] == []


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


def test_dark_chocolate_family_accepts_supported_real_bar_examples():
    examples = (
        "Vanini fondente 95% 90 g",
        "Vanini fondente 91% 90 g",
        "Vanini fondente assoluto 100% 90 g",
        "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
        "Otto Chocolates Cioccolato Fondente 60% Senza Zucchero Nocciole Intere 100 g",
    )

    for product_name in examples:
        result = normalize_product_attributes(
            {"product_name": product_name},
            product_family_candidate=family(),
        )

        assert result["values"]["product_family"] == "dark_chocolate"
        assert not any(
            item["code"] == FAMILY_EVIDENCE_MISMATCH for item in result["reasons"]
        )


def test_dark_chocolate_family_rejects_explicit_conflicting_product_forms():
    examples = (
        "Bahlsen Waffeletten Fondente 100 g",
        "Alfajor ricoperto di cioccolato fondente 150 g",
        "Misura Fibrextra Biscotti integrali Cioccolato Fondente 260 g",
        "Misura Fibrextra 6 Cornetti integrali Cioccolato Fondente 308 g",
        "Oro Saiwa Grano Fondente - frollini integrali con gocce di cioccolato fondente - 300g",
        "Perfect Bio Granola Cacao Fondente e Cocco 250 g",
        "FITNESS Cioccolato Fondente Cereali Integrali con Fiocchi al Cioccolato 325g",
        "Nature Valley Crunchy Fiocchi d'Avena con Cioccolato Fondente 5 x 42 g",
        "NUII Mini Adventure Caramello Salato e Noci Macadamia e Cioccolato Fondente e Mirtilli 6 Gelati 253g",
        "Fiorentini gli Originali Mini Choco Mais Cioccolato Fondente 60 g",
        "Fiorentini i Croccanti Quadrotti di Riso Cioccolato Fondente 80 g",
        "tulipano gocce di cioccolato fondente 250 g",
    )

    for product_name in examples:
        result = normalize_product_attributes(
            {"product_name": product_name},
            product_family_candidate=family(),
        )

        assert "product_family" not in result["values"]
        assert any(
            item["code"] == FAMILY_EVIDENCE_MISMATCH for item in result["reasons"]
        )


def test_dark_chocolate_conflicting_form_rule_is_retailer_neutral():
    product_name = "Bahlsen Waffeletten Fondente 100 g"

    left = normalize_product_attributes(
        {
            "retailer": "esselunga",
            "product_name": product_name,
        },
        product_family_candidate=family(),
    )
    right = normalize_product_attributes(
        {
            "retailer": "any-other-retailer",
            "product_name": product_name,
        },
        product_family_candidate=family(),
    )

    assert left == right
    assert "product_family" not in left["values"]
    assert any(item["code"] == FAMILY_EVIDENCE_MISMATCH for item in left["reasons"])


def test_dark_chocolate_conflict_requires_explicit_observed_phrase():
    result = normalize_product_attributes(
        {"product_name": ("Cioccolato fondente con riso soffiato 100 g")},
        product_family_candidate=family(),
    )

    assert result["values"]["product_family"] == "dark_chocolate"


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
