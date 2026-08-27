from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CarrefourOffer:
    product_name: str
    discount_text: str | None
    loyalty_text: str | None
    price_texts: tuple[str, ...]


@dataclass(frozen=True)
class CarrefourFixture:
    source_url: str
    store_id: str
    flyer_id: str
    store_name: str
    store_address: str
    store_locality: str
    campaign_title: str
    valid_from: str
    valid_to: str
    offers: tuple[CarrefourOffer, ...]


def _parse_offer(parts: list[str]) -> CarrefourOffer:
    if len(parts) < 2:
        raise ValueError("Carrefour offer line must contain product and price evidence")

    product_name = parts[0]
    tail = parts[1:]
    discount_text = None
    loyalty_text = None

    if tail and tail[0].startswith("-") and tail[0].endswith("%"):
        discount_text = tail.pop(0)
    if tail and "PAYBACK" in tail[0].upper():
        loyalty_text = tail.pop(0)
    if not tail:
        raise ValueError("Carrefour offer line must contain at least one price")

    return CarrefourOffer(
        product_name=product_name,
        discount_text=discount_text,
        loyalty_text=loyalty_text,
        price_texts=tuple(tail),
    )


def parse_carrefour_fixture_text(text: str) -> CarrefourFixture:
    metadata: dict[str, str] = {}
    offers: list[CarrefourOffer] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("offer: "):
            parts = [part.strip() for part in line.removeprefix("offer: ").split("|")]
            offers.append(_parse_offer(parts))
            continue
        if ": " not in line:
            raise ValueError(f"Unrecognized Carrefour fixture line: {line}")
        key, value = line.split(": ", 1)
        metadata[key] = value

    required = (
        "source_url",
        "store_id",
        "flyer_id",
        "store_name",
        "store_address",
        "store_locality",
        "campaign_title",
        "valid_from",
        "valid_to",
    )
    missing = [key for key in required if not metadata.get(key)]
    if missing:
        raise ValueError(f"Missing Carrefour fixture metadata: {', '.join(missing)}")
    if not offers:
        raise ValueError("Carrefour fixture must contain at least one offer")

    return CarrefourFixture(
        source_url=metadata["source_url"],
        store_id=metadata["store_id"],
        flyer_id=metadata["flyer_id"],
        store_name=metadata["store_name"],
        store_address=metadata["store_address"],
        store_locality=metadata["store_locality"],
        campaign_title=metadata["campaign_title"],
        valid_from=metadata["valid_from"],
        valid_to=metadata["valid_to"],
        offers=tuple(offers),
    )


def load_carrefour_fixture(path: str | Path) -> CarrefourFixture:
    return parse_carrefour_fixture_text(Path(path).read_text(encoding="utf-8"))
