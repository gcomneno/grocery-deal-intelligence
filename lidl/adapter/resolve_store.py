from dataclasses import dataclass


@dataclass(frozen=True)
class LidlStore:
    object_number: str
    store_id: str
    name: str
    street: str
    city: str
    zip_code: str
    latitude: float
    longitude: float
    offer_region: str
    offer_region_name: str
    zone: str


def normalize_store_id(object_number: str) -> str:
    if len(object_number) != 7:
        raise ValueError(
            f"Unexpected Lidl objectNumber: {object_number!r}"
        )

    return object_number[2:].lstrip("0") or "0"


if __name__ == "__main__":
    assert normalize_store_id("IT01621") == "1621"
    assert normalize_store_id("IT00302") == "302"

    print("resolve_store: PASS")
