import json
from dataclasses import dataclass
from urllib.request import urlopen

from url_validation import validate_esselunga_url

BASE_URL = "https://www.esselunga.it/services/istituzionale35/search-stores-by-town"


@dataclass(frozen=True)
class EsselungaStoreRef:
    store_code: str
    name: str
    description: str


def discover_stores_by_town(
    town_id: int,
    *,
    include_la_esse: bool = False,
    store_type: str = "ALL",
) -> list[EsselungaStoreRef]:
    url = (
        f"{BASE_URL}"
        f".townId:{town_id}"
        f".includeLaEsse:{str(include_la_esse).lower()}"
        f".storeType:{store_type}"
        f".json"
    )

    validated_url = validate_esselunga_url(url)
    with urlopen(validated_url) as response:  # noqa: S310
        payload = json.load(response)

    if not isinstance(payload, list):
        raise ValueError("unexpected store discovery payload")

    stores = []

    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("unexpected store entry")

        stores.append(
            EsselungaStoreRef(
                store_code=item["code"],
                name=item["name"],
                description=item["description"],
            )
        )

    return stores


if __name__ == "__main__":
    stores = discover_stores_by_town(1642)

    assert stores
    assert stores[0].store_code == "ARI"
    assert stores[0].name == "PORCARI"
    assert stores[0].description == "Esselunga di Porcari"

    print("discover_stores: PASS")

    for store in stores:
        print(store)
