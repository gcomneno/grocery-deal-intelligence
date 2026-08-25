from pathlib import Path
import json
from datetime import datetime, timezone

from build_retailer_neutral_offers import (
    build_retailer_neutral_offers,
)


ROOT = Path(__file__).resolve().parent.parent

OUTPUT = (
    ROOT
    / "data/output/esselunga-porcari-current-retailer-neutral.json"
)


def map_record(item):
    requires_loyalty = (
        item.promotion_type == "Sc % Fidaty"
    )

    return {
        "retailer": item.retailer,
        "product_name": item.product_name,
        "price": item.price,
        "currency": item.currency,
        "reference_price": item.reference_price,
        "packaging_text": item.packaging_text,
        "base_price_text": item.base_price_text,

        "promotion": {
            "type": item.promotion_type,
            "requires_loyalty": requires_loyalty,
            "discount_text": item.discount_text,
        },

        "validity": {
            "from": item.valid_from,
            "to": item.valid_to,
        },

        "locality": {
            "scope": "store",
            "stores": [item.region_id]
            if item.region_id
            else [],
            "store_code": item.store_code,
            "campaign_id": item.campaign_id,
        },

        "verification": {
            "locality_status": "verified",
            "evidence_status": "verified",
        },

        "provenance": {
            "source_type": item.source_type,
            "source_url": item.source_url,
            "observed_at": item.observed_at,
        },
    }


def main():
    store_code = "ARI"
    campaign_id = "8260"

    offers = build_retailer_neutral_offers(
        store_code,
        campaign_id,
    )

    records = []

    for offer in offers:
        source_url = (
            "https://www.esselunga.it/services/istituzionale35/"
            "digital-grid.condition:nav_menu"
            f".abbrev:{store_code}"
            ".page:0.rows:1000"
            f".codPromo:{campaign_id}.json"
        )

        campaign_url = (
            "https://www.esselunga.it/it-it/promozioni/volantini/"
            "volantino-digitale.sconti-fino-al-50."
            f"{store_code.lower()}."
            f"{campaign_id}.html"
        )

        records.append({
            "retailer": offer.retailer,
            "product_name": offer.product_name,
            "price": offer.price,
            "currency": offer.currency,
            "reference_price": offer.reference_price,
            "packaging_text": offer.packaging_text,
            "base_price_text": offer.base_price_text,

            "promotion": {
                "type": offer.promotion_type,
                "requires_loyalty": (
                    offer.promotion_type == "Sc % Fidaty"
                ),
                "discount_text": offer.discount_text,
            },

            "validity": {
                "from": offer.valid_from,
                "to": offer.valid_to,
            },

            "locality": {
                "scope": "store",
                "stores": [store_code],
            },

            "verification": {
                "locality_status": "verified",
                "evidence_status": "verified",
            },

            "provenance": {
                "source_type": "retailer_api",
                "source_url": source_url,
                "observed_at": offer.observed_at,
                "campaign_url": campaign_url,
                "store_code": store_code,
                "campaign_id": campaign_id,
            },
        })

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            records,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print("export_retailer_neutral: PASS")
    print("records:", len(records))
    print("output:", OUTPUT)


if __name__ == "__main__":
    main()
