def extract_price_variants(product):
    regions_prices = product.get("regionsPrices") or {}

    results = []

    for region_id, region_data in regions_prices.items():
        price_data = None
        promotion_type = None
        requires_loyalty = False

        if region_data.get("currentPrice"):
            price_data = region_data["currentPrice"]
            promotion_type = "standard"

        elif region_data.get("currentLidlPlusPrice"):
            wrapper = region_data["currentLidlPlusPrice"]
            price_data = wrapper.get("price")
            promotion_type = "lidl_plus"
            requires_loyalty = True

        if not price_data:
            continue

        discount = price_data.get("discount") or {}
        packaging = price_data.get("packaging") or {}
        base_price = price_data.get("basePrice") or {}

        results.append(
            {
                "region_id": region_id,
                "price": price_data.get("price"),
                "currency": price_data.get("currencyCode"),
                "reference_price": (
                    price_data.get("oldPrice") or discount.get("deletedPrice")
                ),
                "discount_text": discount.get("discountText"),
                "promotion_type": promotion_type,
                "requires_loyalty": requires_loyalty,
                "packaging_text": packaging.get("text"),
                "base_price_text": base_price.get("text"),
                "valid_from": price_data.get("startDate"),
                "valid_to": (
                    price_data.get("endDateExclusive") or price_data.get("endDate")
                ),
            }
        )

    return results


if __name__ == "__main__":
    standard = {
        "regionsPrices": {
            "1": {
                "currentPrice": {
                    "price": 1.19,
                    "currencyCode": "EUR",
                    "packaging": {"text": "1,25 kg confezione"},
                    "basePrice": {"text": "1 kg = da 1.19 a 0.95 €"},
                    "discount": {"discountText": "250 G IN PIÙ"},
                    "startDate": "2026-08-14T12:32:40Z",
                    "endDateExclusive": "2026-08-26T22:00Z",
                }
            }
        }
    }

    lidl_plus = {
        "regionsPrices": {
            "1": {
                "currentLidlPlusPrice": {
                    "price": {
                        "price": 1.79,
                        "currencyCode": "EUR",
                        "oldPrice": 2.49,
                        "packaging": {"text": "500 g confezione"},
                        "basePrice": {"text": "1 kg = 3.58 €"},
                        "discount": {
                            "deletedPrice": 2.49,
                            "discountText": "-28%",
                        },
                        "startDate": "2026-08-14T12:32:41Z",
                        "endDateExclusive": "2026-08-26T22:00Z",
                    }
                }
            }
        }
    }

    a = extract_price_variants(standard)[0]
    b = extract_price_variants(lidl_plus)[0]

    assert a["price"] == 1.19
    assert a["promotion_type"] == "standard"
    assert a["requires_loyalty"] is False

    assert b["price"] == 1.79
    assert b["reference_price"] == 2.49
    assert b["promotion_type"] == "lidl_plus"
    assert b["requires_loyalty"] is True

    print("extract_offers: PASS")
