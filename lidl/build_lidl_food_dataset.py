import json
from datetime import UTC, datetime
from pathlib import Path

INPUT = Path("lidl-current-campaign-products.json")
OUTPUT = Path("lidl-current-food-normalized.json")
REJECTED = Path("lidl-current-non-food.json")
UNKNOWN = Path("lidl-current-unknown.json")

FOOD_HINTS = {
    "pollo",
    "carne",
    "pesce",
    "salmone",
    "hamburger",
    "salsiccia",
    "cotoletta",
    "formaggio",
    "mozzarella",
    "gorgonzola",
    "grana",
    "feta",
    "gouda",
    "latte",
    "yogurt",
    "burro",
    "pizza",
    "pasta",
    "spaghetti",
    "cous cous",
    "muesli",
    "cereali",
    "pane",
    "biscotti",
    "cracker",
    "madeleine",
    "quiche",
    "olive",
    "funghi",
    "carciofi",
    "patate",
    "carote",
    "mele",
    "uva",
    "melone",
    "pesche",
    "peperone",
    "verdure",
    "frutta",
    "pomodoro",
    "insalata",
    "tonno",
    "prosciutto",
    "polpette",
    "gelato",
    "birra",
    "vino",
    "chianti",
    "barbera",
    "cedrata",
    "lemon",
    "sushi",
    "lumache",
    "paté",
    "pains",
    "tortilla",
    "snack",
    "polpa",
    "bevanda",
    "bibita",
    "limanda",
    "patatine",
    "camembert",
    "pommes",
}

NON_FOOD_HINTS = {
    "pantaloni",
    "tavolino",
    "asciugapiatti",
    "contenitori",
    "posate",
    "bicchieri",
    "piatti",
    "ciotole",
    "pellicola",
    "vernice",
    "pennelli",
    "deodorante",
    "scarpe",
    "maglia",
    "giacca",
    "lampada",
    "trapano",
    "attrezzi",
    "casalinghi",
}


def normalize_text(value):
    return " ".join((value or "").strip().lower().split())


def classify_product(title):
    text = normalize_text(title)

    if any(token in text for token in NON_FOOD_HINTS):
        return "NON_FOOD"

    if any(token in text for token in FOOD_HINTS):
        return "FOOD"

    return "UNKNOWN"


def extract_price(data):
    regions_prices = data.get("regionsPrices") or {}

    # Per ora prendiamo tutte le region variants presenti.
    results = []

    for region_id, region_data in regions_prices.items():
        price_data = None
        promotion_type = None
        requires_lidl_plus = False

        if region_data.get("currentPrice"):
            price_data = region_data["currentPrice"]
            promotion_type = "standard"

        elif region_data.get("currentLidlPlusPrice"):
            wrapper = region_data["currentLidlPlusPrice"]
            price_data = wrapper.get("price")
            promotion_type = "lidl_plus"
            requires_lidl_plus = True

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
                "requires_lidl_plus": requires_lidl_plus,
                "packaging_text": packaging.get("text"),
                "base_price_text": base_price.get("text"),
                "valid_from": price_data.get("startDate"),
                "valid_to": (
                    price_data.get("endDateExclusive") or price_data.get("endDate")
                ),
            }
        )

    return results


raw = json.loads(INPUT.read_text(encoding="utf-8"))

food = []
non_food = []
unknown = []

observed_at = datetime.now(UTC).isoformat()

for item in raw:
    campaign_url = item.get("campaign_url")
    data = item.get("data") or {}

    title = data.get("title")
    if not title:
        continue

    classification = classify_product(title)

    base_record = {
        "retailer": "lidl",
        "product_name": title.strip(),
        "classification": classification,
        "campaign_url": campaign_url,
        "regions": data.get("regions"),
        "source_type": "official_web",
        "source_url": campaign_url,
        "observed_at": observed_at,
    }

    prices = extract_price(data)

    if not prices:
        record = dict(base_record)
        record["price_status"] = "missing"

        if classification == "FOOD":
            food.append(record)
        elif classification == "NON_FOOD":
            non_food.append(record)
        else:
            unknown.append(record)

        continue

    for price in prices:
        record = {
            **base_record,
            **price,
            "price_status": "present",
        }

        if classification == "FOOD":
            food.append(record)
        elif classification == "NON_FOOD":
            non_food.append(record)
        else:
            unknown.append(record)


def dedup(records):
    result = {}
    for r in records:
        key = (
            r.get("retailer"),
            r.get("product_name"),
            r.get("region_id"),
            r.get("price"),
            r.get("packaging_text"),
            r.get("valid_from"),
            r.get("valid_to"),
            r.get("campaign_url"),
        )
        result[key] = r
    return list(result.values())


food = dedup(food)
non_food = dedup(non_food)
unknown = dedup(unknown)

OUTPUT.write_text(
    json.dumps(food, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

REJECTED.write_text(
    json.dumps(non_food, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

UNKNOWN.write_text(
    json.dumps(unknown, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("===== SUMMARY =====")
print("FOOD:", len(food))
print("NON_FOOD:", len(non_food))
print("UNKNOWN:", len(unknown))

print("\n===== FOOD SAMPLE =====")
for item in food[:20]:
    print(
        f"- {item['product_name']}"
        f" | {item.get('price')} {item.get('currency')}"
        f" | {item.get('packaging_text')}"
        f" | {item.get('promotion_type')}"
        f" | {item.get('discount_text')}"
    )

print("\n===== NON FOOD =====")
for item in non_food:
    print("-", item["product_name"])

print("\n===== UNKNOWN =====")
for item in unknown:
    print("-", item["product_name"])
