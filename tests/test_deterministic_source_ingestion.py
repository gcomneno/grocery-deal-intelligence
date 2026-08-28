from copy import deepcopy
from pathlib import Path

import pytest

from grocery_deal_intelligence.carrefour_adapter import adapt_carrefour_fixture_text
from grocery_deal_intelligence.despar_adapter import adapt_despar_fixture_text
from grocery_deal_intelligence.ingestion import ingest_deterministic_source_record
from grocery_deal_intelligence.source_evidence import (
    CONTRADICTED,
    UNVERIFIABLE,
    summarize_claim_verification,
)


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


def test_carrefour_real_records_are_admitted_deterministically():
    records = _carrefour_records()

    assert len(records) == 3
    for source_record in records:
        result = ingest_deterministic_source_record(
            source_record,
            retailer="carrefour",
        )
        summary = summarize_claim_verification(result["claim_verification"])

        assert result["ai_used"] is False
        assert result["validated"] is True
        assert result["admission"]["eligible"] is True
        assert result["canonical"] == result["candidate"]
        assert summary[CONTRADICTED] == 0
        assert summary[UNVERIFIABLE] == 0


def test_despar_real_records_fail_closed_deterministically():
    records = _despar_records()

    assert len(records) == 3
    for source_record in records:
        result = ingest_deterministic_source_record(
            source_record,
            retailer="despar",
        )
        summary = summarize_claim_verification(result["claim_verification"])

        assert result["ai_used"] is False
        assert result["validated"] is False
        assert result["admission"]["eligible"] is False
        assert result["canonical"] is None
        assert [reason["code"] for reason in result["admission"]["reasons"]] == [
            "structural_invalid"
        ]
        assert summary[CONTRADICTED] == 0
        assert summary[UNVERIFIABLE] == 0


def test_deterministic_source_ingestion_does_not_mutate_caller_input():
    source_record = _carrefour_records()[0]
    before = deepcopy(source_record)

    result = ingest_deterministic_source_record(
        source_record,
        retailer="carrefour",
    )

    assert source_record == before
    assert result["candidate"] is not source_record


@pytest.mark.parametrize("retailer", [None, "", "   "])
def test_deterministic_source_ingestion_requires_non_empty_retailer(retailer):
    with pytest.raises(
        ValueError,
        match="deterministic source ingestion requires a non-empty retailer",
    ):
        ingest_deterministic_source_record({}, retailer=retailer)
