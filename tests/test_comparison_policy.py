import copy

import pytest

from grocery_deal_intelligence.comparison import COMPARABLE, UNKNOWN
from grocery_deal_intelligence.comparison_policy import (
    EXCLUDED_VALUE,
    NO_AUTHORITY_RULES,
    REQUIRED_FACT_MISMATCH,
    REQUIRED_FACT_UNAVAILABLE,
    USER_CATEGORY,
    USER_FAMILY,
    USER_PRODUCT,
    evaluate_comparison_policy,
    resolve_comparison_policy,
    validate_policy_layer,
)


def verification(path, left_value, right_value, *, left_status="supported", right_status="supported"):
    left = {
        "status": left_status,
        "proposed_value": left_value,
    }
    right = {
        "status": right_status,
        "proposed_value": right_value,
    }
    if left_status == "supported":
        left["evidence_value"] = left_value
    if right_status == "supported":
        right["evidence_value"] = right_value
    return {
        "path": list(path),
        "left": left,
        "right": right,
    }


def layer(*, layer_id, origin, rules):
    return {
        "id": layer_id,
        "version": "0.1",
        "origin": origin,
        "rules": rules,
    }


def test_policy_layer_schema_accepts_partial_override_rule():
    candidate = layer(
        layer_id="user:category:chocolate",
        origin=USER_CATEGORY,
        rules={"same_weight": {"enabled": False}},
    )

    assert validate_policy_layer(candidate) == {"valid": True, "errors": []}


def test_chocolate_builtin_is_pragmatic_and_inspectable():
    policy = resolve_comparison_policy(category="chocolate_bar")

    assert [item["origin"] for item in policy["applied_layers"]] == [
        "builtin_global",
        "builtin_category",
    ]
    assert policy["rules"]["same_product_family"]["effect"] == "require"
    assert policy["rules"]["same_weight"]["effect"] == "require"
    assert policy["rules"]["brand"]["effect"] == "ignore"
    assert policy["rules"]["cocoa_percentage"]["effect"] == "ignore"
    assert policy["rules"]["sugar_percentage"]["effect"] == "ignore"
    assert (
        policy["rules"]["same_weight"]["provenance"]["path"]["origin"]
        == "builtin_category"
    )


def test_specific_layers_override_only_supplied_rule_fields_with_provenance():
    category_override = layer(
        layer_id="user:category:chocolate",
        origin=USER_CATEGORY,
        rules={"same_weight": {"enabled": False}},
    )
    family_override = layer(
        layer_id="user:family:dark-chocolate",
        origin=USER_FAMILY,
        rules={"same_weight": {"enabled": True}},
    )
    product_override = layer(
        layer_id="user:product:holiday-bar",
        origin=USER_PRODUCT,
        rules={"same_weight": {"enabled": False}},
    )

    policy = resolve_comparison_policy(
        category="chocolate_bar",
        user_category=category_override,
        user_family=family_override,
        user_product=product_override,
    )

    rule = policy["rules"]["same_weight"]
    assert rule["effect"] == "require"
    assert rule["path"] == ["weight_g"]
    assert rule["enabled"] is False
    assert rule["provenance"]["effect"]["origin"] == "builtin_category"
    assert rule["provenance"]["enabled"]["origin"] == USER_PRODUCT


def test_dark_chocolate_same_family_same_weight_is_comparable_even_when_ignored_attributes_differ():
    policy = resolve_comparison_policy(category="chocolate_bar")
    facts = [
        verification(["product_family"], "dark_chocolate", "dark_chocolate"),
        verification(["weight_g"], 100, 100),
        verification(["brand"], "Novi", "Lindt"),
        verification(["cocoa_percentage"], 70, 85),
        verification(["sugar_percentage"], 28, 12),
    ]

    result = evaluate_comparison_policy(facts, policy)

    assert result["relationship"] == COMPARABLE
    assert result["eligible"] is True
    assert result["reasons"] == []


def test_missing_required_weight_fails_closed():
    policy = resolve_comparison_policy(category="chocolate_bar")
    facts = [
        verification(["product_family"], "dark_chocolate", "dark_chocolate"),
    ]

    result = evaluate_comparison_policy(facts, policy)

    assert result["relationship"] == UNKNOWN
    assert result["eligible"] is False
    assert result["reasons"] == [
        {
            "code": REQUIRED_FACT_UNAVAILABLE,
            "rule_id": "same_weight",
            "path": ["weight_g"],
        }
    ]


