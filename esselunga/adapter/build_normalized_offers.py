from dataclasses import dataclass

from extract_offers import EsselungaOffer, extract_offers


@dataclass(frozen=True)
class NormalizedOffer:
    retailer: str
    store_code: str
    campaign_id: str

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


def normalize_offer(
    offer: EsselungaOffer,
) -> NormalizedOffer:
    return NormalizedOffer(
        retailer="esselunga",
        store_code=offer.store_code,
        campaign_id=offer.cod_promo,

        product_code=offer.product_code,
        product_name=offer.product_name,

        regular_price=offer.regular_price,
        promotional_price=offer.promotional_price,
        discount_percent=offer.discount_percent,

        mechanic_code=offer.mechanic_code,
        mechanic_description=offer.mechanic_description,

        valid_from=offer.valid_from,
        valid_to=offer.valid_to,
        flyer=offer.flyer,
    )


def build_normalized_offers(
    store_code: str,
    cod_promo: str,
) -> list[NormalizedOffer]:
    offers = extract_offers(
        store_code,
        cod_promo,
    )

    return [
        normalize_offer(offer)
        for offer in offers
    ]


if __name__ == "__main__":
    offers = build_normalized_offers(
        "ARI",
        "8260",
    )

    assert len(offers) == 1156
    assert len({
        offer.product_code
        for offer in offers
    }) == 1156

    first = offers[0]

    assert first.retailer == "esselunga"
    assert first.store_code == "ARI"
    assert first.campaign_id == "8260"

    assert first.product_code == "758281"
    assert first.product_name == (
        "F.lli Orsero Ananas Tronchetto 500 g"
    )

    assert first.regular_price == 6.98
    assert first.promotional_price == 4.88
    assert first.discount_percent == "30"

    assert first.mechanic_code == "M002"
    assert first.mechanic_description == "Sconto %"

    assert first.valid_from == "2026-08-13T00:00:00Z"
    assert first.valid_to == "2026-08-26T00:00:00Z"
    assert first.flyer is True

    print("build_normalized_offers: PASS")
    print("normalized offers:", len(offers))
    print(first)
