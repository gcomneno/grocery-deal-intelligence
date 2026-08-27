from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DesparOffer:
    product_name: str
    package_text: str
    price_texts: tuple[str, ...]
    promotion_text: str | None


@dataclass(frozen=True)
class DesparFixture:
    source_url: str
    store_id: str
    store_name: str
    store_address: str
    store_locality: str
    campaign_title: str
    valid_from: str
    valid_to: str
    offers: tuple[DesparOffer, ...]


def _parse_offer(parts: list[str]) -> DesparOffer:
    if len(parts) < 3:
        raise ValueError("Despar offer line must contain product, package, and price")

    product_name = parts[0]
    package_text = parts[1]
    tail = parts[2:]

    promotion_text = None
    if tail and tail[-1].lower().startswith(("sconto ", "offerta ")):
        promotion_text = tail[-1]
        tail = tail[:-1]

    if not tail:
        raise ValueError("Despar offer line must contain at least one price")

    return DesparOffer(
        product_name=product_name,
        package_text=package_text,
        price_texts=tuple(tail),
        promotion_text=promotion_text,
    )


def parse_despar_fixture_text(text: str) -> DesparFixture:
    metadata: dict[str, str] = {}
    offers: list[DesparOffer] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("offer: "):
            parts = [part.strip() for part in line.removeprefix("offer: ").split("|")]
            offers.append(_parse_offer(parts))
            continue

        if ": " not in line:
            raise ValueError(f"Unrecognized Despar fixture line: {line}")
        key, value = line.split(": ", 1)
        metadata[key] = value

    required = (
        "source_url",
        "store_id",
        "store_name",
        "store_address",
        "store_locality",
        "campaign_title",
        "valid_from",
        "valid_to",
    )
    missing = [key for key in required if not metadata.get(key)]
    if missing:
        raise ValueError(f"Missing Despar fixture metadata: {', '.join(missing)}")
    if not offers:
        raise ValueError("Despar fixture must contain at least one offer")

    return DesparFixture(
        source_url=metadata["source_url"],
        store_id=metadata["store_id"],
        store_name=metadata["store_name"],
        store_address=metadata["store_address"],
        store_locality=metadata["store_locality"],
        campaign_title=metadata["campaign_title"],
        valid_from=metadata["valid_from"],
        valid_to=metadata["valid_to"],
        offers=tuple(offers),
    )


def load_despar_fixture(path: str | Path) -> DesparFixture:
    return parse_despar_fixture_text(Path(path).read_text(encoding="utf-8"))


def parse_euro_price(price_text: str) -> Decimal:
    token = price_text.split("€", 1)[0].strip().split()[-1]
    return Decimal(token.replace(".", "").replace(",", "."))