def test_different_required_weight_fails_closed():
    policy = resolve_comparison_policy(category="chocolate_bar")
    facts = [
        verification(["product_family"], "dark_chocolate", "dark_chocolate"),
        verification(["weight_g"], 100, 200),
    ]

    result = evaluate_comparison_policy(facts, policy)

    assert result["relationship"] == UNKNOWN
    assert result["eligible"] is False
    assert result["reasons"] == [
        {
            "code": REQUIRED_FACT_MISMATCH,
            "rule_id": "same_weight",
            "path": ["weight_g"],
            "left_value": 100,
            "right_value": 200,
        }
    ]


def test_prefer_rule_is_non_authoritative():
    prefer_only = layer(
        layer_id="user:category:prefer-brand",
        origin=USER_CATEGORY,
        rules={
            "brand": {
                "effect": "prefer",
                "path": ["brand"],
                "operator": "observe",
                "enabled": True,
            }
        },
    )
    policy = resolve_comparison_policy(user_category=prefer_only)

    result = evaluate_comparison_policy(
        [verification(["brand"], "Novi", "Lindt")],
        policy,
    )

    assert result["relationship"] == UNKNOWN
    assert result["eligible"] is False
    assert result["reasons"] == [{"code": NO_AUTHORITY_RULES}]


def test_empty_global_default_does_not_authorize_comparability():
    policy = resolve_comparison_policy(category="unknown_category")

    result = evaluate_comparison_policy([], policy)

    assert result["relationship"] == UNKNOWN
    assert result["eligible"] is False
    assert result["reasons"] == [{"code": NO_AUTHORITY_RULES}]


def test_user_override_can_disable_builtin_weight_requirement_without_editing_builtin():
    override = layer(
        layer_id="user:category:chocolate-weight-agnostic",
        origin=USER_CATEGORY,
        rules={"same_weight": {"enabled": False}},
    )
    policy = resolve_comparison_policy(
        category="chocolate_bar",
        user_category=override,
    )

    result = evaluate_comparison_policy(
        [verification(["product_family"], "dark_chocolate", "dark_chocolate")],
        policy,
    )

    assert result["relationship"] == COMPARABLE
    assert result["eligible"] is True
    assert policy["rules"]["same_weight"]["enabled"] is False
    assert policy["rules"]["same_weight"]["provenance"]["enabled"] == {
        "policy_id": "user:category:chocolate-weight-agnostic",
        "policy_version": "0.1",
        "origin": USER_CATEGORY,
    }


def test_exclude_rule_blocks_matching_verified_values():
    exclude = layer(
        layer_id="user:category:no-filled",
        origin=USER_CATEGORY,
        rules={
            "same_family": {
                "effect": "require",
                "path": ["product_family"],
                "operator": "equal",
                "enabled": True,
            },
            "filled": {
                "effect": "exclude",
                "path": ["filled"],
                "operator": "value_in",
                "values": [True],
                "enabled": True,
            },
        },
    )
    policy = resolve_comparison_policy(user_category=exclude)

    result = evaluate_comparison_policy(
        [
            verification(["product_family"], "dark_chocolate", "dark_chocolate"),
            verification(["filled"], False, True),
        ],
        policy,
    )

    assert result["relationship"] == UNKNOWN
    assert result["eligible"] is False
    assert result["reasons"][0]["code"] == EXCLUDED_VALUE


def test_inputs_are_not_mutated_and_resolution_is_deterministic():
    override = layer(
        layer_id="user:family:dark-chocolate",
        origin=USER_FAMILY,
        rules={"brand": {"effect": "prefer"}},
    )
    original_override = copy.deepcopy(override)

    first = resolve_comparison_policy(
        category="chocolate_bar",
        user_family=override,
    )
    second = resolve_comparison_policy(
        category="chocolate_bar",
        user_family=override,
    )

    assert override == original_override
    assert first == second
    assert first["rules"]["brand"]["effect"] == "prefer"
    assert first["rules"]["brand"]["operator"] == "observe"


def test_wrong_user_layer_origin_is_rejected():
    wrong = layer(
        layer_id="user:oops",
        origin=USER_PRODUCT,
        rules={},
    )

    with pytest.raises(ValueError, match="user_category"):
        resolve_comparison_policy(user_category=wrong)
