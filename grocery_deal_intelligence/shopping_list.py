from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from typing import Any, Callable

from .comparison_policy import (
    evaluate_comparison_policy,
    resolve_comparison_policy,
)
from .economic_normalization import normalize_economic_basis
from .price_comparison import (
    BASIS_INCOMPATIBLE,
    EQUAL,
    LEFT_CHEAPER,
    NORMALIZATION_INVALID,
    NORMALIZATION_NOT_SUPPORTED,
    RATIO_INVALID,
    RIGHT_CHEAPER,
    compare_normalized_prices,
)
from .product_attributes import (
    comparison_verification_from_attributes,
    normalize_product_attributes,
)
from .shopping_availability import (
    _coerce_date,
    resolve_shopping_item_availability,
)


LOWEST_PRICE = "lowest_price"

SELECTION_SELECTED = "selected"
SELECTION_SINGLETON = "singleton"
SELECTION_UNSELECTED = "unselected"

NO_ELIGIBLE_OFFERS = "no_eligible_offers"
SINGLETON_AVAILABLE = "singleton_available"
UNKNOWN_SELECTION_POLICY = "unknown_selection_policy"
COMPARISON_CATEGORY_REQUIRED = "comparison_category_required"
NO_STRICT_MINIMUM = "no_strict_minimum"
TIE_FOR_LOWEST_PRICE = "tie_for_lowest_price"
SEMANTIC_COMPARISON_NOT_AUTHORIZED = "semantic_comparison_not_authorized"
ECONOMIC_NORMALIZATION_NOT_SUPPORTED = "economic_normalization_not_supported"
ECONOMIC_NORMALIZATION_INVALID = "economic_normalization_invalid"
ECONOMIC_BASIS_INCOMPATIBLE = "economic_basis_incompatible"
EXACT_RATIO_INVALID = "exact_ratio_invalid"

_STRICT_LOWEST_CLAIM = "strict_lowest_supported_normalized_price"

_BLOCKING_REASON_PRECEDENCE = (
    SEMANTIC_COMPARISON_NOT_AUTHORIZED,
    ECONOMIC_NORMALIZATION_NOT_SUPPORTED,
    ECONOMIC_NORMALIZATION_INVALID,
    ECONOMIC_BASIS_INCOMPATIBLE,
    EXACT_RATIO_INVALID,
)


