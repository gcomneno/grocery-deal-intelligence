from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from fractions import Fraction
from typing import Any


SUPPORTED_RESULT = "supported"
UNKNOWN_RESULT = "unknown"
LEFT_CHEAPER = "left_cheaper"
RIGHT_CHEAPER = "right_cheaper"
EQUAL = "equal"

NORMALIZATION_NOT_SUPPORTED = "economic_normalization_not_supported"
NORMALIZATION_INVALID = "economic_normalization_invalid"
BASIS_INCOMPATIBLE = "economic_basis_incompatible"
RATIO_INVALID = "exact_ratio_invalid"

_SUPPORTED_BASES = {("EUR", "kg"), ("EUR", "l")}
_RULES = {
    "kg": {
        "dimension": "mass",
        "quantity_unit": "g",
        "attribute_path": ["weight_g"],
        "rule_id": "builtin:eur-per-kg:v0.1",
        "formula": "price_eur * 1000 / weight_g",
    },
    "l": {
        "dimension": "volume",
        "quantity_unit": "ml",
        "attribute_path": ["volume_ml"],
        "rule_id": "builtin:eur-per-l:v0.1",
        "formula": "price_eur * 1000 / volume_ml",
    },
}


def compare_normalized_prices(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare two already-supported economic-normalization results exactly.

    This function grants no semantic-comparability authority and performs no
    economic normalization. It consumes only structurally valid supported
    comparable-price bases and orders their exact rational values without
    display rounding.
    """
    if not isinstance(left, Mapping):
        raise TypeError("left must be a mapping")
    if not isinstance(right, Mapping):
        raise TypeError("right must be a mapping")

    left_copy = deepcopy(dict(left))
    right_copy = deepcopy(dict(right))

    left_value, left_error = _extract_supported_price(left_copy)
    right_value, right_error = _extract_supported_price(right_copy)

    if left_error is not None or right_error is not None:
        return _unknown(
            _combined_error(left_error, right_error),
            left_error=left_error,
            right_error=right_error,
        )

    if left_value is None or right_value is None:
        return _unknown(NORMALIZATION_INVALID)

    left_currency, left_unit, left_ratio = left_value
    right_currency, right_unit, right_ratio = right_value

    if (left_currency, left_unit) != (right_currency, right_unit):
        return _unknown(
            BASIS_INCOMPATIBLE,
            left_basis={"currency": left_currency, "per_unit": left_unit},
            right_basis={"currency": right_currency, "per_unit": right_unit},
        )

    if left_ratio < right_ratio:
        outcome = LEFT_CHEAPER
    elif right_ratio < left_ratio:
        outcome = RIGHT_CHEAPER
    else:
        outcome = EQUAL

    return {
        "version": "0.1",
        "status": SUPPORTED_RESULT,
        "result": {
            "outcome": outcome,
            "basis": {
                "currency": left_currency,
                "per_unit": left_unit,
            },
            "left": {"exact_ratio": _ratio_dict(left_ratio)},
            "right": {"exact_ratio": _ratio_dict(right_ratio)},
            "comparison": {
                "rule_id": "builtin:exact-rational-price-order:v0.1",
                "method": "exact_rational_ordering",
            },
        },
        "reasons": [],
    }


def _extract_supported_price(
    normalization: Mapping[str, Any],
) -> tuple[tuple[str, str, Fraction] | None, str | None]:
    if normalization.get("status") != SUPPORTED_RESULT:
        return None, NORMALIZATION_NOT_SUPPORTED
    if normalization.get("version") != "0.1" or normalization.get("reasons") != []:
        return None, NORMALIZATION_INVALID

    result = normalization.get("result")
    if not isinstance(result, Mapping):
        return None, NORMALIZATION_INVALID

    current_price = result.get("current_price")
    quantity = result.get("quantity")
    basis = result.get("basis")
    comparable_price = result.get("comparable_price")
    derivation = result.get("derivation")
    if not all(
        isinstance(value, Mapping)
        for value in (current_price, quantity, basis, comparable_price, derivation)
    ):
        return None, NORMALIZATION_INVALID

    if (
        current_price.get("currency") != "EUR"
        or current_price.get("source_path") != ["price"]
        or not isinstance(current_price.get("value"), str)
    ):
        return None, NORMALIZATION_INVALID

    currency = comparable_price.get("currency")
    per_unit = comparable_price.get("per_unit")
    if (currency, per_unit) not in _SUPPORTED_BASES:
        return None, NORMALIZATION_INVALID

    rule = _RULES[per_unit]
    if (
        basis.get("quantity") != "1"
        or basis.get("unit") != per_unit
        or basis.get("dimension") != rule["dimension"]
    ):
        return None, NORMALIZATION_INVALID

    if (
        quantity.get("unit") != rule["quantity_unit"]
        or quantity.get("dimension") != rule["dimension"]
        or quantity.get("attribute_path") != rule["attribute_path"]
        or not isinstance(quantity.get("value"), str)
        or not isinstance(quantity.get("claim"), Mapping)
    ):
        return None, NORMALIZATION_INVALID

    if (
        derivation.get("rule_id") != rule["rule_id"]
        or derivation.get("formula") != rule["formula"]
    ):
        return None, NORMALIZATION_INVALID

    ratio = _parse_ratio(comparable_price.get("exact_ratio"))
    if ratio is None:
        return None, RATIO_INVALID

    return (currency, per_unit, ratio), None


def _combined_error(left_error: str | None, right_error: str | None) -> str:
    errors = {error for error in (left_error, right_error) if error is not None}
    if NORMALIZATION_NOT_SUPPORTED in errors:
        return NORMALIZATION_NOT_SUPPORTED
    if RATIO_INVALID in errors:
        return RATIO_INVALID
    return NORMALIZATION_INVALID


def _parse_ratio(candidate: Any) -> Fraction | None:
    if not isinstance(candidate, Mapping):
        return None

    numerator = _strict_int(candidate.get("numerator"))
    denominator = _strict_int(candidate.get("denominator"))
    if numerator is None or denominator is None:
        return None
    if numerator < 0 or denominator <= 0:
        return None

    return Fraction(numerator, denominator)


def _strict_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if not value or value.strip() != value:
            return None
        signless = value[1:] if value.startswith("-") else value
        if not signless or not signless.isdigit():
            return None
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _ratio_dict(value: Fraction) -> dict[str, str]:
    return {
        "numerator": str(value.numerator),
        "denominator": str(value.denominator),
    }


def _unknown(code: str, **details: Any) -> dict[str, Any]:
    reason = {"code": code}
    for key in sorted(details):
        value = details[key]
        if value is not None:
            reason[key] = deepcopy(value)
    return {
        "version": "0.1",
        "status": UNKNOWN_RESULT,
        "result": None,
        "reasons": [reason],
    }
