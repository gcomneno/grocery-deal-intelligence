from pathlib import Path
import json

from extract_offers import extract_mechanics, extract_price, extract_validity


CAMPAIGNS = [
    ("8260", Path("../esselunga/all-8260.json")),
    ("8400", Path("../esselunga/all-8400.json")),
    ("8340", Path("../esselunga/all-8340.json")),
    ("8580", Path("../esselunga/all-8580.json")),
]


total_items = 0
total_offers = 0

for code, path in CAMPAIGNS:
    if not path.exists():
        raise SystemExit(f"Missing campaign payload: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["status"] == "OK"

    items = payload.get("items") or []

    campaign_offers = 0

    for item in items:
        mechanics = extract_mechanics(item)
        prices = extract_price(item)
        validity = extract_validity(item)

        assert item.get("code")
        assert item.get("title")
        assert mechanics["code"] is not None
        assert validity["from"]
        assert validity["to"]

        if mechanics["is_offer"]:
            assert prices["promo_price"] is not None
            campaign_offers += 1

    total_items += len(items)
    total_offers += campaign_offers

    print(
        f"campaign={code} "
        f"items={len(items)} "
        f"offers={campaign_offers}"
    )


assert total_items == 1234
assert total_offers > 0

print("verify_campaign_payloads: PASS")
print(f"campaigns verified: {len(CAMPAIGNS)}")
print(f"items verified: {total_items}")
print(f"offers verified: {total_offers}")
