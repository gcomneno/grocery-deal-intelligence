import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "data/output/lidl-lucca-current.json"
OUTPUT = ROOT / "data/output/lidl-lucca-current-retailer-neutral.json"


def map_record(item):
    return {
        "retailer": item["retailer"],
        "product_name": item["product_name"],
        "price": item["price"],
        "currency": item["currency"],
        "reference_price": item.get("reference_price"),
        "packaging_text": item.get("packaging_text"),
        "base_price_text": item.get("base_price_text"),
        "promotion": {
            "type": item.get("promotion_type"),
            "requires_loyalty": item.get("requires_loyalty", False),
            "discount_text": item.get("discount_text"),
        },
        "validity": {
            "from": item.get("valid_from"),
            "to": item.get("valid_to"),
        },
        "locality": {
            "scope": "regional",
            "stores": item.get("locality", {}).get("stores", []),
            "offer_region": item.get("locality", {}).get("offer_region"),
            "offer_region_name": item.get("locality", {}).get("offer_region_name"),
        },
        "verification": {
            "locality_status": (
                "verified"
                if item.get("verification", {}).get("locality") == "verified"
                else "unverified"
            ),
            "evidence_status": (
                "verified"
                if item.get("verification", {}).get("flyer_match") == "exact"
                else "unmatched"
            ),
            "flyer_pages": item.get("verification", {}).get(
                "flyer_pages",
                [],
            ),
        },
        "provenance": {
            "source_type": item.get("provenance", {}).get("source_type"),
            "source_url": item.get("provenance", {}).get("campaign_url"),
            "observed_at": item.get("provenance", {}).get("observed_at"),
            "flyer_id": item.get("provenance", {}).get("flyer_id"),
        },
    }


def main():
    records = json.loads(SOURCE.read_text(encoding="utf-8"))

    mapped = [map_record(item) for item in records]

    OUTPUT.write_text(
        json.dumps(mapped, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("export_retailer_neutral: PASS")
    print("records:", len(mapped))
    print("output:", OUTPUT)


if __name__ == "__main__":
    main()
