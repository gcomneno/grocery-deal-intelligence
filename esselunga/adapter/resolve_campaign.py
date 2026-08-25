from dataclasses import dataclass
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
import re


@dataclass(frozen=True)
class EsselungaCampaign:
    cod_promo: str
    store_code: str
    url: str


def select_campaign(
    campaign_url: str,
    store_code: str,
) -> EsselungaCampaign:
    if not store_code:
        raise ValueError("missing store code")

    parts = urlsplit(campaign_url)
    path = parts.path

    match = re.search(
        r"\.([A-Za-z0-9]+)\.(\d+)\.html$",
        path,
    )

    if not match:
        raise ValueError(
            f"unsupported Esselunga campaign URL: {campaign_url!r}"
        )

    current_store = match.group(1)
    cod_promo = match.group(2)

    selected_store = store_code.lower()

    selected_path = (
        path[:match.start()]
        + f".{selected_store}.{cod_promo}.html"
    )

    selected_url = (
        f"{parts.scheme}://{parts.netloc}"
        f"{selected_path}"
    )

    if parts.query:
        selected_url += f"?{parts.query}"

    if parts.fragment:
        selected_url += f"#{parts.fragment}"

    return EsselungaCampaign(
        cod_promo=cod_promo,
        store_code=selected_store.upper(),
        url=selected_url,
    )


def verify_campaign(campaign: EsselungaCampaign) -> None:
    request = Request(
        campaign.url,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    with urlopen(request) as response:
        html = response.read().decode(
            "utf-8",
            errors="replace",
        )

    store_match = re.search(
        r'data-store="([^"]+)"',
        html,
    )
    promo_match = re.search(
        r'data-cod-promo="([^"]+)"',
        html,
    )

    if not store_match:
        raise ValueError("campaign page has no data-store")

    if not promo_match:
        raise ValueError("campaign page has no data-cod-promo")

    actual_store = store_match.group(1).upper()
    actual_promo = promo_match.group(1)

    if actual_store != campaign.store_code:
        raise ValueError(
            f"store mismatch: expected {campaign.store_code}, "
            f"got {actual_store}"
        )

    if actual_promo != campaign.cod_promo:
        raise ValueError(
            f"campaign mismatch: expected {campaign.cod_promo}, "
            f"got {actual_promo}"
        )


if __name__ == "__main__":
    source_url = (
        "https://www.esselunga.it/it-it/promozioni/volantini/"
        "volantino-digitale.sconti-fino-al-50.sco.8260.html"
    )

    campaign = select_campaign(source_url, "ARI")

    assert campaign.cod_promo == "8260"
    assert campaign.store_code == "ARI"
    assert campaign.url.endswith(
        "volantino-digitale.sconti-fino-al-50.ari.8260.html"
    )

    verify_campaign(campaign)

    print("resolve_campaign: PASS")
    print(campaign)
