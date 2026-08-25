from dataclasses import dataclass
from urllib.request import urlopen
import json


BASE_URL = (
    "https://www.esselunga.it/services/istituzionale35/"
    "digital-grid"
)


@dataclass(frozen=True)
class EsselungaOffer:
    product_code: str
    product_name: str
    regular_price: float
    promotional_price: float
    discount_percent: str
    mechanic_code: str
    mechanic_description: str
    valid_from: str
    valid_to: str
    flyer: bool
    store_code: str
    cod_promo: str


def extract_offers(
    store_code: str,
    cod_promo: str,
    *,
    page: int = 0,
    rows: int = 1000,
) -> list[EsselungaOffer]:
    url = (
        f"{BASE_URL}"
        f".condition:nav_menu"
        f".abbrev:{store_code}"
        f".page:{page}"
        f".rows:{rows}"
        f".codPromo:{cod_promo}"
        f".json"
    )

    with urlopen(url) as response:
        payload = json.load(response)

    if payload.get("status") != "OK":
        raise ValueError(
            f"unexpected digital-grid status: "
            f"{payload.get('status')!r}"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise ValueError("unexpected digital-grid items")

    offers = []

    # Esselunga may return parent/family records whose real
    # product offers live inside related_items.
    normalized_items = []

    for item in items:
        if item.get("code") and item.get("title"):
            normalized_items.append(item)
            continue

        related_items = item.get("related_items") or []

        if related_items:
            normalized_items.extend(related_items)
            continue

        raise ValueError(
            "offer missing product identity and related_items"
        )

    for item in normalized_items:
        product_code = item.get("code")
        product_name = item.get("title")

        if not product_code or not product_name:
            raise ValueError("related offer missing product identity")

        promo_price = (item.get("promozioni_prezzoPromo") or [None])[0]
        regular_price = item.get("prezzo")

        if promo_price is None:
            promo_price = regular_price

        if regular_price is None or promo_price is None:
            raise ValueError(
                f"offer missing price: {product_code}"
            )

        offers.append(
            EsselungaOffer(
                product_code=str(product_code),
                product_name=product_name,
                regular_price=float(regular_price),
                promotional_price=float(promo_price),
                discount_percent=(
                    (item.get("promozioni_scontoPercentuale") or [""])[0]
                ),
                mechanic_code=(
                    (item.get("promozioni_codMeccanica") or [""])[0]
                ),
                mechanic_description=(
                    (item.get("promozioni_desMeccanica") or [""])[0]
                ),
                valid_from=(
                    (item.get("promozioni_dataInizioPromoArticolo")
                     or [""])[0]
                ),
                valid_to=(
                    (item.get("promozioni_dataFinePromoArticolo")
                     or [""])[0]
                ),
                flyer=bool(
                    (item.get("promozioni_flgVolantino")
                     or [False])[0]
                ),
                store_code=store_code.upper(),
                cod_promo=str(cod_promo),
            )
        )

    return offers


if __name__ == "__main__":
    offers = extract_offers("ARI", "8260")

    assert len(offers) == 1156

    first = offers[0]

    assert first.product_code == "758281"
    assert first.product_name == "F.lli Orsero Ananas Tronchetto 500 g"
    assert first.regular_price == 6.98
    assert first.promotional_price == 4.88
    assert first.discount_percent == "30"
    assert first.mechanic_code == "M002"
    assert first.mechanic_description == "Sconto %"
    assert first.valid_from == "2026-08-13T00:00:00Z"
    assert first.valid_to == "2026-08-26T00:00:00Z"
    assert first.flyer is True
    assert first.store_code == "ARI"
    assert first.cod_promo == "8260"

    assert len({offer.product_code for offer in offers}) == 1156
    assert all(offer.store_code == "ARI" for offer in offers)
    assert all(offer.cod_promo == "8260" for offer in offers)

    print("extract_offers: PASS")
    print("offers:", len(offers))
    print(first)
