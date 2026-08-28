from copy import deepcopy
from pathlib import Path

import pytest

import grocery_deal_intelligence.ingestion as ingestion
import grocery_deal_intelligence.road_test as road_test
from grocery_deal_intelligence.carrefour_adapter import adapt_carrefour_fixture_text
from grocery_deal_intelligence.despar_adapter import adapt_despar_fixture_text
from grocery_deal_intelligence.source_evidence import CONTRADICTED, SUPPORTED, UNVERIFIABLE


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


def test_carrefour_batch_is_fully_admitted():
    result = ingestion.ingest_deterministic_source_records(
        _carrefour_records(),
        retailer="carrefour",
    )
    summary = result["summary"]

    assert summary["total_records"] == 3
    assert summary["structurally_valid"] == 3
    assert summary["structurally_invalid"] == 0
    assert summary["admission_eligible"] == 3
    assert summary["admission_ineligible"] == 0
    assert summary["canonical_records"] == 3
    assert summary["rejection_reasons"] == {}
    assert summary["claims"][SUPPORTED] > 0
    assert summary["claims"][CONTRADICTED] == 0
    assert summary["claims"][UNVERIFIABLE] == 0
    assert all(record["canonical"] is not None for record in result["records"])
    assert result["ai_used"] is False
    assert result["network_required"] is False


def test_despar_batch_fails_closed_without_dropping_records():
    result = ingestion.ingest_deterministic_source_records(
        _despar_records(),
        retailer="despar",
    )
    summary = result["summary"]

    assert summary["total_records"] == 3
    assert summary["structurally_valid"] == 0
    assert summary["structurally_invalid"] == 3
    assert summary["admission_eligible"] == 0
    assert summary["admission_ineligible"] == 3
    assert summary["canonical_records"] == 0
    assert summary["rejection_reasons"] == {"structural_invalid": 3}
    assert summary["claims"][SUPPORTED] > 0
    assert summary["claims"][CONTRADICTED] == 0
    assert summary["claims"][UNVERIFIABLE] == 0
    assert len(result["records"]) == 3
    assert all(record["canonical"] is None for record in result["records"])


def test_batch_preserves_input_order_and_does_not_mutate_records():
    records = _carrefour_records()
    before = deepcopy(records)

    result = ingestion.ingest_deterministic_source_records(
        records,
        retailer="carrefour",
    )

    assert records == before
    assert [record["candidate"]["product_name"] for record in result["records"]] == [
        record["product_name"] for record in before
    ]


@pytest.mark.parametrize("retailer", [None, "", "   "])
def test_batch_requires_non_empty_retailer(retailer):
    with pytest.raises(
        ValueError,
        match="deterministic source ingestion requires a non-empty retailer",
    ):
        ingestion.ingest_deterministic_source_records([], retailer=retailer)


def test_batch_delegates_each_record_to_single_record_ingestion(monkeypatch):
    records = _carrefour_records()
    calls = []
    real_single = ingestion.ingest_deterministic_source_record

    def recording_single(source_record, *, retailer):
        calls.append((source_record["product_name"], retailer))
        return real_single(source_record, retailer=retailer)

    monkeypatch.setattr(
        ingestion,
        "ingest_deterministic_source_record",
        recording_single,
    )

    result = ingestion.ingest_deterministic_source_records(
        records,
        retailer="carrefour",
    )

    assert result["summary"]["total_records"] == 3
    assert calls == [(record["product_name"], "carrefour") for record in records]


def test_road_test_uses_shared_batch_ingestion(monkeypatch):
    calls = []
    real_batch = road_test.ingest_deterministic_source_records

    def recording_batch(source_records, *, retailer):
        records = list(source_records)
        calls.append((retailer, len(records)))
        return real_batch(records, retailer=retailer)

    monkeypatch.setattr(
        road_test,
        "ingest_deterministic_source_records",
        recording_batch,
    )

    result = road_test.run_road_test()

    assert result["pass"] is True
    assert result["unsupported_facts_invented"] == 0
    assert calls == [("carrefour", 3), ("despar", 3)]
