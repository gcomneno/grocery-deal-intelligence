from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from .validation import _load_schema

_CATEGORY_ORDER = {
    "missing_required_field": 0,
    "wrong_canonical_shape": 1,
    "wrong_field_type": 2,
    "unexpected_field": 3,
    "invalid_enum_or_value": 4,
    "schema_constraint_violation": 5,
}


def _path_sort_key(path: list[object]) -> tuple[tuple[str, str], ...]:
    return tuple((type(segment).__name__, str(segment)) for segment in path)


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _expected_types(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(sorted(str(item) for item in value))
    return (str(value),)


def _diagnostic(
    *,
    category: str,
    path: list[object],
    validator: str,
    message: str,
) -> dict[str, Any]:
    return {
        "category": category,
        "path": path,
        "validator": validator,
        "message": message,
    }


def _required_diagnostics(error: ValidationError) -> list[dict[str, Any]]:
    if not isinstance(error.instance, Mapping):
        return []

    required = error.validator_value
    if not isinstance(required, list):
        return []

    missing = sorted(str(field) for field in required if field not in error.instance)
    return [
        _diagnostic(
            category="missing_required_field",
            path=[*list(error.absolute_path), field],
            validator="required",
            message=f"required field '{field}' is missing",
        )
        for field in missing
    ]


def _unexpected_field_diagnostics(error: ValidationError) -> list[dict[str, Any]]:
    if not isinstance(error.instance, Mapping):
        return []

    properties = error.schema.get("properties", {})
    allowed = set(properties) if isinstance(properties, Mapping) else set()
    unexpected = sorted(str(field) for field in error.instance if field not in allowed)
    return [
        _diagnostic(
            category="unexpected_field",
            path=[*list(error.absolute_path), field],
            validator="additionalProperties",
            message=f"field '{field}' is not allowed by the canonical schema",
        )
        for field in unexpected
    ]


def _type_diagnostic(error: ValidationError) -> dict[str, Any]:
    expected = _expected_types(error.validator_value)
    category = (
        "wrong_canonical_shape"
        if len(expected) == 1 and expected[0] in {"object", "array"}
        else "wrong_field_type"
    )
    expected_text = " or ".join(expected)
    return _diagnostic(
        category=category,
        path=list(error.absolute_path),
        validator="type",
        message=f"expected {expected_text}; got {_json_type(error.instance)}",
    )


def _constraint_diagnostic(error: ValidationError) -> dict[str, Any]:
    validator = str(error.validator)
    messages = {
        "enum": "value is not one of the allowed values",
        "const": "value does not match the required constant",
        "pattern": "value does not match the required pattern",
        "minimum": f"value is below minimum {error.validator_value}",
        "maximum": f"value is above maximum {error.validator_value}",
        "minLength": f"value is shorter than minimum length {error.validator_value}",
        "maxLength": f"value is longer than maximum length {error.validator_value}",
        "uniqueItems": "array items are not unique",
    }
    if validator in messages:
        category = "invalid_enum_or_value"
        message = messages[validator]
    else:
        category = "schema_constraint_violation"
        message = f"schema constraint '{validator}' failed"

    return _diagnostic(
        category=category,
        path=list(error.absolute_path),
        validator=validator,
        message=message,
    )


def diagnose_candidate_rejection(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic schema diagnostics without repairing or authorizing data."""
    if not isinstance(candidate, Mapping):
        raise TypeError("candidate must be a mapping")

    validator = Draft202012Validator(_load_schema())
    diagnostics: list[dict[str, Any]] = []

    for error in validator.iter_errors(candidate):
        if error.validator == "required":
            diagnostics.extend(_required_diagnostics(error))
        elif error.validator == "additionalProperties":
            diagnostics.extend(_unexpected_field_diagnostics(error))
        elif error.validator == "type":
            diagnostics.append(_type_diagnostic(error))
        else:
            diagnostics.append(_constraint_diagnostic(error))

    unique = {
        (
            diagnostic["category"],
            tuple(diagnostic["path"]),
            diagnostic["validator"],
            diagnostic["message"],
        ): diagnostic
        for diagnostic in diagnostics
    }

    return sorted(
        unique.values(),
        key=lambda diagnostic: (
            _path_sort_key(diagnostic["path"]),
            _CATEGORY_ORDER[diagnostic["category"]],
            diagnostic["validator"],
            diagnostic["message"],
        ),
    )
