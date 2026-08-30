from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any

from .source_evidence import SUPPORTED, UNVERIFIABLE

UNKNOWN_FAMILY = "unknown_product_family"
UNSUPPORTED_FAMILY = "unsupported_product_family"
FAMILY_EVIDENCE_UNAVAILABLE = "product_family_evidence_unavailable"
FAMILY_EVIDENCE_MISMATCH = "product_family_evidence_mismatch"
QUANTITY_UNAVAILABLE = "quantity_evidence_unavailable"
QUANTITY_AMBIGUOUS = "quantity_evidence_ambiguous"
QUANTITY_UNSUPPORTED = "quantity_unit_unsupported"

_FAMILY_POLICY_ID = "builtin:product-family-lexical-evidence:v0.2"
_FAMILY_POLICIES: dict[str, dict[str, object]] = {
    "dark_chocolate": {
        "required": ("fondente",),
        "forbidden": ("bianco",),
        "conflicting_phrases": (
            ("waffeletten",),
            ("alfajor",),
            ("biscotti",),
            ("cornetti",),
            ("frollini",),
            ("gelati",),
            ("granola",),
            ("gocce", "di", "cioccolato", "fondente"),
            ("cereali", "integrali", "con", "fiocchi"),
            ("fiocchi", "d", "avena"),
            ("mini", "choco", "mais"),
            ("quadrotti", "di", "riso"),
        ),
    },
    "milk_chocolate": {
        "required": ("cioccolato", "latte"),
        "forbidden": ("fondente", "bianco"),
        "conflicting_phrases": (),
    },
    "passata": {
        "required": ("passata",),
        "forbidden": (),
        "conflicting_phrases": (),
    },
    "whole_milk": {
        "required": ("latte", "intero"),
        "forbidden": (),
        "conflicting_phrases": (),
    },
}

