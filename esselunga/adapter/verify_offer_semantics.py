from collections import Counter

from extract_offers import extract_offers

EXPECTED_MECHANICS = {
    "M000": "EVIDENZIAZIONE SENZA OFFERTA",
    "M001": "EVIDENZIAZIONE PREZZO FISSO",
    "M002": "Sconto %",
    "M003": "Prezzo Corto",
    "M004": "P. Fragola",
    "M005": "Sc % Fidaty",
    "M009": "1 + 1",
    "M014": "Sc + Facile val",
}


def main():
    offers = extract_offers("ARI", "8260")

    assert offers, "no offers extracted"

    mechanics = Counter(offer.mechanic_code for offer in offers)

    print("===== MECHANICS =====")

    for code, description in EXPECTED_MECHANICS.items():
        count = mechanics.get(code, 0)

        if count:
            print(f"{code}\t{description}\t{count}")

    print()
    print("===== SEMANTIC CHECKS =====")

    for offer in offers:
        code = offer.mechanic_code

        if code and code not in EXPECTED_MECHANICS:
            raise AssertionError(f"unknown mechanic: {code!r}")

        if offer.regular_price < 0:
            raise AssertionError(f"negative regular price: {offer.product_code}")

        if offer.promotional_price < 0:
            raise AssertionError(f"negative promotional price: {offer.product_code}")

        if code == "M002":
            assert offer.discount_percent != "", (
                f"M002 without discount: {offer.product_code}"
            )

        if code == "M005":
            assert offer.discount_percent != "", (
                f"M005 without discount: {offer.product_code}"
            )

        if code == "M009":
            assert offer.promotional_price == offer.regular_price, (
                f"M009 price mismatch: {offer.product_code}"
            )

        if code == "M014":
            assert offer.promotional_price <= offer.regular_price, (
                f"M014 promo > regular: {offer.product_code}"
            )

    print("verify_offer_semantics: PASS")
    print("offers verified:", len(offers))


if __name__ == "__main__":
    main()
