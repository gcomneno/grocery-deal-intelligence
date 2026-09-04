import copy

from grocery_deal_intelligence.source_evidence import (
    CONTRADICTED,
    SUPPORTED,
    UNVERIFIABLE,
    project_source_evidence,
    summarize_claim_verification,
    verify_candidate_claims,
)


def make_lidl_source():
    return {
        "retailer": "lidl",
        "product_name": "Controfiletti di pollo",
        "price": 2.69,
        "currency": "EUR",
        "reference_price": 3.69,
        "packaging_text": "400 g confezione",
        "base_price_text": "1 kg = 6.73 €",
        "promotion_type": "lidl_plus",
        "requires_loyalty": True,
        "discount_text": "-27%",
        "valid_from": "2026-08-14T12:32:41.009Z",
        "valid_to": "2026-08-26T22:00Z",
        "locality": {
            "offer_region": "600",
            "offer_region_name": "Pontedera - Toscana",
            "stores": ["IT01621", "IT00302"],
        },
        "provenance": {
            "campaign_url": "https://www.lidl.it/c/example",
            "flyer_id": "flyer-1",
            "observed_at": "2026-08-25T16:24:40+00:00",
            "source_type": "official_web",
        },
        "verification": {
            "flyer_match": "unmatched",
            "flyer_pages": [],
            "locality": "verified",
        },
    }


def make_esselunga_source():
    return {
        "title": "FORST V.I.P. Pils CAN 3 x 0,33 l",
        "prezzo": 2.33,
        "promozioni_prezzoPromo": [1.83],
        "promozioni_dataInizioPromoArticolo": ["2026-08-24T00:00:00Z"],
        "promozioni_dataFinePromoArticolo": ["2026-09-20T00:00:00Z"],
        "promozioni_desMeccanica": ["Sc + Facile val"],
    }


def result_by_path(results):
    return {tuple(item["path"]): item for item in results}


def test_lidl_projection_contains_explicit_and_justified_canonical_claims():
    source = make_lidl_source()
    evidence = project_source_evidence(source, retailer="lidl")

    assert evidence["retailer"] == "lidl"
    assert evidence["price"] == 2.69
    assert evidence["currency"] == "EUR"
    assert evidence["promotion"] == {
        "type": "lidl_plus",
        "requires_loyalty": True,
        "discount_text": "-27%",
    }
    assert evidence["validity"] == {
        "from": "2026-08-14T12:32:41.009Z",
        "to": "2026-08-26T22:00Z",
    }
    assert evidence["locality"] == {
        "stores": ["IT01621", "IT00302"],
        "scope": "store",
    }
    assert evidence["verification"]["locality_status"] == "verified"
    assert evidence["verification"]["evidence_status"] == "unmatched"
    assert evidence["provenance"]["source_url"] == "https://www.lidl.it/c/example"


def test_lidl_locality_scope_requires_verified_nonempty_store_ids():
    source = make_lidl_source()
    source["verification"]["locality"] = "unverified"
    evidence = project_source_evidence(source, retailer="lidl")
    assert "scope" not in evidence["locality"]

    source = make_lidl_source()
    source["locality"]["stores"] = []
    evidence = project_source_evidence(source, retailer="lidl")
    assert evidence["locality"] == {"stores": []}

    source = make_lidl_source()
    source["locality"]["stores"] = [""]
    evidence = project_source_evidence(source, retailer="lidl")
    assert "scope" not in evidence["locality"]


def test_lidl_evidence_status_mapping_is_finite_and_conservative():
    expected = {
        "exact": "verified",
        "partial": "partial",
        "unmatched": "unmatched",
        "unverified": "unverified",
    }

    for flyer_match, canonical_status in expected.items():
        source = make_lidl_source()
        source["verification"]["flyer_match"] = flyer_match
        evidence = project_source_evidence(source, retailer="lidl")
        assert evidence["verification"]["evidence_status"] == canonical_status

    source = make_lidl_source()
    source["verification"]["flyer_match"] = "mystery"
    evidence = project_source_evidence(source, retailer="lidl")
    assert "evidence_status" not in evidence["verification"]


def test_esselunga_projection_uses_trusted_retailer_context_and_explicit_fields_only():
    evidence = project_source_evidence(make_esselunga_source(), retailer="esselunga")

    assert evidence == {
        "retailer": "esselunga",
        "product_name": "FORST V.I.P. Pils CAN 3 x 0,33 l",
        "price": 1.83,
        "reference_price": 2.33,
        "validity": {
            "from": "2026-08-24T00:00:00Z",
            "to": "2026-09-20T00:00:00Z",
        },
        "promotion": {"discount_text": "Sc + Facile val"},
    }
    assert "currency" not in evidence


def test_claim_verification_distinguishes_supported_contradicted_and_unverifiable():
    evidence = project_source_evidence(make_esselunga_source(), retailer="esselunga")
    candidate = {
        "retailer": "FORST",
        "product_name": "FORST V.I.P. Pils CAN 3 x 0,33 l",
        "price": 1.85,
        "currency": "EUR",
        "validity": {
            "from": "2026-08-24T00:00:00Z",
            "to": "2026-09-20T00:00:00Z",
        },
        "locality": {
            "scope": "national",
            "stores": ["www.esselunga.it"],
        },
    }

    results = result_by_path(verify_candidate_claims(candidate, evidence))

    assert results[("retailer",)]["status"] == CONTRADICTED
    assert results[("product_name",)]["status"] == SUPPORTED
    assert results[("price",)]["status"] == CONTRADICTED
    assert results[("currency",)]["status"] == UNVERIFIABLE
    assert results[("validity", "from")]["status"] == SUPPORTED
    assert results[("locality", "scope")]["status"] == UNVERIFIABLE


def test_unverifiable_is_not_treated_as_contradicted():
    results = verify_candidate_claims(
        {"provenance": {"observed_at": "2023-06-26T08:00:00Z"}},
        {},
    )

    assert results == [
        {
            "path": ["provenance", "observed_at"],
            "candidate_value": "2023-06-26T08:00:00Z",
            "status": UNVERIFIABLE,
        }
    ]


def test_projection_and_verification_do_not_mutate_inputs():
    source = make_lidl_source()
    candidate = {
        "retailer": "lidl",
        "locality": {"scope": "store", "stores": ["IT01621", "IT00302"]},
    }
    source_before = copy.deepcopy(source)
    candidate_before = copy.deepcopy(candidate)

    evidence = project_source_evidence(source, retailer="lidl")
    evidence_before = copy.deepcopy(evidence)
    verify_candidate_claims(candidate, evidence)

    assert source == source_before
    assert candidate == candidate_before
    assert evidence == evidence_before


def test_claim_verification_output_is_deterministically_ordered_and_summarized():
    results = verify_candidate_claims(
        {"z": 1, "a": {"y": 2, "x": 3}},
        {"z": 1, "a": {"x": 4}},
    )

    assert [item["path"] for item in results] == [["a", "x"], ["a", "y"], ["z"]]
    assert summarize_claim_verification(results) == {
        SUPPORTED: 1,
        CONTRADICTED: 1,
        UNVERIFIABLE: 1,
    }
