from copy import deepcopy
from pathlib import Path
from types import MappingProxyType

import pytest

import grocery_deal_intelligence.ingestion as ingestion
import grocery_deal_intelligence.ingestion_result_set as result_set_module
from grocery_deal_intelligence.aggregation import aggregate_offers
from grocery_deal_intelligence.carrefour_adapter import adapt_carrefour_fixture_text
from grocery_deal_intelligence.despar_adapter import adapt_despar_fixture_text
from grocery_deal_intelligence.filtering import filter_offers
from grocery_deal_intelligence.ingestion_result_set import IngestionResultSet
from grocery_deal_intelligence.profiling import profile_offers
from grocery_deal_intelligence.query import search_offers
from grocery_deal_intelligence.summary import summarize_offers


_REPO_ROOT = Path(__file__).resolve().parent.parent
_OBSERVED_AT = "2026-08-27T00:00:00Z"


def _carrefour_records():
    path = _REPO_ROOT / "fixtures/carrefour/store-5190-flyer-56879.txt"
    return adapt_carrefour_fixture_text(
        path.read_text(encoding="utf-8"),
        observed_at=_OBSERVED_AT,
        expected_sha256="25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571",
    )


def _despar_records():
    path = _REPO_ROOT / "fixtures/despar/store-191-flyer-2026-08-13.txt"
    return adapt_despar_fixture_text(
        path.read_text(encoding="utf-8"),
        observed_at=_OBSERVED_AT,
        expected_sha256="54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17",
    )


def _carrefour_batch():
    return ingestion.ingest_deterministic_source_records(
        _carrefour_records(),
        retailer="carrefour",
    )


def _despar_batch():
    return ingestion.ingest_deterministic_source_records(
        _despar_records(),
        retailer="despar",
    )


def test_carrefour_result_set_exposes_admitted_canonical_subset():
    result_set = IngestionResultSet(_carrefour_batch())

    assert result_set.retailer == "carrefour"
    assert len(result_set.outcomes) == 3
    assert len(result_set.admitted) == 3
    assert len(result_set.canonical_records) == 3
    assert len(result_set.rejected) == 0
    assert result_set.ai_used is False
    assert result_set.network_required is False


def test_despar_result_set_exposes_fail_closed_rejections():
    result_set = IngestionResultSet(_despar_batch())

    assert result_set.retailer == "despar"
    assert len(result_set.outcomes) == 3
    assert len(result_set.admitted) == 0
    assert len(result_set.canonical_records) == 0
    assert len(result_set.rejected) == 3
    assert result_set.summary["rejection_reasons"] == {
        "structural_invalid": 3
    }


def test_admitted_and_rejected_entries_preserve_original_indexes():
    admitted = IngestionResultSet(_carrefour_batch()).admitted
    rejected = IngestionResultSet(_despar_batch()).rejected

    assert [entry.record_index for entry in admitted] == [0, 1, 2]
    assert [entry.record_index for entry in rejected] == [0, 1, 2]


def test_result_set_preserves_deterministic_ordering():
    batch = _carrefour_batch()
    result_set = IngestionResultSet(batch)

    assert [
        outcome["candidate"]["product_name"]
        for outcome in result_set.outcomes
    ] == [
        outcome["candidate"]["product_name"]
        for outcome in batch["records"]
    ]
    assert [
        record["product_name"]
        for record in result_set.canonical_records
    ] == [
        outcome["canonical"]["product_name"]
        for outcome in result_set.outcomes
    ]


def test_rejected_entries_keep_diagnostics_and_evidence_visible():
    result_set = IngestionResultSet(_despar_batch())
    rejected = result_set.rejected[0].outcome

    assert rejected["canonical"] is None
    assert rejected["admission"]["reasons"] == [
        {"code": "structural_invalid"}
    ]
    assert rejected["structural_validation"]["valid"] is False
    assert rejected["claim_verification"]
    assert rejected["source_evidence"]["retailer"] == "despar"
    assert rejected["source_evidence"]["provenance"]["fixture_sha256"]


