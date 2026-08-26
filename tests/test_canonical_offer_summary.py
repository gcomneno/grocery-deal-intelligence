from copy import deepcopy

from grocery_deal_intelligence.summary import summarize_offers


def make_record(
    retailer,
    product_name,
    price,
    currency="EUR",
    promotion_type="test",
    requires_loyalty=False,
    locality_scope="national",
    locality_status="verified",
    evidence_status="verified",
    reference_price=None,
    base_price_text=None,
):
    return {
        "retailer": retailer,
        "product_name": product_name,
        "price": price,
        "currency": currency,
        "reference_price": reference_price,
        "base_price_text": base_price_text,
        "promotion": {
            "type": promotion_type,
            "requires_loyalty": requires_loyalty,
        },
        "validity": {
            "from": None,
            "to": None,
        },
        "locality": {
            "scope": locality_scope,
            "stores": [],
        },
        "verification": {
            "locality_status": locality_status,
            "evidence_status": evidence_status,
        },
        "provenance": {
            "source_type": "test",
            "source_url": "https://example.test/offer",
            "observed_at": "2026-08-26T00:00:00Z",
        },
    }


def test_summary_derives_canonical_dataset_facts():
    offers = [
        make_record(
            "lidl",
            "Latte Fresco",
            1.49,
            promotion_type="lidl_plus",
            requires_loyalty=True,
            locality_scope="regional",
            reference_price=1.99,
            base_price_text="1 kg = 2.98 €",
        ),
        make_record(
            "esselunga",
            "Ananas",
            4.88,
            promotion_type="Sconto %",
            locality_scope="store",
        ),
        make_record(
            "lidl",
            "Pasta",
            0.99,
            promotion_type="lidl_plus",
            requires_loyalty=True,
            locality_status="unknown",
            evidence_status="partial",
        ),
    ]

    summary = summarize_offers(offers)

    assert summary == {
        "total_offers": 3,
        "retailers": ["esselunga", "lidl"],
        "offers_by_retailer": {
            "esselunga": 1,
            "lidl": 2,
        },
        "currencies": ["EUR"],
        "minimum_price": 0.99,
        "maximum_price": 4.88,
        "promotion_types": {
            "Sconto %": 1,
            "lidl_plus": 2,
        },
        "loyalty_required_offers": 2,
        "locality_scopes": {
            "national": 1,
            "regional": 1,
            "store": 1,
        },
        "locality_verification_status": {
            "unknown": 1,
            "verified": 2,
        },
        "evidence_verification_status": {
            "partial": 1,
            "verified": 2,
        },
        "offers_with_reference_price": 1,
        "offers_with_base_price_text": 1,
    }


def test_summary_is_independent_of_source_order():
    offers = [
        make_record("lidl", "Pasta", 0.99),
        make_record("esselunga", "Ananas", 4.88),
        make_record("lidl", "Latte", 1.49),
    ]

    assert summarize_offers(offers) == summarize_offers(list(reversed(offers)))


def test_summary_does_not_mutate_source_dataset():
    offers = [
        make_record("lidl", "Pasta", 0.99),
        make_record("esselunga", "Ananas", 4.88),
    ]
    original = deepcopy(offers)

    summarize_offers(offers)

    assert offers == original


def test_empty_dataset_has_deterministic_summary():
    assert summarize_offers([]) == {
        "total_offers": 0,
        "retailers": [],
        "offers_by_retailer": {},
        "currencies": [],
        "minimum_price": None,
        "maximum_price": None,
        "promotion_types": {},
        "loyalty_required_offers": 0,
        "locality_scopes": {},
        "locality_verification_status": {},
        "evidence_verification_status": {},
        "offers_with_reference_price": 0,
        "offers_with_base_price_text": 0,
    }
