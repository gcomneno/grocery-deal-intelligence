import json
import re
import unicodedata
from pathlib import Path

DATASET = Path("lidl-current-food-normalized.json")
FLYER = Path("flyer-api/current.json")


def normalize(text):
    text = (text or "").lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


dataset = json.loads(DATASET.read_text(encoding="utf-8"))
flyer = json.loads(FLYER.read_text(encoding="utf-8"))["flyer"]

pages = []

for page in flyer.get("pages", []):
    text = " ".join(
        [
            page.get("keyWords") or "",
            page.get("altText") or "",
        ]
    )

    pages.append(
        {
            "number": page.get("number"),
            "text": text,
            "normalized": normalize(text),
        }
    )


# Riduciamo a prodotti unici per nome.
products = {}

for item in dataset:
    products.setdefault(item["product_name"], item)


matched = []
unmatched = []

for name, item in products.items():
    needle = normalize(name)

    hits = [page for page in pages if needle in page["normalized"]]

    record = {
        "product_name": name,
        "price": item.get("price"),
        "currency": item.get("currency"),
        "packaging_text": item.get("packaging_text"),
        "promotion_type": item.get("promotion_type"),
        "pages": [p["number"] for p in hits],
    }

    if hits:
        matched.append(record)
    else:
        unmatched.append(record)


print("===== SUMMARY =====")
print("dataset unique products:", len(products))
print("exact normalized matches:", len(matched))
print("unmatched:", len(unmatched))

print("\n===== MATCHED =====")
for item in matched:
    print(
        f"- {item['product_name']}"
        f" | {item['price']} {item['currency']}"
        f" | pages={item['pages']}"
    )

print("\n===== UNMATCHED =====")
for item in unmatched:
    print("-", item["product_name"])

Path("flyer-api/product-verification.json").write_text(
    json.dumps(
        {
            "matched": matched,
            "unmatched": unmatched,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
