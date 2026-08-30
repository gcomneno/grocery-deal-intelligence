from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date, datetime

from .validity import coerce_as_of_date, validity_includes


def list_current_offers(
    records: Iterable[Mapping[str, Any]],
    *,
    as_of: str | date | datetime,
    retailer: str | None = None,
) -> list[Mapping[str, Any]]:
    """List currently valid canonical offers, optionally scoped to one retailer."""
    if retailer is not None:
        if not isinstance(retailer, str):
            raise TypeError("retailer must be a string when provided")
        if not retailer.strip():
            raise ValueError("retailer must be a non-empty string")

    resolved_date = coerce_as_of_date(as_of)
    matches: list[Mapping[str, Any]] = []

    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("canonical offer records must be mappings")

        if retailer is not None and record.get("retailer") != retailer:
            continue

        if validity_includes(record.get("validity"), resolved_date):
            matches.append(deepcopy(dict(record)))

    return sorted(matches, key=_offer_sort_key)


def _offer_sort_key(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        record["retailer"],
        record["product_name"],
        record["price"],
        record["currency"],
        _stable_record_key(record),
    )


def _stable_record_key(record: Mapping[str, Any]) -> str:
    return json.dumps(
        record,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
