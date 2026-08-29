from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .comparison import COMPARABLE, UNKNOWN
from .source_evidence import SUPPORTED


ROOT = Path(__file__).resolve().parent.parent
POLICY_SCHEMA_PATH = ROOT / "schema/comparison-policy-layer-v0.1.schema.json"
BUILTIN_DEFAULTS_PATH = ROOT / "policies/comparison-defaults-v0.1.json"

BUILTIN_GLOBAL = "builtin_global"
BUILTIN_CATEGORY = "builtin_category"
USER_CATEGORY = "user_category"
USER_FAMILY = "user_family"
USER_PRODUCT = "user_product"

NO_AUTHORITY_RULES = "no_authority_rules"
REQUIRED_FACT_UNAVAILABLE = "required_fact_unavailable"
REQUIRED_FACT_MISMATCH = "required_fact_mismatch"
EXCLUSION_FACT_UNAVAILABLE = "exclusion_fact_unavailable"
EXCLUDED_VALUE = "excluded_value"

_LAYER_ORDER = (
    BUILTIN_GLOBAL,
    BUILTIN_CATEGORY,
    USER_CATEGORY,
    USER_FAMILY,
    USER_PRODUCT,
)


def _load_policy_schema() -> dict[str, Any]:
    return json.loads(POLICY_SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_builtin_defaults() -> dict[str, Any]:
    return json.loads(BUILTIN_DEFAULTS_PATH.read_text(encoding="utf-8"))


def validate_policy_layer(layer: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one policy layer without granting comparison authority."""
    if not isinstance(layer, Mapping):
        raise TypeError("layer must be a mapping")

    layer_copy = deepcopy(dict(layer))
    validator = Draft202012Validator(_load_policy_schema())
    errors = sorted(
        validator.iter_errors(layer_copy),
        key=lambda error: (
            list(error.absolute_path),
            error.validator,
            error.message,
        ),
    )

    return {
        "valid": not errors,
        "errors": [
            {
                "path": list(error.absolute_path),
                "message": error.message,
            }
            for error in errors
        ],
    }


def resolve_comparison_policy(
    *,
    category: str | None = None,
    user_category: Mapping[str, Any] | None = None,
    user_family: Mapping[str, Any] | None = None,
    user_product: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve built-in defaults plus increasingly specific user overrides.

    Rule fields are merged individually. A more specific layer therefore
    overrides only fields it explicitly supplies. Provenance is retained for
    every effective field so inherited and overridden semantics remain visible.
    """
    if category is not None and (not isinstance(category, str) or not category):
        raise ValueError("category must be a non-empty string or None")

    defaults = _load_builtin_defaults()
    if not isinstance(defaults, Mapping):
        raise ValueError("built-in comparison defaults must be a mapping")

    layers: list[Mapping[str, Any]] = []

    global_layer = defaults.get("global")
    if not isinstance(global_layer, Mapping):
        raise ValueError("built-in comparison defaults must define global layer")
    layers.append(global_layer)

    categories = defaults.get("categories", {})
    if not isinstance(categories, Mapping):
        raise ValueError("built-in comparison categories must be a mapping")

    if category is not None and category in categories:
        category_layer = categories[category]
        if not isinstance(category_layer, Mapping):
            raise ValueError(f"built-in category policy {category!r} must be a mapping")
        layers.append(category_layer)

    for expected_origin, layer in (
        (USER_CATEGORY, user_category),
        (USER_FAMILY, user_family),
        (USER_PRODUCT, user_product),
    ):
        if layer is None:
            continue
        if not isinstance(layer, Mapping):
            raise TypeError(f"{expected_origin} layer must be a mapping")
        layers.append(_validated_user_layer(layer, expected_origin=expected_origin))

    effective_rules: dict[str, dict[str, Any]] = {}
    field_provenance: dict[str, dict[str, dict[str, Any]]] = {}
    applied_layers: list[dict[str, str]] = []

    previous_rank = -1
    for layer in layers:
        validated = _validated_layer(layer)
        origin = validated["origin"]
        rank = _LAYER_ORDER.index(origin)
        if rank < previous_rank:
            raise ValueError("comparison policy layers are out of precedence order")
        previous_rank = rank

        source = {
            "policy_id": validated["id"],
            "policy_version": validated["version"],
            "origin": origin,
        }
        applied_layers.append(deepcopy(source))

        rules = validated["rules"]
        for rule_id in sorted(rules):
            patch = rules[rule_id]
            current = effective_rules.setdefault(rule_id, {})
            provenance = field_provenance.setdefault(rule_id, {})
            for field in sorted(patch):
                current[field] = deepcopy(patch[field])
                provenance[field] = deepcopy(source)

    resolved_rules: dict[str, dict[str, Any]] = {}
    for rule_id in sorted(effective_rules):
        rule = deepcopy(effective_rules[rule_id])
        if "enabled" not in rule:
            rule["enabled"] = True
            field_provenance[rule_id]["enabled"] = {
                "policy_id": "implicit-default",
                "policy_version": "0.1",
                "origin": "resolver_default",
            }
        _validate_effective_rule(rule_id, rule)
        rule["provenance"] = deepcopy(field_provenance[rule_id])
        resolved_rules[rule_id] = rule

    return {
        "version": str(defaults.get("version", "0.1")),
        "category": category,
        "applied_layers": applied_layers,
        "rules": resolved_rules,
    }


def evaluate_comparison_policy(
    verification: list[Mapping[str, Any]],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate comparability using only already-verified bilateral facts.

    `require` and `exclude` rules are authority-bearing policy constraints.
    `ignore` and `prefer` rules are observable policy metadata only and cannot
    make a comparison eligible.
    """
    if not isinstance(verification, list):
        raise TypeError("verification must be a list")
    if not isinstance(policy, Mapping):
        raise TypeError("policy must be a mapping")

    verification_by_path = _index_verification(verification)
    policy_copy = deepcopy(dict(policy))
    rules = policy_copy.get("rules")
    if not isinstance(rules, Mapping):
        raise ValueError("policy.rules must be a mapping")

    reasons: list[dict[str, Any]] = []
    evaluated_rules: list[dict[str, Any]] = []
    authority_rule_count = 0

    for rule_id in sorted(rules):
        raw_rule = rules[rule_id]
        if not isinstance(raw_rule, Mapping):
            raise ValueError(f"policy rule {rule_id!r} must be a mapping")
        rule = deepcopy(dict(raw_rule))

        if not rule.get("enabled", True):
            evaluated_rules.append({"rule_id": rule_id, "outcome": "disabled"})
            continue

        effect = rule.get("effect")
        path = _rule_path(rule_id, rule)

        if effect in {"ignore", "prefer"}:
            evaluated_rules.append(
                {
                    "rule_id": rule_id,
                    "effect": effect,
                    "path": list(path),
                    "outcome": "non_authoritative",
                }
            )
            continue

        if effect not in {"require", "exclude"}:
            raise ValueError(f"unsupported policy effect: {effect!r}")
        authority_rule_count += 1

        fact = verification_by_path.get(path)
        if fact is None or not _bilaterally_supported(fact):
            code = (
                REQUIRED_FACT_UNAVAILABLE
                if effect == "require"
                else EXCLUSION_FACT_UNAVAILABLE
            )
            reasons.append(
                {
                    "code": code,
                    "rule_id": rule_id,
                    "path": list(path),
                }
            )
            evaluated_rules.append(
                {
                    "rule_id": rule_id,
                    "effect": effect,
                    "path": list(path),
                    "outcome": "unavailable",
                }
            )
            continue

        left_value = deepcopy(fact["left"]["evidence_value"])
        right_value = deepcopy(fact["right"]["evidence_value"])

        if effect == "require":
            if left_value != right_value:
                reasons.append(
                    {
                        "code": REQUIRED_FACT_MISMATCH,
                        "rule_id": rule_id,
                        "path": list(path),
                        "left_value": left_value,
                        "right_value": right_value,
                    }
                )
                outcome = "mismatch"
            else:
                outcome = "satisfied"

            evaluated_rules.append(
                {
                    "rule_id": rule_id,
                    "effect": effect,
                    "path": list(path),
                    "outcome": outcome,
                }
            )
            continue

        values = rule["values"]
        excluded = left_value in values or right_value in values
        if excluded:
            reasons.append(
                {
                    "code": EXCLUDED_VALUE,
                    "rule_id": rule_id,
                    "path": list(path),
                    "left_value": left_value,
                    "right_value": right_value,
                }
            )
        evaluated_rules.append(
            {
                "rule_id": rule_id,
                "effect": effect,
                "path": list(path),
                "outcome": "excluded" if excluded else "satisfied",
            }
        )

    if authority_rule_count == 0:
        reasons.append({"code": NO_AUTHORITY_RULES})

    reasons.sort(key=lambda item: (item.get("rule_id", ""), item["code"]))
    eligible = not reasons

    return {
        "relationship": COMPARABLE if eligible else UNKNOWN,
        "eligible": eligible,
        "reasons": reasons,
        "evaluated_rules": evaluated_rules,
        "policy": policy_copy,
    }


def _validated_user_layer(
    layer: Mapping[str, Any],
    *,
    expected_origin: str,
) -> dict[str, Any]:
    validated = _validated_layer(layer)
    if validated["origin"] != expected_origin:
        raise ValueError(
            f"user policy layer origin must be {expected_origin!r}, "
            f"got {validated['origin']!r}"
        )
    return validated


def _validated_layer(layer: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_policy_layer(layer)
    if not validation["valid"]:
        raise ValueError(f"invalid comparison policy layer: {validation['errors']!r}")
    return deepcopy(dict(layer))


def _validate_effective_rule(rule_id: str, rule: Mapping[str, Any]) -> None:
    required_fields = {"effect", "path", "operator", "enabled"}
    missing = sorted(required_fields - set(rule))
    if missing:
        raise ValueError(
            f"effective comparison rule {rule_id!r} is missing fields: {missing!r}"
        )

    effect = rule["effect"]
    operator = rule["operator"]
    path = rule["path"]

    if (
        not isinstance(path, list)
        or not path
        or not all(isinstance(part, str) and part for part in path)
    ):
        raise ValueError(f"effective comparison rule {rule_id!r} has invalid path")

    expected_operator = {
        "require": "equal",
        "ignore": "observe",
        "prefer": "observe",
        "exclude": "value_in",
    }.get(effect)
    if expected_operator is None:
        raise ValueError(f"effective comparison rule {rule_id!r} has invalid effect")
    if operator != expected_operator:
        raise ValueError(
            f"effective comparison rule {rule_id!r} effect {effect!r} "
            f"requires operator {expected_operator!r}"
        )

    if effect == "exclude":
        values = rule.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError(
                f"effective comparison exclude rule {rule_id!r} requires values"
            )


def _index_verification(
    verification: list[Mapping[str, Any]],
) -> dict[tuple[str, ...], dict[str, Any]]:
    indexed: dict[tuple[str, ...], dict[str, Any]] = {}

    for index, item in enumerate(verification):
        if not isinstance(item, Mapping):
            raise TypeError("verification entries must be mappings")

        raw_path = item.get("path")
        if (
            not isinstance(raw_path, list)
            or not raw_path
            or not all(isinstance(part, str) and part for part in raw_path)
        ):
            raise ValueError(
                f"verification[{index}].path must be a non-empty list of strings"
            )

        path = tuple(raw_path)
        if path in indexed:
            raise ValueError(f"duplicate verification claim path: {list(path)!r}")
        indexed[path] = deepcopy(dict(item))

    return indexed


def _rule_path(rule_id: str, rule: Mapping[str, Any]) -> tuple[str, ...]:
    raw_path = rule.get("path")
    if (
        not isinstance(raw_path, list)
        or not raw_path
        or not all(isinstance(part, str) and part for part in raw_path)
    ):
        raise ValueError(f"policy rule {rule_id!r} has invalid path")
    return tuple(raw_path)


def _side_is_supported(side: Mapping[str, Any]) -> bool:
    return (
        side.get("status") == SUPPORTED
        and "proposed_value" in side
        and "evidence_value" in side
        and side["proposed_value"] == side["evidence_value"]
    )


def _bilaterally_supported(item: Mapping[str, Any]) -> bool:
    left = item.get("left")
    right = item.get("right")
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return False
    return _side_is_supported(left) and _side_is_supported(right)
