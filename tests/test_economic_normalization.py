import copy
import unittest

from grocery_deal_intelligence.economic_normalization import (
    CURRENCY_UNSUPPORTED,
    QUANTITY_AMBIGUOUS,
    QUANTITY_CLAIM_MISMATCH,
    QUANTITY_UNAVAILABLE,
    normalize_economic_basis,
)
from grocery_deal_intelligence.product_attributes import normalize_product_attributes


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

    def test_mass_basis_uses_current_price_and_exact_decimal_arithmetic(self):
        offer = self.offer(price=2.49, packaging_text="100 g", reference_price=3.99)
        attributes = normalize_product_attributes(offer)
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["result"]["current_price"]["value"], "2.49")
        self.assertEqual(result["result"]["comparable_price"]["value"], "24.9")
        self.assertEqual(result["result"]["comparable_price"]["per_unit"], "kg")
        self.assertEqual(result["result"]["derivation"]["rule_id"], "builtin:eur-per-kg:v0.1")

    def test_volume_basis(self):
        offer = self.offer(price=1.09, packaging_text="1 l")
        attributes = normalize_product_attributes(offer)
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["result"]["quantity"]["value"], "1000")
        self.assertEqual(result["result"]["quantity"]["dimension"], "volume")
        self.assertEqual(result["result"]["comparable_price"]["value"], "1.09")
        self.assertEqual(result["result"]["comparable_price"]["per_unit"], "l")

    def test_composite_pack_uses_total_mass(self):
        offer = self.offer(price=3, packaging_text="2 x 100 g")
        attributes = normalize_product_attributes(offer)
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["result"]["quantity"]["value"], "200")
        self.assertEqual(result["result"]["comparable_price"]["value"], "15")

    def test_reference_price_is_never_numerator(self):
        offer = self.offer(price=2, packaging_text="100 g", reference_price=1)
        attributes = normalize_product_attributes(offer)
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["result"]["current_price"]["value"], "2")
        self.assertEqual(result["result"]["comparable_price"]["value"], "20")

    def test_not_comparable_fails_closed_even_with_quantity(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        result = normalize_economic_basis(offer, attributes, comparable=False)

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasons"][0]["code"], "comparison_not_admitted")

    def test_unsupported_currency_fails_closed(self):
        offer = self.offer(currency="USD")
        attributes = normalize_product_attributes(offer)
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasons"][0]["code"], CURRENCY_UNSUPPORTED)

    def test_missing_quantity_claim_fails_closed(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        attributes["claims"] = [
            claim for claim in attributes["claims"] if claim["path"] != ["weight_g"]
        ]
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasons"][0]["code"], QUANTITY_CLAIM_MISMATCH)

    def test_stale_supported_claim_cannot_authorize_altered_value(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        attributes["values"]["weight_g"] = 80
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasons"][0]["code"], QUANTITY_CLAIM_MISMATCH)

    def test_forged_supported_claim_without_normalized_value_fails_closed(self):
        offer = self.offer()
        attributes = {
            "version": "0.1",
            "values": {"weight_g": 100},
            "claims": [{"path": ["weight_g"], "status": "supported"}],
            "reasons": [],
        }
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["status"], "unknown")
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
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasons"][0]["code"], QUANTITY_AMBIGUOUS)

    def test_no_quantity_is_unknown(self):
        offer = self.offer(packaging_text=None)
        attributes = normalize_product_attributes(offer)
        result = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasons"][0]["code"], QUANTITY_UNAVAILABLE)

    def test_inputs_are_immutable_and_output_deterministic(self):
        offer = self.offer()
        attributes = normalize_product_attributes(offer)
        offer_before = copy.deepcopy(offer)
        attributes_before = copy.deepcopy(attributes)

        first = normalize_economic_basis(offer, attributes, comparable=True)
        second = normalize_economic_basis(offer, attributes, comparable=True)

        self.assertEqual(first, second)
        self.assertEqual(offer, offer_before)
        self.assertEqual(attributes, attributes_before)


if __name__ == "__main__":
    unittest.main()
