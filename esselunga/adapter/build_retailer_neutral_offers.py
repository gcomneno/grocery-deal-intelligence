from dataclasses import dataclass
from datetime import UTC, datetime

from extract_offers import EsselungaOffer, extract_offers


@dataclass(frozen=True)
class RetailerNeutralOffer:
    retailer: str
    product_name: str
    classification: str | None
    campaign_url: str
    regions: list[str] | None
    source_type: str
    source_url: str
    observed_at: str
    region_id: str | None
    price: float
    currency: str
    reference_price: float | None
    discount_text: str | None
    promotion_type: str | None
    requires_lidl_plus: bool | None
    packaging_text: str | None
    base_price_text: str | None
    valid_from: str | None
    valid_to: str | None
    price_status: str


def campaign_url(cod_promo: str, store_code: str) -> str:
    return (
        "https://www.esselunga.it/it-it/promozioni/volantini/"
        f"volantino-digitale.sconti-fino-al-50."
        f"{store_code.lower()}.{cod_promo}.html"
    )


def source_url(store_code: str, cod_promo: str) -> str:
    return (
        "https://www.esselunga.it/services/istituzionale35/"
        "digital-grid.condition:nav_menu"
        f".abbrev:{store_code}"
        ".page:0.rows:1000"
        f".codPromo:{cod_promo}.json"
    )


def discount_text(offer: EsselungaOffer) -> str | None:
    if offer.discount_percent:
        return f"{offer.discount_percent}%"

    return None


def price_status(offer: EsselungaOffer) -> str:
    if offer.promotional_price < offer.regular_price:
        return "promo"

    return "regular"


def normalize_offer(
    offer: EsselungaOffer,
    observed_at: str,
) -> RetailerNeutralOffer:
    return RetailerNeutralOffer(
        retailer="esselunga",
        product_name=offer.product_name,
        # Esselunga does not currently expose the
        # retailer-neutral classification contract directly.
        classification=None,
        campaign_url=campaign_url(
            offer.cod_promo,
            offer.store_code,
        ),
        # Store geography is not automatically a "region"
        # in the common contract.
        regions=None,
        source_type="retailer_api",
        source_url=source_url(
            offer.store_code,
            offer.cod_promo,
        ),
        observed_at=observed_at,
        region_id=None,
        price=offer.promotional_price,
        currency="EUR",
        reference_price=offer.regular_price,
        discount_text=discount_text(offer),
        promotion_type=offer.mechanic_description,
        # Esselunga's Fìdaty is not Lidl Plus.
        # Do not collapse retailer-specific loyalty semantics.
        requires_lidl_plus=None,
        packaging_text=None,
        base_price_text=None,
        valid_from=offer.valid_from or None,
        valid_to=offer.valid_to or None,
        price_status=price_status(offer),
    )


def build_retailer_neutral_offers(
    store_code: str,
    cod_promo: str,
) -> list[RetailerNeutralOffer]:
    offers = extract_offers(
        store_code,
        cod_promo,
    )

    observed_at = (
        datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )

    return [
        normalize_offer(
            offer,
            observed_at,
        )
        for offer in offers
    ]


if __name__ == "__main__":
    offers = build_retailer_neutral_offers(
        "ARI",
        "8260",
    )

    assert len(offers) == 1156
    assert len({offer.product_name for offer in offers}) > 0

    first = offers[0]

    assert first.retailer == "esselunga"
    assert first.product_name == ("F.lli Orsero Ananas Tronchetto 500 g")

    assert first.price == 4.88
    assert first.reference_price == 6.98
    assert first.currency == "EUR"
    assert first.discount_text == "30%"
    assert first.promotion_type == "Sconto %"

    assert first.requires_lidl_plus is None
    assert first.classification is None
    assert first.region_id is None
    assert first.regions is None

    assert first.valid_from == "2026-08-13T00:00:00Z"
    assert first.valid_to == "2026-08-26T00:00:00Z"
    assert first.price_status == "promo"

    print("build_retailer_neutral_offers: PASS")
    print("offers:", len(offers))
    print(first)
