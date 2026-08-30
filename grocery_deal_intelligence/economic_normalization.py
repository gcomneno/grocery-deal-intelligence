from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any

from .comparison import COMPARABLE
from .source_evidence import SUPPORTED

SUPPORTED_RESULT = "supported"
UNKNOWN_RESULT = "unknown"
PRICE_UNAVAILABLE = "current_price_unavailable"
PRICE_INVALID = "current_price_invalid"
CURRENCY_UNSUPPORTED = "currency_unsupported"
QUANTITY_UNAVAILABLE = "normalized_quantity_unavailable"
QUANTITY_AMBIGUOUS = "normalized_quantity_ambiguous"
QUANTITY_CLAIM_MISMATCH = "normalized_quantity_claim_mismatch"
COMPARISON_NOT_ADMITTED = "comparison_not_admitted"

_RULES = {
    "weight_g": {
        "dimension": "mass",
        "source_unit": "g",
        "basis_unit": "kg",
        "rule_id": "builtin:eur-per-kg:v0.1",
        "formula": "price_eur * 1000 / weight_g",
    },
    "volume_ml": {
        "dimension": "volume",
        "source_unit": "ml",
        "basis_unit": "l",
        "rule_id": "builtin:eur-per-l:v0.1",
        "formula": "price_eur * 1000 / volume_ml",
    },
}


def normalize_economic_basis(
    offer: Mapping[str, Any],
    attributes: Mapping[str, Any],
    *,
    comparison_decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive an exact comparable-price basis without granting comparability.

    The caller supplies the already-admitted comparison-policy result rather than
    a free boolean. Quantity authority is consumed only when the exact current
    normalized value remains bound to a supported #136 claim. Source text is
    never reparsed here.
    """
    if not isinstance(offer, Mapping):
        raise TypeError("offer must be a mapping")
    if not isinstance(attributes, Mapping):
        raise TypeError("attributes must be a mapping")
    if not isinstance(comparison_decision, Mapping):
        raise TypeError("comparison_decision must be a mapping")

    offer_copy = deepcopy(dict(offer))
    attributes_copy = deepcopy(dict(attributes))
    decision_copy = deepcopy(dict(comparison_decision))

    if not _comparison_is_admitted(decision_copy):
        return _unknown(COMPARISON_NOT_ADMITTED)

    price = _decimal_input(offer_copy.get("price"))
    if price is None:
        code = PRICE_UNAVAILABLE if "price" not in offer_copy else PRICE_INVALID
        return _unknown(code)
    if not price.is_finite() or price < 0:
        return _unknown(PRICE_INVALID)

    currency = offer_copy.get("currency")
    if currency != "EUR":
        return _unknown(CURRENCY_UNSUPPORTED, currency=deepcopy(currency))

    values = attributes_copy.get("values")
    claims = attributes_copy.get("claims")
    if not isinstance(values, Mapping) or not isinstance(claims, list):
        return _unknown(QUANTITY_UNAVAILABLE)

    supported_claims = _supported_claims_by_path(claims)
    candidates: list[tuple[str, Decimal, dict[str, Any]]] = []
    mismatched_paths: list[list[str]] = []

    for key in ("weight_g", "volume_ml"):
        if key not in values:
            continue
        quantity = _decimal_input(values.get(key))
        claim = supported_claims.get((key,))
        if (
            quantity is None
            or not quantity.is_finite()
            or quantity <= 0
            or claim is None
        ):
            mismatched_paths.append([key])
            continue
        claim_value = _decimal_input(claim.get("normalized_value"))
        if (
            claim_value is None
            or not claim_value.is_finite()
            or claim_value != quantity
        ):
            mismatched_paths.append([key])
            continue
        candidates.append((key, quantity, claim))

    if mismatched_paths:
        return _unknown(QUANTITY_CLAIM_MISMATCH, paths=mismatched_paths)
    if not candidates:
        return _unknown(QUANTITY_UNAVAILABLE)
    if len(candidates) != 1:
        return _unknown(QUANTITY_AMBIGUOUS, paths=[[key] for key, _, _ in candidates])

    key, quantity, claim = candidates[0]
    rule = _RULES[key]
    exact_ratio = Fraction(price) * 1000 / Fraction(quantity)

    return {
        "version": "0.1",
        "status": SUPPORTED_RESULT,
        "result": {
            "current_price": {
                "value": _decimal_text(price),
                "currency": "EUR",
                "source_path": ["price"],
            },
            "quantity": {
                "value": _decimal_text(quantity),
                "unit": rule["source_unit"],
                "dimension": rule["dimension"],
                "attribute_path": [key],
                "claim": deepcopy(claim),
            },
            "basis": {
                "quantity": "1",
                "unit": rule["basis_unit"],
                "dimension": rule["dimension"],
            },
            "comparable_price": {
                "currency": "EUR",
                "per_unit": rule["basis_unit"],
                "exact_ratio": {
                    "numerator": str(exact_ratio.numerator),
                    "denominator": str(exact_ratio.denominator),
                },
            },
            "derivation": {
                "rule_id": rule["rule_id"],
                "formula": rule["formula"],
            },
        },
        "reasons": [],
    }


def _comparison_is_admitted(decision: Mapping[str, Any]) -> bool:
    if decision.get("relationship") != COMPARABLE:
        return False
    if decision.get("eligible") is not True:
        return False
    reasons = decision.get("reasons")
    evaluated_rules = decision.get("evaluated_rules")
    policy = decision.get("policy")
    if (
        reasons != []
        or not isinstance(evaluated_rules, list)
        or not isinstance(policy, Mapping)
    ):
        return False

    authority_seen = False
    for item in evaluated_rules:
        if not isinstance(item, Mapping):
            return False
        effect = item.get("effect")
        if effect not in {"require", "exclude"}:
            continue
        authority_seen = True
        if item.get("outcome") != "satisfied":
            return False
    return authority_seen


def _supported_claims_by_path(
    claims: list[Any],
) -> dict[tuple[str, ...], dict[str, Any]]:
    supported: dict[tuple[str, ...], dict[str, Any]] = {}
    conflicted: set[tuple[str, ...]] = set()
    for claim in claims:
        if not isinstance(claim, Mapping) or claim.get("status") != SUPPORTED:
            continue
        raw_path = claim.get("path")
        if not (
            isinstance(raw_path, list)
            and raw_path
            and all(isinstance(part, str) and part for part in raw_path)
        ):
            continue
        path = tuple(raw_path)
        if path in conflicted:
            continue
        candidate = deepcopy(dict(claim))
        if "normalized_value" not in candidate:
            supported.pop(path, None)
            conflicted.add(path)
            continue
        if (
            path in supported
            and supported[path]["normalized_value"] != candidate["normalized_value"]
        ):
            supported.pop(path, None)
            conflicted.add(path)
            continue
        supported[path] = candidate
    return supported


def _decimal_input(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, float):
            return Decimal(str(value))
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("non-finite Decimal is not supported")
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _unknown(code: str, **details: Any) -> dict[str, Any]:
    reason = {"code": code}
    for key in sorted(details):
        reason[key] = deepcopy(details[key])
    return {
        "version": "0.1",
        "status": UNKNOWN_RESULT,
        "result": None,
        "reasons": [reason],
    }
