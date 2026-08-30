from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

VALIDITY_CURRENT = "current"
VALIDITY_NOT_CURRENT = "not_current"
VALIDITY_UNAVAILABLE = "unavailable"


def coerce_as_of_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not isinstance(value, str) or not value.strip():
        raise ValueError("as_of must be an ISO date or datetime")

    observed = value.strip()

    try:
        return date.fromisoformat(observed)
    except ValueError:
        pass

    try:
        return datetime.fromisoformat(observed).date()
    except ValueError as exc:
        raise ValueError("as_of must be an ISO date or datetime") from exc


def validity_status(validity: Any, as_of: date) -> str:
    if not isinstance(validity, Mapping):
        return VALIDITY_UNAVAILABLE

    valid_from = _parse_validity_date(validity.get("from"))
    valid_to = _parse_validity_date(validity.get("to"))

    if valid_from is None or valid_to is None:
        return VALIDITY_UNAVAILABLE

    if not valid_from <= as_of <= valid_to:
        return VALIDITY_NOT_CURRENT

    return VALIDITY_CURRENT


def validity_includes(validity: Any, as_of: date) -> bool:
    return validity_status(validity, as_of) == VALIDITY_CURRENT


def _parse_validity_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None

    observed = value.strip()

    try:
        return date.fromisoformat(observed)
    except ValueError:
        pass

    try:
        return datetime.fromisoformat(observed).date()
    except ValueError:
        return None