_ALLOWED_EVIDENCE_PATHS = (("packaging_text",), ("product_name",))
_UNIT_MAP = {
    "g": ("mass", Decimal(1), "g"),
    "kg": ("mass", Decimal(1000), "g"),
    "ml": ("volume", Decimal(1), "ml"),
    "l": ("volume", Decimal(1000), "ml"),
}
_NUMBER = r"(?P<value>\d+(?:[\.,]\d+)?)"
_UNIT = r"(?P<unit>kg|g|ml|l)"
_COMPOSITE_RE = re.compile(
    rf"(?<!\w)(?P<count>\d+)\s*[x×]\s*{_NUMBER}\s*{_UNIT}(?!\w)",
    re.IGNORECASE,
)
_WORD_COMPOSITE_RE = re.compile(
    rf"(?<!\w)(?P<count>\d+)\s*(?:pz\.?|pezzi)\s+da\s+"
    rf"{_NUMBER}\s*{_UNIT}(?!\w)",
    re.IGNORECASE,
)
_SIMPLE_RE = re.compile(rf"(?<!\w){_NUMBER}\s*{_UNIT}(?!\w)", re.IGNORECASE)
_UNSUPPORTED_UNIT_RE = re.compile(
    r"(?<!\w)\d+(?:[\.,]\d+)?\s*(?:mg|cl|dl)(?!\w)", re.IGNORECASE
)
_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def normalize_product_attributes(
    offer: Mapping[str, Any],
    *,
    product_family_candidate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive comparison-ready attributes from one already-admitted offer.

    Quantity is parsed deterministically from observed canonical text. Product
    family remains a proposal until a narrow, versioned lexical evidence policy
    supports it. Missing or ambiguous facts are omitted and reported fail-closed.
    """
    if not isinstance(offer, Mapping):
        raise TypeError("offer must be a mapping")
    if product_family_candidate is not None and not isinstance(
        product_family_candidate, Mapping
    ):
        raise TypeError("product_family_candidate must be a mapping or None")

    source = deepcopy(dict(offer))
    values: dict[str, Any] = {}
    claims: list[dict[str, Any]] = []
    reasons: list[dict[str, Any]] = []

    family = _verify_product_family(source, product_family_candidate)
    if family["supported"]:
        values["product_family"] = family["value"]
        claims.append(family["claim"])
    elif family["reason"] is not None:
        reasons.append(family["reason"])

    quantity = _derive_quantity(source)
    if quantity["supported"]:
        quantity_values = quantity["values"]
        for key in sorted(quantity_values):
            values[key] = deepcopy(quantity_values[key])
        claims.extend(deepcopy(quantity["claims"]))
    elif quantity["reason"] is not None:
        reasons.append(quantity["reason"])

    claims.sort(key=lambda item: tuple(item["path"]))
    reasons.sort(key=lambda item: (item["code"], tuple(item.get("path", []))))

    return {
        "version": "0.1",
        "values": values,
        "claims": claims,
        "reasons": reasons,
    }


def comparison_verification_from_attributes(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    paths: Sequence[Sequence[str]] = (("product_family",), ("weight_g",)),
) -> list[dict[str, Any]]:
    """Project normalized attribute values into comparison-policy facts.

    This function grants no new authority. A side is marked supported only when
    that exact normalized path and value already have a supported claim in its
    own result.
    """
    left_copy = _validated_attribute_result(left)
    right_copy = _validated_attribute_result(right)
    left_claims = _supported_claim_values(left_copy)
    right_claims = _supported_claim_values(right_copy)

    results: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for raw_path in paths:
        path = tuple(str(part) for part in raw_path)
        if not path or any(not part for part in path):
            raise ValueError("comparison attribute paths must be non-empty strings")
        if path in seen:
            raise ValueError(f"duplicate comparison attribute path: {list(path)!r}")
        seen.add(path)

        left_value = _get_path(left_copy["values"], path)
        right_value = _get_path(right_copy["values"], path)
        results.append(
            {
                "path": list(path),
                "left": _comparison_side(path, left_value, left_claims),
                "right": _comparison_side(path, right_value, right_claims),
            }
        )

    return results


def _verify_product_family(
    offer: Mapping[str, Any],
    candidate: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if candidate is None:
        return {"supported": False, "reason": None}

    value = candidate.get("value")
    raw_path = candidate.get("evidence_path")
    if not isinstance(value, str) or not value:
        raise ValueError("product family candidate value must be a non-empty string")
    if (
        not isinstance(raw_path, list)
        or not raw_path
        or not all(isinstance(part, str) and part for part in raw_path)
    ):
        raise ValueError("product family candidate evidence_path is invalid")

    path = tuple(raw_path)
    if path not in _ALLOWED_EVIDENCE_PATHS:
        return {
            "supported": False,
            "reason": {
                "code": FAMILY_EVIDENCE_UNAVAILABLE,
                "path": list(path),
                "product_family": value,
            },
        }

    observed = _get_path(offer, path)
    if not isinstance(observed, str) or not observed.strip():
        return {
            "supported": False,
            "reason": {
                "code": FAMILY_EVIDENCE_UNAVAILABLE,
                "path": list(path),
                "product_family": value,
            },
        }

    policy = _FAMILY_POLICIES.get(value)
    if policy is None:
        return {
            "supported": False,
            "reason": {"code": UNSUPPORTED_FAMILY, "product_family": value},
        }

    ordered_tokens = tuple(_TOKEN_RE.findall(observed.casefold()))
    tokens = set(ordered_tokens)
    required = set(policy["required"])
    forbidden = set(policy["forbidden"])
    conflicting_phrases = tuple(policy["conflicting_phrases"])

    has_conflicting_form = any(
        _contains_token_phrase(ordered_tokens, phrase) for phrase in conflicting_phrases
    )

    if (
        not required.issubset(tokens)
        or forbidden.intersection(tokens)
        or has_conflicting_form
    ):
        return {
            "supported": False,
            "reason": {
                "code": FAMILY_EVIDENCE_MISMATCH,
                "path": list(path),
                "product_family": value,
            },
        }

    return {
        "supported": True,
        "value": value,
        "claim": {
            "path": ["product_family"],
            "status": SUPPORTED,
            "evidence_path": list(path),
            "raw_value": observed,
            "normalized_value": value,
            "normalization": "curated_lexical_family_policy",
            "policy_id": _FAMILY_POLICY_ID,
        },
        "reason": None,
    }


def _contains_token_phrase(
    tokens: tuple[str, ...],
    phrase: tuple[str, ...],
) -> bool:
    """Return whether one explicit normalized token phrase occurs contiguously."""
    if not phrase or len(phrase) > len(tokens):
        return False

    width = len(phrase)
    return any(
        tokens[index : index + width] == phrase
        for index in range(len(tokens) - width + 1)
    )


def _derive_quantity(offer: Mapping[str, Any]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    parse_reasons: list[str] = []

    for path in _ALLOWED_EVIDENCE_PATHS:
        raw = _get_path(offer, path)
        if not isinstance(raw, str) or not raw.strip():
            continue

        parsed, parse_reason = _parse_quantity_text(raw)
        if parse_reason is not None:
            parse_reasons.append(parse_reason)

        if parsed is not None:
            parsed["evidence_path"] = list(path)
            parsed["raw_value"] = raw
            observations.append(parsed)

    if QUANTITY_UNSUPPORTED in parse_reasons:
        return {
            "supported": False,
            "reason": {"code": QUANTITY_UNSUPPORTED},
        }

    if QUANTITY_AMBIGUOUS in parse_reasons:
        return {
            "supported": False,
            "reason": {"code": QUANTITY_AMBIGUOUS},
        }

    if not observations:
        return {
            "supported": False,
            "reason": {"code": QUANTITY_UNAVAILABLE},
        }

    signatures = {_quantity_signature(item) for item in observations}
    if len(signatures) != 1:
        return {
            "supported": False,
            "reason": {
                "code": QUANTITY_AMBIGUOUS,
                "observations": [
                    {
                        "evidence_path": item["evidence_path"],
                        "raw_value": item["raw_value"],
                    }
                    for item in observations
                ],
            },
        }

    selected = observations[0]
    values = deepcopy(selected["values"])
    claim_normalizations = selected.get("claim_normalizations", {})
    claims: list[dict[str, Any]] = []

    for path, normalized_value in _quantity_claim_values(values):
        key = path[0]
        claims.append(
            {
                "path": list(path),
                "status": SUPPORTED,
                "evidence_path": deepcopy(selected["evidence_path"]),
                "raw_value": selected["raw_value"],
                "normalized_value": deepcopy(normalized_value),
                "normalization": claim_normalizations.get(
                    key,
                    selected["normalization"],
                ),
            }
        )

    return {
        "supported": True,
        "values": values,
        "claims": claims,
        "reason": None,
    }


def _parse_quantity_text(
    text: str,
) -> tuple[dict[str, Any] | None, str | None]:
    if _UNSUPPORTED_UNIT_RE.search(text):
        return None, QUANTITY_UNSUPPORTED

    composite_matches = sorted(
        [
            *_COMPOSITE_RE.finditer(text),
            *_WORD_COMPOSITE_RE.finditer(text),
        ],
        key=lambda match: match.span(),
    )
    simple_matches = list(_SIMPLE_RE.finditer(text))

    if len(composite_matches) > 1:
        return None, QUANTITY_AMBIGUOUS

    if composite_matches:
        match = composite_matches[0]
        composite_span = match.span()

        count = int(match.group("count"))
        if count <= 0:
            return None, QUANTITY_AMBIGUOUS

        normalized = _normalize_measure(
            match.group("value"),
            match.group("unit"),
        )
        if normalized is None:
            return None, QUANTITY_UNSUPPORTED

        dimension, unit_value, base_unit = normalized
        total = unit_value * count

        extra_simple_matches = [
            simple
            for simple in simple_matches
            if not (
                composite_span[0] <= simple.start()
                and simple.end() <= composite_span[1]
            )
        ]

        for simple in extra_simple_matches:
            extra = _normalize_measure(
                simple.group("value"),
                simple.group("unit"),
            )
            if extra is None:
                return None, QUANTITY_UNSUPPORTED

            extra_dimension, extra_value, extra_unit = extra
            if (
                extra_dimension != dimension
                or extra_value != total
                or extra_unit != base_unit
            ):
                return None, QUANTITY_AMBIGUOUS

        values = {
            "pack_count": count,
            "unit_quantity": _measure_value(
                unit_value,
                base_unit,
                dimension,
            ),
            "total_quantity": _measure_value(
                total,
                base_unit,
                dimension,
            ),
            "quantity": _measure_value(
                total,
                base_unit,
                dimension,
            ),
        }

        if dimension == "mass":
            values["weight_g"] = _json_number(total)
            scalar_key = "weight_g"
        else:
            values["volume_ml"] = _json_number(total)
            scalar_key = "volume_ml"

        derived_normalization = "exact_composite_arithmetic"
        if extra_simple_matches:
            derived_normalization = "exact_composite_arithmetic_corroborated"

        claim_normalizations = {
            "pack_count": "explicit_composite_relation",
            "unit_quantity": "explicit_composite_relation",
            "total_quantity": derived_normalization,
            "quantity": derived_normalization,
            scalar_key: derived_normalization,
        }

        return {
            "values": values,
            "normalization": "explicit_composite_quantity",
            "claim_normalizations": claim_normalizations,
        }, None

    if not simple_matches:
        return None, None

    normalized_matches: list[tuple[str, Decimal, str]] = []
    for match in simple_matches:
        normalized = _normalize_measure(
            match.group("value"),
            match.group("unit"),
        )
        if normalized is None:
            return None, QUANTITY_UNSUPPORTED
        normalized_matches.append(normalized)

    signatures = {
        (dimension, value, unit) for dimension, value, unit in normalized_matches
    }
    if len(signatures) != 1:
        return None, QUANTITY_AMBIGUOUS

    dimension, value, unit = normalized_matches[0]
    values = {
        "quantity": _measure_value(
            value,
            unit,
            dimension,
        )
    }

    if dimension == "mass":
        values["weight_g"] = _json_number(value)
    else:
        values["volume_ml"] = _json_number(value)

    return {
        "values": values,
        "normalization": "deterministic_unit_conversion",
    }, None


def _normalize_measure(raw_value: str, raw_unit: str):
    unit = raw_unit.casefold()
    unit_info = _UNIT_MAP.get(unit)
    if unit_info is None:
        return None
    try:
        value = Decimal(raw_value.replace(",", "."))
    except InvalidOperation:
        return None
    if value <= 0:
        return None
    dimension, factor, base_unit = unit_info
    return dimension, value * factor, base_unit


def _measure_value(value: Decimal, unit: str, dimension: str) -> dict[str, Any]:
    return {"value": _json_number(value), "unit": unit, "dimension": dimension}


def _json_number(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    if value == integral:
        return int(integral)
    return float(value)


def _quantity_signature(item: Mapping[str, Any]) -> tuple[Any, ...]:
    values = item["values"]
    quantity = values["quantity"]
    return (
        quantity["dimension"],
        quantity["value"],
        quantity["unit"],
        values.get("pack_count"),
        _nested_measure_signature(values.get("unit_quantity")),
    )


def _nested_measure_signature(value: Any):
    if not isinstance(value, Mapping):
        return None
    return value.get("value"), value.get("unit"), value.get("dimension")


def _quantity_claim_values(values: Mapping[str, Any]):
    for key in (
        "quantity",
        "weight_g",
        "volume_ml",
        "pack_count",
        "unit_quantity",
        "total_quantity",
    ):
        if key in values:
            yield (key,), values[key]


def _validated_attribute_result(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("attribute result must be a mapping")
    result = deepcopy(dict(value))
    if not isinstance(result.get("values"), Mapping):
        raise ValueError("attribute result values must be a mapping")
    if not isinstance(result.get("claims"), list):
        raise ValueError("attribute result claims must be a list")
    return result


def _supported_claim_values(result: Mapping[str, Any]) -> dict[tuple[str, ...], Any]:
    supported: dict[tuple[str, ...], Any] = {}
    conflicted: set[tuple[str, ...]] = set()

    for claim in result["claims"]:
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
        normalized_value = claim.get("normalized_value", _MISSING)
        if normalized_value is _MISSING:
            conflicted.add(path)
            supported.pop(path, None)
            continue
        if path in conflicted:
            continue
        if path in supported and supported[path] != normalized_value:
            conflicted.add(path)
            supported.pop(path, None)
            continue
        supported[path] = deepcopy(normalized_value)

    return supported


def _comparison_side(
    path: tuple[str, ...],
    value: Any,
    supported_claims: Mapping[tuple[str, ...], Any],
) -> dict[str, Any]:
    if (
        value is _MISSING
        or path not in supported_claims
        or supported_claims[path] != value
    ):
        return {"status": UNVERIFIABLE}
    return {
        "status": SUPPORTED,
        "proposed_value": deepcopy(value),
        "evidence_value": deepcopy(value),
    }


class _Missing:
    pass


_MISSING = _Missing()


def _get_path(value: Mapping[str, Any], path: tuple[str, ...]):
    current: Any = value
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return deepcopy(current)
