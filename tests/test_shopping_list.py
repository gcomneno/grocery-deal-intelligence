import copy

from grocery_deal_intelligence.shopping_list import (
    COMPARISON_CATEGORY_REQUIRED,
    ECONOMIC_BASIS_INCOMPATIBLE,
    ECONOMIC_NORMALIZATION_INVALID,
    ECONOMIC_NORMALIZATION_NOT_SUPPORTED,
    EXACT_RATIO_INVALID,
    LOWEST_PRICE,
    NO_ELIGIBLE_OFFERS,
    SELECTION_SELECTED,
    SELECTION_SINGLETON,
    SELECTION_UNSELECTED,
    SEMANTIC_COMPARISON_NOT_AUTHORIZED,
    SINGLETON_AVAILABLE,
    TIE_FOR_LOWEST_PRICE,
    UNKNOWN_SELECTION_POLICY,
    resolve_shopping_list,
)


AS_OF = "2026-08-29"


def offer(
    product_name,
    *,
    retailer="example",
    price=2.19,
    currency="EUR",
    valid_from="2026-08-27",
    valid_to="2026-09-06",
    stores=None,
):
    return {
        "retailer": retailer,
        "product_name": product_name,
        "price": price,
        "currency": currency,
        "packaging_text": None,
        "validity": {
            "from": valid_from,
            "to": valid_to,
        },
        "locality": {
            "scope": "store",
            "stores": list(stores or ["store-lucca"]),
        },
        "verification": {
            "locality_status": "verified",
            "evidence_status": "verified",
        },
        "provenance": {
            "source_type": "retailer_api",
            "source_url": (
                "https://example.invalid/source/"
                + retailer
                + "/campaign"
            ),
            "observed_at": "2026-08-29T07:00:00Z",
            "fixture_sha256": "abc123",
        },
    }


def item(
    item_id,
    product_family="dark_chocolate",
    *,
    policy=LOWEST_PRICE,
    category="chocolate_bar",
):
    result = {
        "id": item_id,
        "product_family": product_family,
        "selection_policy": policy,
    }
    if category is not None:
        result["comparison_category"] = category
    return result


def resolve(records, items):
    return resolve_shopping_list(
        records,
        items=items,
        as_of=AS_OF,
        locality_scope="store",
        stores=["store-lucca"],
    )


def selection(result, index=0):
    return result["items"][index]["selection"]


def test_original_caller_order_is_preserved():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="z"),
        offer("Latte Intero 1000 ml", retailer="a"),
    ]
    items = [
        item("milk", "whole_milk", category=None),
        item("chocolate", "dark_chocolate", category=None),
    ]

    result = resolve(records, items)

    assert [resolved["id"] for resolved in result["items"]] == [
        "milk",
        "chocolate",
    ]


def test_as_of_is_list_level_only():
    result = resolve(
        [offer("Vanini fondente 95% 90 g", retailer="a", price=2.19)],
        [item("chocolate")],
    )

    assert result["as_of"] == "2026-08-29"
    assert "as_of" not in result["items"][0]["availability"]


def test_blocking_reason_precedence_is_order_independent():
    import grocery_deal_intelligence.shopping_list as shopping_list

    reasons = [
        shopping_list.EXACT_RATIO_INVALID,
        shopping_list.SEMANTIC_COMPARISON_NOT_AUTHORIZED,
        shopping_list.ECONOMIC_BASIS_INCOMPATIBLE,
    ]

    assert shopping_list._blocking_reason(reasons) == (
        shopping_list.SEMANTIC_COMPARISON_NOT_AUTHORIZED
    )
    assert shopping_list._blocking_reason(list(reversed(reasons))) == (
        shopping_list.SEMANTIC_COMPARISON_NOT_AUTHORIZED
    )


def test_duplicate_family_with_different_ids_remains_distinct():
    records = [offer("Vanini fondente 91% 90 g")]
    items = [
        item("first", category=None),
        item("second", category=None),
    ]

    result = resolve(records, items)

    assert [resolved["id"] for resolved in result["items"]] == [
        "first",
        "second",
    ]
    assert result["singleton_item_count"] == 2


