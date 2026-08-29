import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from grocery_deal_intelligence.economic_normalization import (
    COMPARISON_NOT_ADMITTED,
    CURRENCY_UNSUPPORTED,
    PRICE_INVALID,
    QUANTITY_AMBIGUOUS,
    QUANTITY_CLAIM_MISMATCH,
    QUANTITY_UNAVAILABLE,
    normalize_economic_basis,
)
from grocery_deal_intelligence.product_attributes import normalize_product_attributes


ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (ROOT / "schema/economic-normalization-v0.1.schema.json").read_text(encoding="utf-8")
)


class EconomicNormalizationTests(unittest.TestCase):
    def offer(self, *, price=2.49, currency="EUR", packaging_text="100 g", **extra):
        value = {
            "retailer": "Example",
            "product_name": "Cioccolato fondente 70%",
            "price": price,
            "currency": currency,
            "packaging_text": packaging_text,
        }
        value.update(extra)
        return value

    def admitted_decision(self):
        return {
            "relationship": "comparable",
            "eligible": True,
            "reasons": [],
            "evaluated_rules": [
                {
                    "rule_id": "same_weight",
                    "effect": "require",
                    "path": ["weight_g"],
                    "outcome": "satisfied",
                }
            ],
            "policy": {"rules": {"same_weight": {"effect": "require"}}},
        }

    def normalize(self, offer, attributes, decision=None):
        return normalize_economic_basis(
            offer,
            attributes,
            comparison_decision=self.admitted_decision() if decision is None else decision,
        )

    def assert_schema_valid(self, result):
        errors = sorted(Draft202012Validator(SCHEMA).iter_errors(result), key=str)
        self.assertEqual(errors, [])

    def test_mass_basis_uses_current_price_and_exact_ratio(self):
        offer = self.offer(price=2.49, packaging_text="100 g", reference_price=3.99)
        attributes = normalize_product_attributes(offer)
        result = self.normalize(offer, attributes)

        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["result"]["current_price"]["value"], "2.49")
        self.assertEqual(
            result["result"]["comparable_price"]["exact_ratio"],
            {"numerator": "249", "denominator": "10"},
        )
        self.assertEqual(result["result"]["comparable_price"]["per_unit"], "kg")
        self.assert_schema_valid(result)

    def test_volume_basis(self):
        offer = self.offer(price=1.09, packaging_text="1 l")
        attributes = normalize_product_attributes(offer)
        result = self.normalize(offer, attributes)

        self.assertEqual(result["result"]["quantity"]["value"], "1000")
        self.assertEqual(result["result"]["quantity"]["dimension"], "volume")
        self.assertEqual(
            result["result"]["comparable_price"]["exact_ratio"],
            {"numerator": "109", "denominator": "100"},
        )
        self.assertEqual(result["result"]["comparable_price"]["per_unit"], "l")
        self.assert_schema_valid(result)

    def test_non_terminating_decimal_remains_exact_ratio(self):
        offer = self.offer(price=1, packaging_text="300 g")
        attributes = normalize_product_attributes(offer)
        result = self.normalize(offer, attributes)

        self.assertEqual(
            result["result"]["comparable_price"]["exact_ratio"],
            {"numerator": "10", "denominator": "3"},
        )
        self.assert_schema_valid(result)

    def test_composite_pack_uses_total_mass(self):
        offer = self.offer(price=3, packaging_text="2 x 100 g")
        attributes = normalize_product_attributes(offer)
        result = self.normalize(offer, attributes)

        self.assertEqual(result["result"]["quantity"]["value"], "200")
        self.assertEqual(
            result["result"]["comparable_price"]["exact_ratio"],
            {"numerator": "15", "denominator": "1"},
        )

    def test_reference_price_is_never_numerator(self):
        offer = self.offer(price=2, packaging_text="100 g", reference_price=1)
        attributes = normalize_product_attributes(offer)
        result = self.normalize(offer, attributes)

        self.assertEqual(result["result"]["current_price"]["value"], "2")
        self.assertEqual(
            result["result"]["comparable_price"]["exact_ratio"],
            {"numerator": "20", "denominator": "1"},
        )

    def test_free_boolean_cannot_grant_comparability(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        with self.assertRaises(TypeError):
            normalize_economic_basis(offer, attributes, comparison_decision=True)

    def test_structurally_unadmitted_comparison_fails_closed(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        decision = self.admitted_decision()
        decision["eligible"] = False
        result = self.normalize(offer, attributes, decision)

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasons"][0]["code"], COMPARISON_NOT_ADMITTED)
        self.assert_schema_valid(result)

    def test_no_authority_rule_cannot_admit_comparison(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        decision = self.admitted_decision()
        decision["evaluated_rules"] = [
            {
                "rule_id": "brand",
                "effect": "ignore",
                "path": ["brand"],
                "outcome": "non_authoritative",
            }
        ]
        result = self.normalize(offer, attributes, decision)

        self.assertEqual(result["reasons"][0]["code"], COMPARISON_NOT_ADMITTED)

    def test_unsupported_currency_fails_closed(self):
        offer = self.offer(currency="USD")
        attributes = normalize_product_attributes(offer)
        result = self.normalize(offer, attributes)

        self.assertEqual(result["reasons"][0]["code"], CURRENCY_UNSUPPORTED)

    def test_non_finite_price_fails_closed(self):
        offer = self.offer(price="NaN")
        attributes = normalize_product_attributes(offer)
        result = self.normalize(offer, attributes)

        self.assertEqual(result["reasons"][0]["code"], PRICE_INVALID)

    def test_missing_quantity_claim_fails_closed(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        attributes["claims"] = [claim for claim in attributes["claims"] if claim["path"] != ["weight_g"]]
        result = self.normalize(offer, attributes)

        self.assertEqual(result["reasons"][0]["code"], QUANTITY_CLAIM_MISMATCH)

    def test_stale_supported_claim_cannot_authorize_altered_value(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        attributes["values"]["weight_g"] = 80
        result = self.normalize(offer, attributes)

        self.assertEqual(result["reasons"][0]["code"], QUANTITY_CLAIM_MISMATCH)

    def test_forged_supported_claim_without_normalized_value_fails_closed(self):
        offer = self.offer()
        attributes = {
            "version": "0.1",
            "values": {"weight_g": 100},
            "claims": [{"path": ["weight_g"], "status": "supported"}],
            "reasons": [],
        }
        result = self.normalize(offer, attributes)

        self.assertEqual(result["reasons"][0]["code"], QUANTITY_CLAIM_MISMATCH)

    def test_conflicting_duplicate_claims_fail_closed(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        attributes["claims"].append(
            {
                "path": ["weight_g"],
                "status": "supported",
                "evidence_path": ["packaging_text"],
                "raw_value": "80 g",
                "normalized_value": 80,
                "normalization": "deterministic_unit_conversion",
            }
        )
        result = self.normalize(offer, attributes)

        self.assertEqual(result["reasons"][0]["code"], QUANTITY_CLAIM_MISMATCH)

    def test_mass_and_volume_together_are_ambiguous(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        attributes["values"]["volume_ml"] = 100
        attributes["claims"].append(
            {
                "path": ["volume_ml"],
                "status": "supported",
                "evidence_path": ["packaging_text"],
                "raw_value": "100 ml",
                "normalized_value": 100,
                "normalization": "deterministic_unit_conversion",
            }
        )
        result = self.normalize(offer, attributes)

        self.assertEqual(result["reasons"][0]["code"], QUANTITY_AMBIGUOUS)

    def test_no_quantity_is_unknown(self):
        offer = self.offer(packaging_text=None)
        attributes = normalize_product_attributes(offer)
        result = self.normalize(offer, attributes)

        self.assertEqual(result["reasons"][0]["code"], QUANTITY_UNAVAILABLE)

    def test_schema_rejects_supported_null_result(self):
        invalid = {"version": "0.1", "status": "supported", "result": None, "reasons": []}
        self.assertTrue(list(Draft202012Validator(SCHEMA).iter_errors(invalid)))

    def test_schema_rejects_mass_with_litre_basis(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        result = self.normalize(offer, attributes)
        result["result"]["basis"]["unit"] = "l"
        self.assertTrue(list(Draft202012Validator(SCHEMA).iter_errors(result)))

    def test_inputs_are_immutable_and_output_deterministic(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        decision = self.admitted_decision()
        offer_before = copy.deepcopy(offer)
        attributes_before = copy.deepcopy(attributes)
        decision_before = copy.deepcopy(decision)

        first = self.normalize(offer, attributes, decision)
        second = self.normalize(offer, attributes, decision)

        self.assertEqual(first, second)
        self.assertEqual(offer, offer_before)
        self.assertEqual(attributes, attributes_before)
        self.assertEqual(decision, decision_before)


if __name__ == "__main__":
    unittest.main()
