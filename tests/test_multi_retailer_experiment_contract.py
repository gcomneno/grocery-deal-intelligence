import copy

from experiments.run_multi_retailer_ai_ingestion import (
    FIXTURES,
    evaluate_fixture,
    load_fixture_record,
    summarize_results,
)


class FakeAdapter:
    def __init__(self, candidate):
        self.candidate = candidate

    def propose(self, source_record):
        return copy.deepcopy(self.candidate)


def valid_candidate():
    return {
        "retailer": "lidl",
        "product_name": "Example",
        "price": 1.99,
        "currency": "EUR",
        "promotion": {
            "type": "standard",
            "requires_loyalty": False,
            "discount_text": None,
        },
        "validity": {"from": None, "to": None},
        "locality": {"scope": "unknown", "stores": []},
        "verification": {
            "locality_status": "unknown",
            "evidence_status": "unverified",
        },
        "provenance": {
            "source_type": "fixture",
            "source_url": "https://example.invalid/source",
            "observed_at": "2026-08-26T00:00:00Z",
        },
    }


def test_fixture_corpus_is_fixed_cross_retailer_and_ordered():
    assert len(FIXTURES) == 4
    assert [spec["retailer"] for spec in FIXTURES] == [
        "esselunga",
        "esselunga",
        "lidl",
        "lidl",
    ]
    assert [spec["selector"]["kind"] for spec in FIXTURES] == [
        "item_id",
        "item_id",
        "list_index",
        "list_index",
    ]


def test_all_fixed_real_fixtures_load_with_stable_identity():
    loaded = [load_fixture_record(spec) for spec in FIXTURES]

    assert [identity["retailer"] for _, identity in loaded] == [
        "esselunga",
        "esselunga",
        "lidl",
        "lidl",
    ]
    assert [identity["selector"]["value"] for _, identity in loaded] == [
        "2_27__8400__1",
        "2_27__8400__2",
        0,
        1,
    ]
    assert all(len(identity["file_sha256"]) == 64 for _, identity in loaded)


def test_evaluate_fixture_preserves_source_and_denies_canonical_when_admission_fails():
    source, identity = load_fixture_record(FIXTURES[0])
    before = copy.deepcopy(source)

    result = evaluate_fixture(source, identity, adapter=FakeAdapter(valid_candidate()))

    assert source == before
    assert result["validated"] is True
    assert result["structural_validation"]["valid"] is True
    assert result["admission"]["eligible"] is False
    assert result["canonical"] is None
    assert result["diagnostics"] == []
    assert result["source_evidence"]["retailer"] == "esselunga"
    assert result["source_evidence"]["product_name"] == source["title"]
    assert result["source_evidence"]["price"] == source["promozioni_prezzoPromo"][0]
    assert result["claim_verification"]
    assert sum(result["semantic_summary"].values()) == len(result["claim_verification"])
    assert result["semantic_summary"]["contradicted"] > 0
    assert result["semantic_summary"]["unverifiable"] > 0


def test_evaluate_fixture_can_admit_supported_critical_claims():
    source, identity = load_fixture_record(FIXTURES[2])
    candidate = {
        "retailer": source["retailer"],
        "product_name": source["product_name"],
        "price": source["price"],
        "currency": source["currency"],
        "promotion": {
            "type": source["promotion_type"],
            "requires_loyalty": source["requires_loyalty"],
            "discount_text": source["discount_text"],
        },
        "validity": {
            "from": source["valid_from"],
            "to": source["valid_to"],
        },
        "locality": {
            "scope": "regional",
            "stores": copy.deepcopy(source["locality"]["stores"]),
        },
        "verification": {
            "locality_status": source["verification"]["locality"],
            "evidence_status": "verified",
        },
        "provenance": {
            "source_type": source["provenance"]["source_type"],
            "source_url": source["provenance"]["campaign_url"],
            "observed_at": source["provenance"]["observed_at"],
        },
    }

    result = evaluate_fixture(source, identity, adapter=FakeAdapter(candidate))

    assert result["validated"] is True
    assert result["admission"]["eligible"] is True
    assert result["canonical"] == candidate


def test_evaluate_fixture_rejects_structurally_invalid_candidate_and_reports_admission():
    source, identity = load_fixture_record(FIXTURES[1])
    before = copy.deepcopy(source)
    candidate = valid_candidate()
    candidate["promotion"] = "standard"

    result = evaluate_fixture(source, identity, adapter=FakeAdapter(candidate))

    assert source == before
    assert result["validated"] is False
    assert result["structural_validation"]["valid"] is False
    assert result["admission"]["eligible"] is False
    assert result["canonical"] is None
    assert result["diagnostics"] == [
        {
            "category": "wrong_canonical_shape",
            "path": ["promotion"],
            "validator": "type",
            "message": "expected object; got string",
        }
    ]
    assert result["source_evidence"]["retailer"] == "esselunga"
    assert result["claim_verification"]
    assert sum(result["semantic_summary"].values()) == len(result["claim_verification"])


def test_summary_counts_structural_admission_canonical_and_semantic_results():
    results = [
        {
            "validated": True,
            "canonical": {"x": 1},
            "admission": {"eligible": True, "reasons": []},
            "diagnostics": [],
            "semantic_summary": {
                "supported": 5,
                "contradicted": 0,
                "unverifiable": 2,
            },
        },
        {
            "validated": True,
            "canonical": None,
            "admission": {
                "eligible": False,
                "reasons": [
                    {"code": "contradicted_claim", "path": ["price"]},
                    {"code": "critical_claim_unsupported", "path": ["retailer"]},
                ],
            },
            "diagnostics": [],
            "semantic_summary": {
                "supported": 3,
                "contradicted": 1,
                "unverifiable": 4,
            },
        },
        {
            "validated": False,
            "canonical": None,
            "admission": {
                "eligible": False,
                "reasons": [{"code": "structural_invalid"}],
            },
            "diagnostics": [{"category": "wrong_canonical_shape"}],
            "semantic_summary": {
                "supported": 2,
                "contradicted": 0,
                "unverifiable": 1,
            },
        },
    ]

    assert summarize_results(results) == {
        "total_records": 3,
        "structurally_valid_records": 2,
        "structurally_invalid_records": 1,
        "admission_eligible_records": 1,
        "admission_ineligible_records": 2,
        "canonical_records": 1,
        "diagnostic_category_counts": {"wrong_canonical_shape": 1},
        "admission_reason_counts": {
            "contradicted_claim": 1,
            "critical_claim_unsupported": 1,
            "structural_invalid": 1,
        },
        "total_claims": 18,
        "supported_claims": 10,
        "contradicted_claims": 1,
        "unverifiable_claims": 7,
    }
