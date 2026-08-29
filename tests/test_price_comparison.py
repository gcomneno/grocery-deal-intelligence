import copy

import pytest

from grocery_deal_intelligence.price_comparison import (
    BASIS_INCOMPATIBLE,
    EQUAL,
    LEFT_CHEAPER,
    NORMALIZATION_INVALID,
    NORMALIZATION_NOT_SUPPORTED,
    RATIO_INVALID,
    RIGHT_CHEAPER,
    compare_normalized_prices,
)


def economic_result(numerator, denominator, *, unit="kg", status="supported"):
    dimension = "mass" if unit == "kg" else "volume"
    if status != "supported":
        return {
            "version": "0.1",
            "status": "unknown",
            "result": None,
            "reasons": [{"code": "fixture_unknown"}],
        }
    return {
        "version": "0.1",
        "status": "supported",
        "result": {
            "basis": {
                "quantity": "1",
                "unit": unit,
                "dimension": dimension,
            },
            "comparable_price": {
                "currency": "EUR",
                "per_unit": unit,
                "exact_ratio": {
                    "numerator": str(numerator),
                    "denominator": str(denominator),
                },
            },
        },
        "reasons": [],
    }


def test_right_is_cheaper_on_common_eur_per_kg_basis():
    left = economic_result(249, 10)
    right = economic_result(22, 1)

    result = compare_normalized_prices(left, right)

    assert result["status"] == "supported"
    assert result["result"]["outcome"] == RIGHT_CHEAPER
    assert result["result"]["basis"] == {"currency": "EUR", "per_unit": "kg"}
    assert result["result"]["left"]["exact_ratio"] == {
        "numerator": "249",
        "denominator": "10",
    }
    assert result["result"]["right"]["exact_ratio"] == {
        "numerator": "22",
        "denominator": "1",
    }


def test_non_terminating_ratios_are_ordered_exactly():
    left = economic_result(10, 3)
    right = economic_result(13, 4)

    result = compare_normalized_prices(left, right)

    assert result["result"]["outcome"] == RIGHT_CHEAPER


def test_left_is_cheaper():
    result = compare_normalized_prices(
        economic_result(109, 100),
        economic_result(3, 2),
    )

    assert result["result"]["outcome"] == LEFT_CHEAPER


def test_equivalent_unreduced_ratios_are_equal_and_canonicalized():
    result = compare_normalized_prices(
        economic_result(498, 20),
        economic_result(249, 10),
    )

    assert result["result"]["outcome"] == EQUAL
    assert result["result"]["left"]["exact_ratio"] == {
        "numerator": "249",
        "denominator": "10",
    }
    assert result["result"]["right"]["exact_ratio"] == {
        "numerator": "249",
        "denominator": "10",
    }


def test_kg_and_litre_bases_fail_closed():
    result = compare_normalized_prices(
        economic_result(22, 1, unit="kg"),
        economic_result(109, 100, unit="l"),
    )

    assert result["status"] == "unknown"
    assert result["result"] is None
    assert result["reasons"] == [
        {
            "code": BASIS_INCOMPATIBLE,
            "left_basis": {"currency": "EUR", "per_unit": "kg"},
            "right_basis": {"currency": "EUR", "per_unit": "l"},
        }
    ]


def test_upstream_unknown_fails_closed():
    result = compare_normalized_prices(
        economic_result(1, 1, status="unknown"),
        economic_result(1, 1),
    )

    assert result["status"] == "unknown"
    assert result["reasons"][0]["code"] == NORMALIZATION_NOT_SUPPORTED
    assert result["reasons"][0]["left_error"] == NORMALIZATION_NOT_SUPPORTED


@pytest.mark.parametrize("numerator,denominator", [("1", "0"), ("1", "-2"), ("-1", "2"), ("1.0", "2")])
def test_malformed_or_invalid_ratio_fails_closed(numerator, denominator):
    left = economic_result(1, 1)
    left["result"]["comparable_price"]["exact_ratio"] = {
        "numerator": numerator,
        "denominator": denominator,
    }

    result = compare_normalized_prices(left, economic_result(1, 1))

    assert result["status"] == "unknown"
    assert result["reasons"][0]["code"] == RATIO_INVALID


def test_contradictory_basis_structure_fails_closed():
    left = economic_result(1, 1)
    left["result"]["basis"]["dimension"] = "volume"

    result = compare_normalized_prices(left, economic_result(1, 1))

    assert result["status"] == "unknown"
    assert result["reasons"][0]["code"] == NORMALIZATION_INVALID


def test_supported_result_with_reasons_is_rejected():
    left = economic_result(1, 1)
    left["reasons"] = [{"code": "contradiction"}]

    result = compare_normalized_prices(left, economic_result(1, 1))

    assert result["status"] == "unknown"
    assert result["reasons"][0]["code"] == NORMALIZATION_INVALID


def test_inputs_are_immutable_and_output_is_deterministic():
    left = economic_result(249, 10)
    right = economic_result(22, 1)
    left_before = copy.deepcopy(left)
    right_before = copy.deepcopy(right)

    first = compare_normalized_prices(left, right)
    second = compare_normalized_prices(left, right)

    assert left == left_before
    assert right == right_before
    assert first == second


def test_non_mapping_inputs_are_rejected():
    with pytest.raises(TypeError, match="left must be a mapping"):
        compare_normalized_prices([], economic_result(1, 1))
    with pytest.raises(TypeError, match="right must be a mapping"):
        compare_normalized_prices(economic_result(1, 1), [])
