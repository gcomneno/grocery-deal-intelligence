from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from datetime import date, datetime
from typing import Any

from .product_attributes import normalize_product_attributes
from .source_evidence import SUPPORTED

AVAILABLE = "available"
UNKNOWN = "unknown"

EVIDENCE_UNVERIFIED = "availability_evidence_unverified"
LOCALITY_UNVERIFIED = "availability_locality_unverified"
OUTSIDE_REQUESTED_LOCALITY = "availability_outside_requested_locality"
VALIDITY_UNAVAILABLE = "availability_validity_unavailable"
NOT_CURRENT = "availability_not_current"
PRODUCT_FAMILY_MISMATCH = "availability_product_family_mismatch"


def resolve_shopping_item_availability(
    records: Iterable[Mapping[str, Any]],
    *,
    product_family: str,
    as_of: str | date | datetime,
    locality_scope: str | None = None,
    stores: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Resolve verified current availability for one shopping-list item.

    This is a canonical consumer, not a new authority boundary. Input records
    are expected to be already-admitted canonical offers. Product-family
    eligibility is authorized only by the existing deterministic attribute
    verifier.

    Cardinality changes the result shape only:

        0 eligible offers -> unknown
        1+ eligible offers -> available

    Bilateral semantic/economic comparison is deliberately outside this
    resolver.
    """
    if not isinstance(product_family, str) or not product_family.strip():
        raise ValueError("product_family must be a non-empty string")

    resolved_date = _coerce_date(as_of)
    requested_stores = _normalize_requested_stores(stores)

    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for raw_record in records:
        if not isinstance(raw_record, Mapping):
            raise TypeError("availability records must be mappings")

        record = deepcopy(dict(raw_record))

        verification = record.get("verification")
        if (
            not isinstance(verification, Mapping)
            or verification.get("evidence_status") != "verified"
        ):
            rejected.append(_rejection(record, EVIDENCE_UNVERIFIED))
            continue

        family_result = normalize_product_attributes(
            record,
            product_family_candidate={
                "value": product_family,
                "evidence_path": ["product_name"],
            },
        )
        family_claim = _supported_claim(
            family_result,
            path=("product_family",),
            normalized_value=product_family,
        )
        if (
            family_result["values"].get("product_family") != product_family
            or family_claim is None
        ):
            rejected.append(
                _rejection(
                    record,
                    PRODUCT_FAMILY_MISMATCH,
                    details={"attribute_reasons": deepcopy(family_result["reasons"])},
                )
            )
            continue

        validity_code = _validity_rejection_code(
            record.get("validity"),
            resolved_date,
        )
        if validity_code is not None:
            rejected.append(_rejection(record, validity_code))
            continue

        if verification.get("locality_status") != "verified":
            rejected.append(_rejection(record, LOCALITY_UNVERIFIED))
            continue

        locality = record.get("locality")
        if not _locality_matches(
            locality,
            locality_scope=locality_scope,
            stores=requested_stores,
        ):
            rejected.append(_rejection(record, OUTSIDE_REQUESTED_LOCALITY))
            continue

        quantity_claim = _supported_claim(
            family_result,
            path=("quantity",),
        )

        resolved_offer = {
            "retailer": record["retailer"],
            "product_name": record["product_name"],
            "price": deepcopy(record["price"]),
            "currency": record["currency"],
            "validity": deepcopy(record["validity"]),
            "locality": deepcopy(record["locality"]),
            "verification": deepcopy(record["verification"]),
            "provenance": deepcopy(record["provenance"]),
            "product_family": product_family,
            "product_family_claim": deepcopy(family_claim),
        }

        if record.get("packaging_text") is not None:
            resolved_offer["packaging_text"] = deepcopy(record["packaging_text"])

        if quantity_claim is not None:
            resolved_offer["quantity"] = deepcopy(family_result["values"]["quantity"])
            resolved_offer["quantity_claim"] = deepcopy(quantity_claim)

        eligible.append(resolved_offer)

    eligible.sort(key=_offer_sort_key)
    rejected.sort(key=_rejection_sort_key)

    return {
        "status": AVAILABLE if eligible else UNKNOWN,
        "product_family": product_family,
        "as_of": resolved_date.isoformat(),
        "offer_count": len(eligible),
        "offers": eligible,
        "rejections": rejected,
    }


def _coerce_date(value: str | date | datetime) -> date:
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


def _validity_rejection_code(
    validity: Any,
    as_of: date,
) -> str | None:
    if not isinstance(validity, Mapping):
        return VALIDITY_UNAVAILABLE

    valid_from = _parse_validity_date(validity.get("from"))
    valid_to = _parse_validity_date(validity.get("to"))

    if valid_from is None or valid_to is None:
        return VALIDITY_UNAVAILABLE

    if not valid_from <= as_of <= valid_to:
        return NOT_CURRENT

    return None


def _normalize_requested_stores(
    stores: Sequence[str] | None,
) -> tuple[str, ...]:
    if stores is None:
        return ()

    if isinstance(stores, (str, bytes, bytearray)):
        raise TypeError("stores must be a sequence of store identifiers")

    normalized: set[str] = set()
    for store in stores:
        if not isinstance(store, str) or not store.strip():
            raise ValueError("store identifiers must be non-empty strings")
        normalized.add(store)

    return tuple(sorted(normalized))


def _locality_matches(
    locality: Any,
    *,
    locality_scope: str | None,
    stores: tuple[str, ...],
) -> bool:
    if not isinstance(locality, Mapping):
        return False

    if locality_scope is not None and locality.get("scope") != locality_scope:
        return False

    if not stores:
        return True

    observed_stores = locality.get("stores")
    if not isinstance(observed_stores, list):
        return False

    return bool(set(stores).intersection(observed_stores))


def _supported_claim(
    result: Mapping[str, Any],
    *,
    path: tuple[str, ...],
    normalized_value: Any = None,
) -> dict[str, Any] | None:
    for claim in result.get("claims", []):
        if (
            tuple(claim.get("path", ())) == path
            and claim.get("status") == SUPPORTED
            and (
                normalized_value is None
                or claim.get("normalized_value") == normalized_value
            )
        ):
            return claim

    return None


def _rejection(
    record: Mapping[str, Any],
    code: str,
    *,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "code": code,
        "retailer": record.get("retailer"),
        "product_name": record.get("product_name"),
        "validity": deepcopy(record.get("validity")),
        "locality": deepcopy(record.get("locality")),
        "provenance": deepcopy(record.get("provenance")),
    }

    if details:
        result["details"] = deepcopy(dict(details))

    return result


def _offer_sort_key(offer: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        offer["retailer"],
        offer["product_name"],
        offer["price"],
        offer["currency"],
    )


def _rejection_sort_key(
    rejection: Mapping[str, Any],
) -> tuple[str, str, str]:
    return (
        str(rejection.get("retailer") or ""),
        str(rejection.get("product_name") or ""),
        str(rejection.get("code") or ""),
    )
