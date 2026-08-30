import json
from dataclasses import dataclass
from urllib.request import urlopen

from url_validation import validate_esselunga_url

BASE_URL = "https://www.esselunga.it/services/istituzionale35/"


@dataclass(frozen=True)
class EsselungaStore:
    store_code: str
    name: str
    city: str
    city_code: str
    province: str


def discover_stores_by_town(town_id: int) -> list[dict]:
    url = (
        f"{BASE_URL}search-stores-by-town"
        f".townId:{town_id}"
        f".includeLaEsse:false"
        f".storeType:ALL"
        f".json"
    )

    validated_url = validate_esselunga_url(url)
    with urlopen(validated_url) as response:  # noqa: S310
        payload = json.load(response)

    if not isinstance(payload, list):
        raise ValueError("unexpected store discovery payload")

    return payload


def resolve_store(store_code: str) -> EsselungaStore:
    url = f"{BASE_URL}info-stores-by-abbrev.abbrev:{store_code}.json"

    validated_url = validate_esselunga_url(url)
    with urlopen(validated_url) as response:  # noqa: S310
        payload = json.load(response)

    if not isinstance(payload, dict):
        raise ValueError("unexpected store payload")

    return EsselungaStore(
        store_code=payload["abbrev"],
        name=payload["descBreveClienti"],
        city=payload["town"]["name"],
        city_code=str(payload["town"]["id"]),
        province=payload["province"],
    )


def resolve_town_stores(town_id: int) -> list[EsselungaStore]:
    refs = discover_stores_by_town(town_id)

    return [resolve_store(ref["code"]) for ref in refs]


if __name__ == "__main__":
    stores = resolve_town_stores(1642)

    assert stores
    assert stores[0].store_code == "ARI"
    assert stores[0].name == "Esselunga di Porcari"
    assert stores[0].city == "Porcari"
    assert stores[0].city_code == "1642"
    assert stores[0].province == "LU"

    print("resolve_town_stores: PASS")

    for store in stores:
        print(store)