def test_zero_offers_is_unknown_and_unselected():
    result = resolve(
        [offer("Latte Intero 1000 ml")],
        [item("chocolate", category=None)],
    )

    resolved = result["items"][0]
    assert resolved["availability"]["status"] == "unknown"
    assert selection(result) == {
        "policy_id": LOWEST_PRICE,
        "status": SELECTION_UNSELECTED,
        "selected_offer": None,
        "sole_offer": None,
        "reason": {"code": NO_ELIGIBLE_OFFERS},
        "comparative_claim": None,
        "diagnostics": {"pairs": []},
    }


def test_singleton_uses_sole_offer_without_comparative_superiority():
    record = offer("Vanini fondente 91% 90 g", retailer="esselunga")

    result = resolve([record], [item("chocolate", category=None)])

    selected = selection(result)
    assert selected["status"] == SELECTION_SINGLETON
    assert selected["selected_offer"] is None
    assert selected["sole_offer"]["product_name"] == "Vanini fondente 91% 90 g"
    assert selected["reason"] == {"code": SINGLETON_AVAILABLE}
    assert selected["comparative_claim"] is None
    assert selected["diagnostics"] == {"pairs": []}
    assert "cheapest" not in selected
    assert "winner" not in selected
    assert "best" not in selected


def test_unknown_policy_is_explicit_unselected_result():
    result = resolve(
        [offer("Vanini fondente 91% 90 g")],
        [item("chocolate", policy="nearest_store", category=None)],
    )

    assert selection(result)["status"] == SELECTION_UNSELECTED
    assert selection(result)["reason"] == {
        "code": UNKNOWN_SELECTION_POLICY
    }


def test_multi_offer_lowest_price_requires_comparison_category():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="a"),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="b",
        ),
    ]

    result = resolve(records, [item("chocolate", category=None)])

    assert selection(result)["status"] == SELECTION_UNSELECTED
    assert selection(result)["reason"] == {
        "code": COMPARISON_CATEGORY_REQUIRED
    }
    assert selection(result)["diagnostics"] == {"pairs": []}


def test_two_comparable_offers_select_exact_normalized_lower_price():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="a", price=2.25),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="b",
            price=2.30,
        ),
    ]

    result = resolve(records, [item("chocolate")])

    selected = selection(result)
    assert selected["status"] == SELECTION_SELECTED
    assert selected["selected_offer"]["retailer"] == "b"
    assert selected["sole_offer"] is None
    assert selected["reason"] is None
    assert (
        selected["comparative_claim"]
        == "strict_lowest_supported_normalized_price"
    )
    assert selected["diagnostics"]["pairs"][0]["authorized_order"] == (
        "right_cheaper"
    )


def test_raw_package_price_does_not_override_normalized_comparable_price():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="small", price=1.90),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="large",
            price=2.00,
        ),
    ]

    result = resolve(records, [item("chocolate")])

    selected = selection(result)
    assert selected["status"] == SELECTION_SELECTED
    assert selected["selected_offer"]["retailer"] == "large"


def test_semantic_comparison_unsupported_means_no_selection():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="a", price=1.90),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="b",
            price=2.00,
        ),
    ]

    result = resolve(records, [item("chocolate", category="unknown_category")])

    assert selection(result)["status"] == SELECTION_UNSELECTED
    assert selection(result)["reason"] == {
        "code": SEMANTIC_COMPARISON_NOT_AUTHORIZED
    }
    pair = selection(result)["diagnostics"]["pairs"][0]
    assert pair["comparison_decision"]["eligible"] is False
    assert pair["economic_normalization"] == {"left": None, "right": None}


def test_economic_normalization_unsupported_means_no_selection():
    records = [
        offer("Vanini fondente 91%", retailer="a", price=1.90),
        offer("Vanini fondente 95% 90 g", retailer="b", price=2.00),
    ]

    result = resolve(records, [item("chocolate")])

    assert selection(result)["status"] == SELECTION_UNSELECTED
    assert selection(result)["reason"] == {
        "code": ECONOMIC_NORMALIZATION_NOT_SUPPORTED
    }


