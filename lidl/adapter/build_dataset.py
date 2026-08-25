from pathlib import Path
from datetime import datetime, timezone
import json

from classify_food import classify_product
from extract_offers import extract_price_variants
from verify_flyer import find_product_pages


ROOT = Path(__file__).resolve().parent.parent

RAW_PRODUCTS = ROOT / "lidl-current-campaign-products.json"
FLYER_JSON = ROOT / "flyer-api/current.json"
OUTPUT = ROOT / "data/output/lidl-lucca-current.json"

STORES = [
    "IT01621",
    "IT00302",
]

OFFER_REGION = "600"
OFFER_REGION_NAME = "Pontedera - Toscana"


def main():
    raw = json.loads(
        RAW_PRODUCTS.read_text(encoding="utf-8")
    )

    flyer = json.loads(
        FLYER_JSON.read_text(encoding="utf-8")
    )["flyer"]

    pages = flyer.get("pages") or []

    output = []
    observed_at = datetime.now(timezone.utc).isoformat()

    for item in raw:
        data = item.get("data") or {}
        title = (data.get("title") or "").strip()

        if not title:
            continue

        if classify_product(title) != "FOOD":
            continue

        variants = extract_price_variants(data)

        for variant in variants:
            flyer_pages = find_product_pages(title, pages)

            output.append({
                "retailer": "lidl",
                "product_name": title,

                **variant,

                "locality": {
                    "offer_region": OFFER_REGION,
                    "offer_region_name": OFFER_REGION_NAME,
                    "stores": STORES,
                },

                "verification": {
                    "locality": "verified",
                    "flyer_match": (
                        "exact" if flyer_pages else "unmatched"
                    ),
                    "flyer_pages": flyer_pages,
                },

                "provenance": {
                    "source_type": "official_web",
                    "campaign_url": item.get("campaign_url"),
                    "flyer_id": flyer.get("id"),
                    "observed_at": observed_at,
                },
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    exact = sum(
        1
        for item in output
        if item["verification"]["flyer_match"] == "exact"
    )

    print("===== DATASET =====")
    print("records:", len(output))
    print("exact flyer matches:", exact)
    print("unmatched:", len(output) - exact)
    print("output:", OUTPUT)


if __name__ == "__main__":
    main()
