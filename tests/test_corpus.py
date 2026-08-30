from copy import deepcopy
from pathlib import Path
from types import MappingProxyType

import pytest

from grocery_deal_intelligence import ingestion
from grocery_deal_intelligence.carrefour_adapter import adapt_carrefour_fixture_text
from grocery_deal_intelligence.corpus import assemble_corpus
from grocery_deal_intelligence.current_offers import list_current_offers
from grocery_deal_intelligence.despar_adapter import adapt_despar_fixture_text
from grocery_deal_intelligence.ingestion_result_set import IngestionResultSet
from grocery_deal_intelligence.retailers import list_available_retailers

_REPO_ROOT = Path(__file__).resolve().parent.parent
_OBSERVED_AT = "2026-08-27T00:00:00Z"


def _carrefour_records():
    path = _REPO_ROOT / "fixtures/carrefour/store-5190-flyer-56879.txt"
    return adapt_carrefour_fixture_text(
        path.read_text(encoding="utf-8"),
        observed_at=_OBSERVED_AT,
        expected_sha256=(
            "25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571"
        ),
    )


def _despar_records():
    path = _REPO_ROOT / "fixtures/despar/store-191-flyer-2026-08-13.txt"
    return adapt_despar_fixture_text(
        path.read_text(encoding="utf-8"),
        observed_at=_OBSERVED_AT,
        expected_sha256=(
            "54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17"
        ),
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


def _rejected_despar_batch():
    batch = _despar_batch()

    for outcome in batch["records"]:
        outcome["validated"] = False
        outcome["structural_validation"]["valid"] = False
        outcome["admission"] = {
            "eligible": False,
            "reasons": [{"code": "structural_invalid"}],
        }
        outcome["canonical"] = None

    batch["summary"]["structurally_valid"] = 0
    batch["summary"]["structurally_invalid"] = 3
    batch["summary"]["admission_eligible"] = 0
    batch["summary"]["admission_ineligible"] = 3
    batch["summary"]["canonical_records"] = 0
    batch["summary"]["rejection_reasons"] = {"structural_invalid": 3}

    return batch


def test_real_result_sets_assemble_to_six_canonical_records():
    snapshot = assemble_corpus(
        (
            IngestionResultSet(_carrefour_batch()),
            IngestionResultSet(_despar_batch()),
        )
    )

    assert snapshot.summary == {
        "result_set_count": 2,
        "total_outcomes": 6,
        "canonical_records": 6,
        "rejected": 0,
    }
    assert snapshot.result_set_retailers == ("carrefour", "despar")
    assert list_available_retailers(snapshot.canonical_records) == [
        "carrefour",
        "despar",
    ]


def test_input_result_set_and_per_record_order_are_preserved():
    carrefour = IngestionResultSet(_carrefour_batch())
    despar = IngestionResultSet(_despar_batch())

    snapshot = assemble_corpus((despar, carrefour))

    expected = [
        *(record["product_name"] for record in despar.canonical_records),
        *(record["product_name"] for record in carrefour.canonical_records),
    ]

    assert snapshot.result_set_retailers == ("despar", "carrefour")
    assert [record["product_name"] for record in snapshot.canonical_records] == expected


def test_rejected_entries_preserve_retailer_index_and_outcome():
    result_set = IngestionResultSet(_rejected_despar_batch())

    snapshot = assemble_corpus((result_set,))

    assert len(snapshot.canonical_records) == 0
    assert len(snapshot.rejected) == 3

    rejected = snapshot.rejected[0]

    assert rejected.retailer == "despar"
    assert rejected.record_index == 0
    assert rejected.outcome is result_set.rejected[0].outcome
    assert rejected.outcome["canonical"] is None
    assert rejected.outcome["admission"]["reasons"] == [{"code": "structural_invalid"}]
    assert rejected.outcome["source_evidence"]["retailer"] == "despar"


def test_zero_admitted_result_set_is_valid_input():
    snapshot = assemble_corpus((IngestionResultSet(_rejected_despar_batch()),))

    assert snapshot.summary == {
        "result_set_count": 1,
        "total_outcomes": 3,
        "canonical_records": 0,
        "rejected": 3,
    }
    assert snapshot.result_set_retailers == ("despar",)
    assert list_available_retailers(snapshot.canonical_records) == []


def test_canonical_record_top_level_mapping_remains_read_only():
    snapshot = assemble_corpus((IngestionResultSet(_carrefour_batch()),))

    canonical = snapshot.canonical_records[0]

    assert isinstance(canonical, MappingProxyType)

    with pytest.raises(TypeError):
        canonical["product_name"] = "mutated"


def test_snapshot_is_isolated_from_later_raw_batch_mutation():
    batch = _carrefour_batch()
    result_set = IngestionResultSet(batch)
    snapshot = assemble_corpus((result_set,))
    original_name = snapshot.canonical_records[0]["product_name"]

    batch["retailer"] = "mutated"
    batch["records"][0]["canonical"]["product_name"] = "mutated"
    batch["records"][0]["admission"]["eligible"] = False
    batch["summary"]["canonical_records"] = 0

    assert snapshot.result_set_retailers == ("carrefour",)
    assert snapshot.canonical_records[0]["product_name"] == original_name
    assert snapshot.summary["canonical_records"] == 3


def test_aggregate_counts_are_derived_from_observed_result_set_contents():
    snapshot = assemble_corpus(
        (
            IngestionResultSet(_carrefour_batch()),
            IngestionResultSet(_rejected_despar_batch()),
        )
    )

    assert snapshot.summary["result_set_count"] == 2
    assert snapshot.summary["total_outcomes"] == 6
    assert snapshot.summary["canonical_records"] == 3
    assert snapshot.summary["rejected"] == 3
    assert (
        snapshot.summary["canonical_records"] + snapshot.summary["rejected"]
        == snapshot.summary["total_outcomes"]
    )


def test_ai_used_aggregates_with_any_semantics():
    first_batch = _carrefour_batch()
    second_batch = _despar_batch()
    second_batch["ai_used"] = True

    snapshot = assemble_corpus(
        (
            IngestionResultSet(first_batch),
            IngestionResultSet(second_batch),
        )
    )

    assert snapshot.ai_used is True


def test_network_required_aggregates_with_any_semantics():
    first_batch = _carrefour_batch()
    second_batch = _despar_batch()
    second_batch["network_required"] = True

    snapshot = assemble_corpus(
        (
            IngestionResultSet(first_batch),
            IngestionResultSet(second_batch),
        )
    )

    assert snapshot.network_required is True


def test_all_false_operational_metadata_stays_false():
    snapshot = assemble_corpus(
        (
            IngestionResultSet(_carrefour_batch()),
            IngestionResultSet(_despar_batch()),
        )
    )

    assert snapshot.ai_used is False
    assert snapshot.network_required is False


def test_empty_input_returns_explicit_empty_snapshot():
    snapshot = assemble_corpus(())

    assert snapshot.canonical_records == ()
    assert snapshot.rejected == ()
    assert snapshot.result_set_retailers == ()
    assert snapshot.summary == {
        "result_set_count": 0,
        "total_outcomes": 0,
        "canonical_records": 0,
        "rejected": 0,
    }
    assert snapshot.ai_used is False
    assert snapshot.network_required is False


def test_non_iterable_input_fails_explicitly():
    with pytest.raises(
        TypeError,
        match="result_sets must be an iterable of IngestionResultSet values",
    ):
        assemble_corpus(None)


@pytest.mark.parametrize("value", [{}, "not-a-result-set", object()])
def test_non_result_set_member_fails_explicitly(value):
    with pytest.raises(
        TypeError,
        match=r"result_sets\[0\] must be an IngestionResultSet",
    ):
        assemble_corpus((value,))


def test_existing_canonical_consumers_accept_snapshot_records():
    snapshot = assemble_corpus(
        (
            IngestionResultSet(_carrefour_batch()),
            IngestionResultSet(_despar_batch()),
        )
    )

    current = list_current_offers(
        snapshot.canonical_records,
        as_of="2026-08-30",
    )

    assert len(current) == 3
    assert all(record["retailer"] == "carrefour" for record in current)
    assert list_available_retailers(snapshot.canonical_records) == [
        "carrefour",
        "despar",
    ]


def test_duplicate_retailer_result_sets_are_allowed_and_preserved():
    first = IngestionResultSet(_carrefour_batch())
    second = IngestionResultSet(deepcopy(_carrefour_batch()))

    snapshot = assemble_corpus((first, second))

    assert snapshot.result_set_retailers == ("carrefour", "carrefour")
    assert snapshot.summary["result_set_count"] == 2
    assert snapshot.summary["canonical_records"] == 6
    assert list_available_retailers(snapshot.canonical_records) == ["carrefour"]
