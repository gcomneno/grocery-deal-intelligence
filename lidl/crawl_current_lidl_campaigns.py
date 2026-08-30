import json
import re
import shutil
import subprocess
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

BASE = "https://www.lidl.it"

_MALFORMED_GRID_DATA = object()

_CURL = shutil.which("curl")
if _CURL is None:
    raise RuntimeError("curl executable is required to crawl Lidl campaigns")
CURL = str(Path(_CURL).resolve())


def _decode_grid_data(raw: str) -> Any:
    try:
        return json.loads(unescape(raw))
    except json.JSONDecodeError:
        return _MALFORMED_GRID_DATA


CAMPAIGNS = [
    "/c/lidl-plus-kw-34-26/a10101068",
    "/c/xxl-kw-34-26/a10100002",
    "/c/frutta-e-verdura-kw-34-26/a10101066",
    "/c/carne-e-pesce-kw-34-26/a10101067",
    "/c/super-offerte-kw-34-26/a10101069",
    "/c/inflazione-zero-kw-34-26/a10101071",
    "/c/duc-de-coeur-sapori-in-stile-francese-kw-34-26/a10100003",
]

all_products = []

for campaign in CAMPAIGNS:
    url = urljoin(BASE, campaign)

    print(f"\n===== {url} =====")

    try:
        # CURL is resolved once with shutil.which and executed with shell=False.
        body = subprocess.check_output(  # noqa: S603
            [CURL, "-Ls", url],
            text=True,
            timeout=30,
        )
    except (
        OSError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as exc:
        print("ERROR:", exc)
        continue

    matches = re.findall(
        r'data-grid-data="([^"]+)"',
        body,
        flags=re.IGNORECASE,
    )

    products = []

    for raw in matches:
        data = _decode_grid_data(raw)
        if data is _MALFORMED_GRID_DATA:
            continue

        if not data.get("title"):
            continue

        products.append(data)

        all_products.append(
            {
                "campaign_url": url,
                "data": data,
            }
        )

    print("records:", len(products))

    for product in products:
        print("-", product.get("title"))

# Dedup preliminare per titolo.
dedup = {}

for item in all_products:
    title = item["data"].get("title")
    if not title:
        continue

    dedup.setdefault(title, item)

print("\n===== SUMMARY =====")
print("raw records:", len(all_products))
print("unique titles:", len(dedup))

Path("lidl-current-campaign-products.json").write_text(
    json.dumps(all_products, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("\n===== UNIQUE PRODUCTS =====")

for title in sorted(dedup):
    print("-", title)
