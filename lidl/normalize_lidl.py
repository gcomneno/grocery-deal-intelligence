import json
import re
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from typing import Any

SOURCE_URL = "https://www.lidl.it/c/template_sales_campaigns/"

_MALFORMED_GRID_DATA = object()


def _decode_grid_data(raw: str) -> Any:
    try:
        return json.loads(unescape(raw))
    except json.JSONDecodeError:
        return _MALFORMED_GRID_DATA


html = Path("lidl-offers.html").read_text(encoding="utf-8")

matches = re.findall(
    r'data-grid-data="([^"]+)"',
    html,
    flags=re.IGNORECASE,
)

normalized = []

for raw in matches:
    data = _decode_grid_data(raw)
    if data is _MALFORMED_GRID_DATA:
        continue

    title = data.get("title")
    if not title:
        continue

    regions_prices = data.get("regionsPrices") or {}

    for region_id, region_data in regions_prices.items():
        price_data = None
        promotion_type = None
        lidl_plus = False

        if region_data.get("currentPrice"):
            price_data = region_data["currentPrice"]
            promotion_type = "standard"

        elif region_data.get("currentLidlPlusPrice"):
            lp = region_data["currentLidlPlusPrice"]
            price_data = lp.get("price")
            promotion_type = "lidl_plus"
            lidl_plus = True

        if not price_data:
            continue

        discount = price_data.get("discount") or {}
        packaging = price_data.get("packaging") or {}
        base_price = price_data.get("basePrice") or {}

        normalized.append(
            {
                "retailer": "lidl",
                "region_id": region_id,
                "product_name": title,
                "price": price_data.get("price"),
                "currency": price_data.get("currencyCode"),
                "reference_price": (
                    price_data.get("oldPrice") or discount.get("deletedPrice")
                ),
                "discount_text": discount.get("discountText"),
                "promotion_type": promotion_type,
                "requires_lidl_plus": lidl_plus,
                "packaging_text": packaging.get("text"),
                "base_price_text": base_price.get("text"),
                "valid_from": price_data.get("startDate"),
                "valid_to": (
                    price_data.get("endDateExclusive") or price_data.get("endDate")
                ),
                "regions": data.get("regions"),
                "source_type": "official_web",
                "source_url": SOURCE_URL,
                "observed_at": datetime.now(UTC).isoformat(),
            }
        )

Path("lidl-normalized.json").write_text(
    json.dumps(normalized, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("normalized records:", len(normalized))

for item in normalized:
    print(
        f"{item['product_name']}: "
        f"{item['price']} {item['currency']} | "
        f"{item['packaging_text']} | "
        f"{item['promotion_type']} | "
        f"{item['discount_text']}"
    )