def test_result_set_is_isolated_from_caller_mutation():
    batch = _carrefour_batch()
    result_set = IngestionResultSet(batch)
    original_name = result_set.canonical_records[0]["product_name"]

    batch["retailer"] = "mutated"
    batch["summary"]["total_records"] = 0
    batch["records"][0]["canonical"]["product_name"] = "mutated"
    batch["records"][0]["admission"]["eligible"] = False

    assert result_set.retailer == "carrefour"
    assert result_set.summary["total_records"] == 3
    assert result_set.canonical_records[0]["product_name"] == original_name
    assert result_set.admitted[0].outcome["admission"]["eligible"] is True


def test_result_set_deepcopies_incoming_batch_once(monkeypatch):
    batch = _carrefour_batch()
    calls = []

    def recording_deepcopy(value):
        calls.append(value)
        return deepcopy(value)

    monkeypatch.setattr(result_set_module, "deepcopy", recording_deepcopy)

    result_set = IngestionResultSet(batch)

    assert len(calls) == 1
    assert calls[0] is batch
    assert len(result_set.outcomes) == 3


def test_top_level_and_collection_boundaries_are_read_only():
    result_set = IngestionResultSet(_carrefour_batch())

    assert isinstance(result_set.summary, MappingProxyType)
    assert isinstance(result_set.outcomes, tuple)
    assert isinstance(result_set.admitted, tuple)
    assert isinstance(result_set.canonical_records, tuple)
    assert isinstance(result_set.rejected, tuple)

    with pytest.raises(TypeError):
        result_set.summary["total_records"] = 10
    with pytest.raises(TypeError):
        result_set.outcomes[0]["canonical"] = None
    with pytest.raises(TypeError):
        result_set.canonical_records[0]["product_name"] = "mutated"
    with pytest.raises(AttributeError):
        result_set.outcomes.append({})


def test_canonical_mapping_cannot_be_mutated_through_outcome_alias():
    result_set = IngestionResultSet(_carrefour_batch())

    canonical = result_set.canonical_records[0]

    assert result_set.outcomes[0]["canonical"] is canonical
    assert result_set.admitted[0].outcome["canonical"] is canonical

    with pytest.raises(TypeError):
        result_set.outcomes[0]["canonical"]["product_name"] = "mutated"

    with pytest.raises(TypeError):
        result_set.admitted[0].outcome["canonical"]["product_name"] = "mutated"


def test_nested_diagnostics_are_not_recursively_frozen():
    result_set = IngestionResultSet(_despar_batch())

    result_set.rejected[0].outcome["source_evidence"]["test_marker"] = True

    assert result_set.rejected[0].outcome["source_evidence"]["test_marker"] is True


def test_construction_invokes_no_authority_calls(monkeypatch):
    batch = _carrefour_batch()

    def forbidden(*args, **kwargs):
        raise AssertionError("authority call invoked")

    monkeypatch.setattr(
        ingestion,
        "ingest_deterministic_source_record",
        forbidden,
    )
    monkeypatch.setattr(
        ingestion,
        "ingest_deterministic_source_records",
        forbidden,
    )
    monkeypatch.setattr(ingestion, "validate_offers", forbidden)
    monkeypatch.setattr(ingestion, "evaluate_canonical_admission", forbidden)
    monkeypatch.setattr(ingestion, "project_source_evidence", forbidden)
    monkeypatch.setattr(ingestion, "verify_candidate_claims", forbidden)

    result_set = IngestionResultSet(batch)

    assert len(result_set.canonical_records) == 3


def test_canonical_records_work_with_existing_consumers():
    result_set = IngestionResultSet(_carrefour_batch())
    canonical_records = result_set.canonical_records

    assert search_offers(canonical_records, "latte")
    assert filter_offers(canonical_records, retailer="carrefour")
    assert aggregate_offers(
        canonical_records,
        dimension="retailer",
    ) == {
        "dimension": "retailer",
        "groups": {"carrefour": 3},
    }
    assert summarize_offers(canonical_records)["total_offers"] == 3
    assert profile_offers(canonical_records)["total_records"] == 3


def test_canonical_records_are_already_admitted_values_from_snapshot():
    batch = _carrefour_batch()
    result_set = IngestionResultSet(batch)

    assert [
        dict(record)
        for record in result_set.canonical_records
    ] == [
        outcome["canonical"]
        for outcome in deepcopy(batch)["records"]
    ]


