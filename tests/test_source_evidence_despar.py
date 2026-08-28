from copy import deepcopy

from grocery_deal_intelligence.source_evidence import project_source_evidence


def test_despar_projection_preserves_only_supported_claims():
    source = {
        "retailer": "despar",
        "product_name": "Example",
        "price": 1.99,
        "currency": "EUR",
        "packaging_text": "1 kg",
        "discount_text": "Sconto -20%",
        "valid_from": "2026-08-13",
        "valid_to": "2026-08-26",
        "locality": {
            "scope": "store",
            "stores": ["191"],
            "store_name": "Interspar Montebelluna",
            "store_address": "Via Schiavonesca Priula, 64",
            "store_locality": "Montebelluna (TV)",
        },
        "verification": {
            "locality_status": "verified",
            "evidence_status": "verified",
        },
        "provenance": {
            "source_type": "official_store_scoped_flyer_fixture",
            "source_url": "https://www.despar.it/it/volantino-digitale/191/",
            "observed_at": "2026-08-27T00:00:00Z",
            "fixture_sha256": "a" * 64,
            "campaign_title": "Campaign",
        },
    }
    before = deepcopy(source)

    evidence = project_source_evidence(source, retailer="despar")

    assert evidence == {
        "retailer": "despar",
        "product_name": "Example",
        "price": 1.99,
        "currency": "EUR",
        "packaging_text": "1 kg",
        "promotion": {"discount_text": "Sconto -20%"},
        "validity": {"from": "2026-08-13", "to": "2026-08-26"},
        "locality": deepcopy(source["locality"]),
        "verification": deepcopy(source["verification"]),
        "provenance": deepcopy(source["provenance"]),
    }
    assert "type" not in evidence["promotion"]
    assert "requires_loyalty" not in evidence["promotion"]
    assert source == before
