from dataclasses import dataclass
from urllib.request import urlopen
import json


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

    with urlopen(url) as response:
        payload = json.load(response)

    if not isinstance(payload, list):
        raise ValueError("unexpected store discovery payload")

    return payload


def resolve_store(store_code: str) -> EsselungaStore:
    url = (
        f"{BASE_URL}info-stores-by-abbrev"
        f".abbrev:{store_code}"
        f".json"
    )

    with urlopen(url) as response:
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

    stores = []

    for ref in refs:
        stores.append(resolve_store(ref["code"]))

    return stores


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
