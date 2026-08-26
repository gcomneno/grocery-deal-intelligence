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


def test_evaluate_fixture_preserves_source_and_accepts_valid_candidate():
    source, identity = load_fixture_record(FIXTURES[0])
    before = copy.deepcopy(source)

    result = evaluate_fixture(source, identity, adapter=FakeAdapter(valid_candidate()))

    assert source == before
    assert result["validated"] is True
    assert result["canonical"] == valid_candidate()
    assert result["diagnostics"] == []


def test_evaluate_fixture_rejects_and_diagnoses_invalid_candidate():
    source, identity = load_fixture_record(FIXTURES[1])
    before = copy.deepcopy(source)
    candidate = valid_candidate()
    candidate["promotion"] = "standard"

    result = evaluate_fixture(source, identity, adapter=FakeAdapter(candidate))

    assert source == before
    assert result["validated"] is False
    assert result["canonical"] is None
    assert result["diagnostics"] == [
        {
            "category": "wrong_canonical_shape",
            "path": ["promotion"],
            "validator": "type",
            "message": "expected object; got string",
        }
    ]


def test_summary_is_deterministic_and_counts_diagnostic_categories():
    results = [
        {"validated": True, "diagnostics": []},
        {
            "validated": False,
            "diagnostics": [
                {"category": "wrong_canonical_shape"},
                {"category": "missing_required_field"},
            ],
        },
        {
            "validated": False,
            "diagnostics": [
                {"category": "wrong_canonical_shape"},
            ],
        },
    ]

    assert summarize_results(results) == {
        "total_records": 3,
        "accepted_records": 1,
        "rejected_records": 2,
        "diagnostic_category_counts": {
            "missing_required_field": 1,
            "wrong_canonical_shape": 2,
        },
    }