def resolve_shopping_list(
    records: Iterable[Mapping[str, Any]],
    *,
    items: Sequence[Mapping[str, Any]],
    as_of: Any,
    locality_scope: str | None = None,
    stores: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Resolve caller-ordered shopping items through explicit policy dispatch."""
    records_copy = [deepcopy(dict(record)) for record in records]
    resolved_as_of = _coerce_date(as_of).isoformat()
    item_results: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, Mapping):
            raise TypeError("shopping-list items must be mappings")
        item_copy = deepcopy(dict(item))
        item_id = item_copy.get("id")
        product_family = item_copy.get("product_family")
        policy_id = item_copy.get("selection_policy")

        if not isinstance(item_id, str) or not item_id:
            raise ValueError("shopping-list item id must be a non-empty string")
        if not isinstance(product_family, str) or not product_family:
            raise ValueError("shopping-list item product_family must be a non-empty string")
        if not isinstance(policy_id, str) or not policy_id:
            raise ValueError("shopping-list item selection_policy must be a non-empty string")

        availability = resolve_shopping_item_availability(
            records_copy,
            product_family=product_family,
            as_of=resolved_as_of,
            locality_scope=locality_scope,
            stores=stores,
        )
        availability_as_of = availability.pop("as_of", None)
        if availability_as_of != resolved_as_of:
            raise ValueError("availability as_of diverged from shopping-list as_of")

        selector = _SELECTION_POLICIES.get(policy_id)
        if selector is None:
            selection = _unselected(
                policy_id,
                UNKNOWN_SELECTION_POLICY,
                diagnostics={"pairs": []},
            )
        else:
            selection = selector(
                availability,
                item_copy,
                policy_id=policy_id,
            )

        item_results.append(
            {
                "id": item_id,
                "product_family": product_family,
                "selection_policy": policy_id,
                "availability": availability,
                "selection": selection,
            }
        )

    selected_count = _count_status(item_results, SELECTION_SELECTED)
    singleton_count = _count_status(item_results, SELECTION_SINGLETON)
    unselected_count = _count_status(item_results, SELECTION_UNSELECTED)

    return {
        "version": "0.1",
        "as_of": resolved_as_of,
        "requested_item_count": len(item_results),
        "resolved_item_count": selected_count + singleton_count,
        "unresolved_item_count": unselected_count,
        "selected_item_count": selected_count,
        "singleton_item_count": singleton_count,
        "unselected_item_count": unselected_count,
        "items": item_results,
    }


def _select_lowest_price(
    availability: Mapping[str, Any],
    item: Mapping[str, Any],
    *,
    policy_id: str,
) -> dict[str, Any]:
    offers = deepcopy(list(availability.get("offers", [])))

    if len(offers) == 0:
        return _unselected(
            policy_id,
            NO_ELIGIBLE_OFFERS,
            diagnostics={"pairs": []},
        )

    if len(offers) == 1:
        return {
            "policy_id": policy_id,
            "status": SELECTION_SINGLETON,
            "selected_offer": None,
            "sole_offer": deepcopy(offers[0]),
            "reason": {"code": SINGLETON_AVAILABLE},
            "comparative_claim": None,
            "diagnostics": {"pairs": []},
        }

    category = item.get("comparison_category")
    if not isinstance(category, str) or not category:
        return _unselected(
            policy_id,
            COMPARISON_CATEGORY_REQUIRED,
            diagnostics={"pairs": []},
        )

    pair_diagnostics: list[dict[str, Any]] = []
    cheaper_than: dict[int, set[int]] = {index: set() for index in range(len(offers))}
    unsupported_reasons: list[str] = []
    has_tie = False

    for left_index in range(len(offers)):
        for right_index in range(left_index + 1, len(offers)):
            pair = _evaluate_pair(
                offers,
                left_index,
                right_index,
                category=category,
            )
            pair_diagnostics.append(pair)

            authorized_order = pair["authorized_order"]
            if authorized_order == LEFT_CHEAPER:
                cheaper_than[left_index].add(right_index)
            elif authorized_order == RIGHT_CHEAPER:
                cheaper_than[right_index].add(left_index)
            elif authorized_order == EQUAL:
                has_tie = True
            else:
                unsupported_reasons.append(pair["selection_blocker"]["code"])

    diagnostics = {"pairs": pair_diagnostics}
    required_other_count = len(offers) - 1
    strict_minima = [
        index
        for index, proven_less_than in cheaper_than.items()
        if len(proven_less_than) == required_other_count
    ]

    if len(strict_minima) == 1:
        selected_index = strict_minima[0]
        return {
            "policy_id": policy_id,
            "status": SELECTION_SELECTED,
            "selected_offer": deepcopy(offers[selected_index]),
            "sole_offer": None,
            "reason": None,
            "comparative_claim": _STRICT_LOWEST_CLAIM,
            "diagnostics": diagnostics,
        }

    if unsupported_reasons:
        reason_code = _blocking_reason(unsupported_reasons)
    elif has_tie:
        reason_code = TIE_FOR_LOWEST_PRICE
    else:
        reason_code = NO_STRICT_MINIMUM

    return _unselected(
        policy_id,
        reason_code,
        diagnostics=diagnostics,
    )


def _evaluate_pair(
    offers: list[Mapping[str, Any]],
    left_index: int,
    right_index: int,
    *,
    category: str,
) -> dict[str, Any]:
    left_offer = deepcopy(dict(offers[left_index]))
    right_offer = deepcopy(dict(offers[right_index]))
    left_attributes = _normalize_offer_attributes(left_offer)
    right_attributes = _normalize_offer_attributes(right_offer)
    semantic_verification = comparison_verification_from_attributes(
        left_attributes,
        right_attributes,
    )
    resolved_policy = resolve_comparison_policy(category=category)
    comparison_decision = evaluate_comparison_policy(
        semantic_verification,
        resolved_policy,
    )

    left_economic = None
    right_economic = None
    price_comparison = None
    authorized_order = None
    blocker = None

    if comparison_decision.get("eligible") is not True:
        blocker = {"code": SEMANTIC_COMPARISON_NOT_AUTHORIZED}
    else:
        left_economic = normalize_economic_basis(
            left_offer,
            left_attributes,
            comparison_decision=comparison_decision,
        )
        right_economic = normalize_economic_basis(
            right_offer,
            right_attributes,
            comparison_decision=comparison_decision,
        )
        price_comparison = compare_normalized_prices(
            left_economic,
            right_economic,
        )

        if price_comparison.get("status") == "supported":
            authorized_order = price_comparison["result"]["outcome"]
        else:
            blocker = {"code": _price_failure_reason(price_comparison)}

    return {
        "offer_indexes": [left_index, right_index],
        "offers": {
            "left": left_offer,
            "right": right_offer,
        },
        "normalized_attributes": {
            "left": left_attributes,
            "right": right_attributes,
        },
        "semantic_verification": semantic_verification,
        "resolved_comparison_policy": resolved_policy,
        "comparison_decision": comparison_decision,
        "economic_normalization": {
            "left": left_economic,
            "right": right_economic,
        },
        "price_comparison": price_comparison,
        "authorized_order": authorized_order,
        "selection_blocker": blocker,
    }


def _normalize_offer_attributes(offer: Mapping[str, Any]) -> dict[str, Any]:
    family = offer.get("product_family")
    if not isinstance(family, str) or not family:
        raise ValueError("eligible offers must preserve product_family")
    return normalize_product_attributes(
        offer,
        product_family_candidate={
            "value": family,
            "evidence_path": ["product_name"],
        },
    )


def _blocking_reason(reasons: Sequence[str]) -> str:
    observed = set(reasons)
    for code in _BLOCKING_REASON_PRECEDENCE:
        if code in observed:
            return code
    return min(observed) if observed else NO_STRICT_MINIMUM


def _price_failure_reason(price_comparison: Mapping[str, Any]) -> str:
    reasons = price_comparison.get("reasons")
    code = None
    if isinstance(reasons, list) and reasons:
        first = reasons[0]
        if isinstance(first, Mapping):
            code = first.get("code")

    return {
        NORMALIZATION_NOT_SUPPORTED: ECONOMIC_NORMALIZATION_NOT_SUPPORTED,
        NORMALIZATION_INVALID: ECONOMIC_NORMALIZATION_INVALID,
        BASIS_INCOMPATIBLE: ECONOMIC_BASIS_INCOMPATIBLE,
        RATIO_INVALID: EXACT_RATIO_INVALID,
    }.get(code, ECONOMIC_NORMALIZATION_NOT_SUPPORTED)


def _unselected(
    policy_id: str,
    code: str,
    *,
    diagnostics: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "policy_id": policy_id,
        "status": SELECTION_UNSELECTED,
        "selected_offer": None,
        "sole_offer": None,
        "reason": {"code": code},
        "comparative_claim": None,
        "diagnostics": deepcopy(dict(diagnostics)),
    }


def _count_status(items: Sequence[Mapping[str, Any]], status: str) -> int:
    return sum(
        1
        for item in items
        if item["selection"]["status"] == status
    )


_Selector = Callable[[Mapping[str, Any], Mapping[str, Any]], dict[str, Any]]
_SELECTION_POLICIES: dict[str, _Selector] = {
    LOWEST_PRICE: _select_lowest_price,
}
