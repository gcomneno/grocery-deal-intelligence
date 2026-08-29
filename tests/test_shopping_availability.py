import copy

from grocery_deal_intelligence.shopping_availability import (
    AVAILABLE,
    EVIDENCE_UNVERIFIED,
    LOCALITY_UNVERIFIED,
    NOT_CURRENT,
    OUTSIDE_REQUESTED_LOCALITY,
    PRODUCT_FAMILY_MISMATCH,
    UNKNOWN,
    VALIDITY_UNAVAILABLE,
    resolve_shopping_item_availability,
)


AS_OF = "2026-08-29"


def offer(
    product_name,
    *,
    retailer="example",
    price=2.19,
    valid_from="2026-08-27",
    valid_to="2026-09-06",
    evidence_status="verified",
    locality_status="verified",
    locality_scope="store",
    stores=None,
):
    return {
        "retailer": retailer,
        "product_name": product_name,
        "price": price,
        "currency": "EUR",
        "packaging_text": None,
        "validity": {
            "from": valid_from,
            "to": valid_to,
        },
        "locality": {
            "scope": locality_scope,
            "stores": list(stores or ["store-lucca"]),
        },
        "verification": {
            "locality_status": locality_status,
            "evidence_status": evidence_status,
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


def test_zero_eligible_offers_is_unknown_and_preserves_rejections():
    records = [
        offer("Bahlsen Waffeletten Fondente 100 g"),
        offer(
            "Vanini fondente 95% 90 g",
            valid_from="2026-08-12",
            valid_to="2026-08-26",
        ),
    ]

    result = resolve_shopping_item_availability(
        records,
        product_family="dark_chocolate",
        as_of=AS_OF,
        locality_scope="store",
        stores=["store-lucca"],
    )

    assert result["status"] == UNKNOWN
    assert result["offer_count"] == 0
    assert result["offers"] == []
    assert [item["code"] for item in result["rejections"]] == [
        PRODUCT_FAMILY_MISMATCH,
        NOT_CURRENT,
    ]


def test_single_verified_current_offer_is_valid_where_plus_price_answer():
    record = offer(
        "Vanini fondente 95% 90 g",
        retailer="esselunga",
        price=2.19,
        stores=["esselunga-porcari"],
    )

    result = resolve_shopping_item_availability(
        [record],
        product_family="dark_chocolate",
        as_of=AS_OF,
        locality_scope="store",
        stores=["esselunga-porcari"],
    )

    assert result["status"] == AVAILABLE
    assert result["offer_count"] == 1
    assert result["rejections"] == []

    resolved = result["offers"][0]
    assert resolved["retailer"] == "esselunga"
    assert resolved["product_name"] == "Vanini fondente 95% 90 g"
    assert resolved["price"] == 2.19
    assert resolved["currency"] == "EUR"
    assert resolved["locality"] == {
        "scope": "store",
        "stores": ["esselunga-porcari"],
    }
    assert resolved["product_family"] == "dark_chocolate"
    assert resolved["quantity"] == {
        "value": 90,
        "unit": "g",
        "dimension": "mass",
    }
    assert (
        resolved["product_family_claim"]["policy_id"]
        == "builtin:product-family-lexical-evidence:v0.2"
    )


def test_single_offer_result_makes_no_comparative_superiority_claim():
    result = resolve_shopping_item_availability(
        [offer("Vanini fondente 91% 90 g")],
        product_family="dark_chocolate",
        as_of=AS_OF,
    )

    serialized_keys = {
        key
        for key in result
    } | {
        key
        for resolved in result["offers"]
        for key in resolved
    }

    assert "best" not in serialized_keys
    assert "cheapest" not in serialized_keys
    assert "winner" not in serialized_keys
    assert "comparison" not in serialized_keys


def test_multiple_offers_are_availability_results_not_implicit_comparison():
    records = [
        offer(
            "Vanini fondente 95% 90 g",
            retailer="z-retailer",
            price=2.19,
        ),
        offer(
            "Otto Chocolates Cioccolato Fondente Senza Zucchero 60% 100 g",
            retailer="a-retailer",
            price=1.89,
        ),
    ]

    result = resolve_shopping_item_availability(
        records,
        product_family="dark_chocolate",
        as_of=AS_OF,
    )

    assert result["status"] == AVAILABLE
    assert result["offer_count"] == 2
    assert [
        item["retailer"] for item in result["offers"]
    ] == [
        "a-retailer",
        "z-retailer",
    ]
    assert "comparison" not in result


def test_current_validity_must_be_explicitly_supported():
    records = [
        offer(
            "Vanini fondente 91% 90 g",
            valid_from=None,
            valid_to=None,
        ),
        offer(
            "Vanini fondente 95% 90 g",
            valid_from="not-a-date",
        ),
    ]

    result = resolve_shopping_item_availability(
        records,
        product_family="dark_chocolate",
        as_of=AS_OF,
    )

    assert result["status"] == UNKNOWN
    assert {
        item["code"] for item in result["rejections"]
    } == {VALIDITY_UNAVAILABLE}


def test_evidence_and_locality_must_be_verified_before_emission():
    records = [
        offer(
            "Vanini fondente 91% 90 g",
            evidence_status="partial",
        ),
        offer(
            "Vanini fondente 95% 90 g",
            locality_status="unknown",
        ),
    ]

    result = resolve_shopping_item_availability(
        records,
        product_family="dark_chocolate",
        as_of=AS_OF,
    )

    assert result["status"] == UNKNOWN
    assert {
        item["code"] for item in result["rejections"]
    } == {
        EVIDENCE_UNVERIFIED,
        LOCALITY_UNVERIFIED,
    }


def test_requested_locality_excludes_unrelated_verified_store():
    records = [
        offer(
            "Vanini fondente 91% 90 g",
            retailer="lucca",
            stores=["store-lucca"],
        ),
        offer(
            "Vanini fondente 95% 90 g",
            retailer="milano",
            stores=["store-milano"],
        ),
    ]

    result = resolve_shopping_item_availability(
        records,
        product_family="dark_chocolate",
        as_of=AS_OF,
        locality_scope="store",
        stores=["store-lucca"],
    )

    assert result["status"] == AVAILABLE
    assert result["offer_count"] == 1
    assert result["offers"][0]["retailer"] == "lucca"
    assert result["rejections"][0]["code"] == (
        OUTSIDE_REQUESTED_LOCALITY
    )


def test_wrong_family_keyword_match_is_rejected_by_hardened_verifier():
    result = resolve_shopping_item_availability(
        [
            offer("Bahlsen Waffeletten Fondente 100 g"),
            offer(
                "FITNESS Cioccolato Fondente Cereali Integrali "
                "con Fiocchi al Cioccolato 325g"
            ),
            offer(
                "NUII Mini Adventure Caramello Salato e Noci "
                "Macadamia e Cioccolato Fondente e Mirtilli "
                "6 Gelati 253g"
            ),
        ],
        product_family="dark_chocolate",
        as_of=AS_OF,
    )

    assert result["status"] == UNKNOWN
    assert result["offer_count"] == 0
    assert {
        item["code"] for item in result["rejections"]
    } == {PRODUCT_FAMILY_MISMATCH}


def test_resolver_does_not_mutate_inputs_and_is_deterministic():
    records = [
        offer(
            "Vanini fondente assoluto 100% 90 g",
            retailer="esselunga",
        ),
        offer("Bahlsen Waffeletten Fondente 100 g"),
    ]
    original = copy.deepcopy(records)

    first = resolve_shopping_item_availability(
        records,
        product_family="dark_chocolate",
        as_of=AS_OF,
    )
    second = resolve_shopping_item_availability(
        records,
        product_family="dark_chocolate",
        as_of=AS_OF,
    )

    assert records == original
    assert first == second
