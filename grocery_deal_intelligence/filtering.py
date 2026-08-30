from collections.abc import Iterable, Mapping
from typing import Any


def filter_offers(
    records: Iterable[Mapping[str, Any]],
    *,
    retailer: str | None = None,
    locality_scope: str | None = None,
    locality_status: str | None = None,
    evidence_status: str | None = None,
    requires_loyalty: bool | None = None,
) -> list[Mapping[str, Any]]:
    matches = [
        record
        for record in records
        if (retailer is None or record["retailer"] == retailer)
        and (locality_scope is None or record["locality"]["scope"] == locality_scope)
        and (
            locality_status is None
            or record["verification"]["locality_status"] == locality_status
        )
        and (
            evidence_status is None
            or record["verification"]["evidence_status"] == evidence_status
        )
        and (
            requires_loyalty is None
            or record["promotion"]["requires_loyalty"] == requires_loyalty
        )
    ]

    return sorted(
        matches,
        key=lambda record: (
            record["retailer"],
            record["product_name"],
            record["price"],
            record["currency"],
        ),
    )
