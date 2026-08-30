from build_normalized_offers import build_normalized_offers

CONTRACT_FIELDS = {
    "retailer",
    "product_name",
    "classification",
    "campaign_url",
    "regions",
    "source_type",
    "source_url",
    "observed_at",
    "region_id",
    "price",
    "currency",
    "reference_price",
    "discount_text",
    "promotion_type",
    "requires_lidl_plus",
    "packaging_text",
    "base_price_text",
    "valid_from",
    "valid_to",
    "price_status",
}

ESSSELUNGA_MAPPED_FIELDS = {
    "retailer",
    "product_name",
    "campaign_url",
    "regions",
    "source_type",
    "source_url",
    "observed_at",
    "region_id",
    "price",
    "currency",
    "reference_price",
    "discount_text",
    "promotion_type",
    "packaging_text",
    "base_price_text",
    "valid_from",
    "valid_to",
    "price_status",
}

UNRESOLVED_FIELDS = {
    "classification",
    "requires_lidl_plus",
}


def main():
    offers = build_normalized_offers("ARI", "8260")

    assert offers
    assert CONTRACT_FIELDS - ESSSELUNGA_MAPPED_FIELDS == UNRESOLVED_FIELDS

    print("===== RETAILER-NEUTRAL COMPATIBILITY =====")
    print("contract fields:", len(CONTRACT_FIELDS))
    print("mapped fields:", len(ESSSELUNGA_MAPPED_FIELDS))
    print("unresolved fields:", len(UNRESOLVED_FIELDS))

    print()
    print("===== UNRESOLVED =====")

    for field in sorted(UNRESOLVED_FIELDS):
        print(field)

    print()
    print("verify_retailer_neutral_contract: PASS")
    print("offers inspected:", len(offers))


if __name__ == "__main__":
    main()