def test_malformed_batch_result_fails_explicitly():
    with pytest.raises(ValueError, match="batch result must be a mapping"):
        IngestionResultSet([])


def test_malformed_retailer_fails_explicitly():
    batch = _carrefour_batch()
    batch["retailer"] = ""

    with pytest.raises(ValueError, match="retailer"):
        IngestionResultSet(batch)


def test_malformed_records_collection_fails_explicitly():
    batch = _carrefour_batch()
    batch["records"] = tuple(batch["records"])

    with pytest.raises(ValueError, match="records"):
        IngestionResultSet(batch)


def test_malformed_summary_fails_explicitly():
    batch = _carrefour_batch()
    batch["summary"] = []

    with pytest.raises(ValueError, match="summary"):
        IngestionResultSet(batch)


@pytest.mark.parametrize("key", ["ai_used", "network_required"])
def test_malformed_top_level_boolean_metadata_fails_explicitly(key):
    batch = _carrefour_batch()
    batch[key] = None

    with pytest.raises(ValueError, match=key):
        IngestionResultSet(batch)


def test_malformed_outcome_fails_explicitly():
    batch = _carrefour_batch()
    batch["records"][0] = []

    with pytest.raises(ValueError, match="outcome at record_index 0"):
        IngestionResultSet(batch)


def test_malformed_admission_fails_explicitly():
    batch = _carrefour_batch()
    batch["records"][0]["admission"] = []

    with pytest.raises(ValueError, match="admission"):
        IngestionResultSet(batch)


@pytest.mark.parametrize("eligible", [1, "true", None])
def test_malformed_eligibility_fails_explicitly(eligible):
    batch = _carrefour_batch()
    batch["records"][0]["admission"]["eligible"] = eligible

    with pytest.raises(ValueError, match="actual boolean"):
        IngestionResultSet(batch)


def test_missing_eligibility_fails_explicitly():
    batch = _carrefour_batch()
    del batch["records"][0]["admission"]["eligible"]

    with pytest.raises(ValueError, match="eligible is required"):
        IngestionResultSet(batch)


def test_eligible_outcome_without_canonical_mapping_fails_explicitly():
    batch = _carrefour_batch()
    batch["records"][0]["canonical"] = None

    with pytest.raises(ValueError, match="requires a non-null canonical mapping"):
        IngestionResultSet(batch)


def test_ineligible_outcome_with_canonical_mapping_fails_explicitly():
    batch = _despar_batch()
    batch["records"][0]["canonical"] = {
        "retailer": "despar",
        "product_name": "synthetic",
    }

    with pytest.raises(ValueError, match="requires canonical to be None"):
        IngestionResultSet(batch)


@pytest.mark.parametrize(
    ("summary_key", "value"),
    [
        ("total_records", 2),
        ("admission_eligible", 2),
        ("admission_ineligible", 1),
        ("canonical_records", 2),
    ],
)
def test_inconsistent_summary_counts_fail_explicitly(summary_key, value):
    batch = _carrefour_batch()
    batch["summary"][summary_key] = value

    with pytest.raises(ValueError, match=summary_key):
        IngestionResultSet(batch)


@pytest.mark.parametrize(
    "summary_key",
    [
        "total_records",
        "admission_eligible",
        "admission_ineligible",
        "canonical_records",
        "structurally_valid",
        "structurally_invalid",
    ],
)
def test_negative_summary_counts_fail_explicitly(summary_key):
    batch = _carrefour_batch()
    batch["summary"][summary_key] = -1

    with pytest.raises(ValueError, match="non-negative integer count"):
        IngestionResultSet(batch)


def test_inconsistent_structural_counts_fail_explicitly():
    batch = _carrefour_batch()
    batch["summary"]["structurally_invalid"] = 1

    with pytest.raises(ValueError, match="structural counts"):
        IngestionResultSet(batch)


def test_missing_structural_partner_count_fails_explicitly():
    batch = _carrefour_batch()
    del batch["summary"]["structurally_invalid"]

    with pytest.raises(ValueError, match="structurally_invalid"):
        IngestionResultSet(batch)
