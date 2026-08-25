from dataclasses import dataclass


@dataclass(frozen=True)
class EsselungaStore:
    store_code: str
    name: str
    city: str
    city_code: str
    province: str


def resolve_store(payload: dict) -> EsselungaStore:
    return EsselungaStore(
        store_code=payload["abbrev"],
        name=payload["descBreveClienti"],
        city=payload["town"]["name"],
        city_code=str(payload["town"]["id"]),
        province=payload["province"],
    )


def validate_store(store: EsselungaStore) -> None:
    if not store.store_code:
        raise ValueError("missing store code")
    if not store.name:
        raise ValueError("missing store name")
    if not store.city:
        raise ValueError("missing city")
    if not store.city_code:
        raise ValueError("missing city code")
    if not store.province:
        raise ValueError("missing province")


if __name__ == "__main__":
    porcar_payload = {
        "abbrev": "ARI",
        "descBreveClienti": "Esselunga di Porcari",
        "province": "LU",
        "town": {
            "id": 1642,
            "name": "Porcari",
        },
    }

    store = resolve_store(porcar_payload)
    validate_store(store)

    assert store.store_code == "ARI"
    assert store.name == "Esselunga di Porcari"
    assert store.city == "Porcari"
    assert store.city_code == "1642"
    assert store.province == "LU"

    print("resolve_store: PASS")
    print(store)