def test_incompatible_economic_bases_mean_no_selection():
    records = [
        offer("Latte Intero 1000 ml", retailer="volume", price=1.10),
        offer("Latte Intero 500 g", retailer="mass", price=0.90),
    ]

    result = resolve(
        records,
        [item("milk", "whole_milk", category="chocolate_bar")],
    )

    assert selection(result)["status"] == SELECTION_UNSELECTED
    assert selection(result)["reason"] == {
        "code": ECONOMIC_BASIS_INCOMPATIBLE
    }


def test_exact_tie_produces_no_arbitrary_winner():
    records = [
        offer("Vanini fondente 91% 100 g", retailer="a", price=2.00),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="b",
            price=2.00,
        ),
    ]

    result = resolve(records, [item("chocolate")])

    assert selection(result)["status"] == SELECTION_UNSELECTED
    assert selection(result)["selected_offer"] is None
    assert selection(result)["reason"] == {"code": TIE_FOR_LOWEST_PRICE}
    assert selection(result)["diagnostics"]["pairs"][0]["authorized_order"] == (
        "equal"
    )


def test_reversed_presentation_order_does_not_change_tie_semantics():
    records = [
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="b",
            price=2.00,
        ),
        offer("Vanini fondente 91% 100 g", retailer="a", price=2.00),
    ]

    result = resolve(records, [item("chocolate")])

    assert selection(result)["status"] == SELECTION_UNSELECTED
    assert selection(result)["reason"] == {"code": TIE_FOR_LOWEST_PRICE}


def test_n_way_strict_minimum_requires_cheaper_than_every_other_proof():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="a", price=2.25),
        offer("Vanini fondente 95% 100 g", retailer="b", price=2.60),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="c",
            price=2.20,
        ),
    ]

    result = resolve(records, [item("chocolate")])

    assert selection(result)["status"] == SELECTION_SELECTED
    assert selection(result)["selected_offer"]["retailer"] == "c"
    assert [
        pair["offer_indexes"]
        for pair in selection(result)["diagnostics"]["pairs"]
    ] == [[0, 1], [0, 2], [1, 2]]


def test_one_missing_pair_prevents_unsupported_n_way_winner():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="a", price=2.25),
        offer("Vanini fondente 95% 100 g", retailer="b", price=2.60),
        offer("Vanini fondente 100%", retailer="c", price=1.00),
    ]

    result = resolve(records, [item("chocolate")])

    assert selection(result)["status"] == SELECTION_UNSELECTED
    assert selection(result)["selected_offer"] is None
    assert selection(result)["reason"] == {
        "code": ECONOMIC_NORMALIZATION_NOT_SUPPORTED
    }


def test_partial_success_aggregate_counts():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="a", price=2.25),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="b",
            price=2.30,
        ),
        offer("Latte Intero 1000 ml", retailer="c", price=1.00),
    ]
    items = [
        item("selected-chocolate"),
        item("singleton-milk", "whole_milk", category=None),
        item("missing-passata", "passata", category=None),
        item("unknown-policy", policy="coupon"),
    ]

    result = resolve(records, items)

    assert result["requested_item_count"] == 4
    assert result["selected_item_count"] == 1
    assert result["singleton_item_count"] == 1
    assert result["unselected_item_count"] == 2
    assert result["resolved_item_count"] == 2
    assert result["unresolved_item_count"] == 2


def test_inputs_are_not_mutated():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="a", price=2.25),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="b",
            price=2.30,
        ),
    ]
    items = [item("chocolate")]
    records_before = copy.deepcopy(records)
    items_before = copy.deepcopy(items)

    resolve(records, items)

    assert records == records_before
    assert items == items_before


def test_result_is_deterministic_when_repeated():
    records = [
        offer("Vanini fondente 91% 90 g", retailer="a", price=2.25),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="b",
            price=2.30,
        ),
    ]
    items = [item("chocolate")]

    assert resolve(records, items) == resolve(records, items)
