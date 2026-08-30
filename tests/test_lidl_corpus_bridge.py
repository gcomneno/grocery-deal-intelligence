"""Contract tests for the pinned Lidl canonical corpus bridge."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from grocery_deal_intelligence.ingestion import ingest_deterministic_source_records
from grocery_deal_intelligence.ingestion_result_set import IngestionResultSet
from grocery_deal_intelligence.lidl_fixture import (
    LIDL_LUCCA_CURRENT_FIXTURE_SHA256,
    load_lidl_fixture,
)
from grocery_deal_intelligence.road_test import run_road_test

if TYPE_CHECKING:
    import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LIDL_FIXTURE = _REPO_ROOT / "lidl/data/output/lidl-lucca-current.json"
_LEGACY_NEUTRAL_EXPORT = (
    _REPO_ROOT / "lidl/data/output/lidl-lucca-current-retailer-neutral.json"
)

_EXPECTED_RECORDS = 58
_EXPECTED_SUPPORTED_CLAIMS = 1218


def _lidl_result_set() -> IngestionResultSet:
    records = load_lidl_fixture(
        _LIDL_FIXTURE,
        expected_sha256=LIDL_LUCCA_CURRENT_FIXTURE_SHA256,
    )
    batch = ingest_deterministic_source_records(records, retailer="lidl")
    return IngestionResultSet(batch)


def test_pinned_lidl_fixture_reproduces_canonical_admission_contract() -> None:
    """The pinned source-shaped fixture must reproduce reviewed 58/58 behavior."""
    result_set = _lidl_result_set()

    assert len(result_set.outcomes) == _EXPECTED_RECORDS
    assert len(result_set.canonical_records) == _EXPECTED_RECORDS
    assert result_set.rejected == ()

    assert result_set.summary["total_records"] == _EXPECTED_RECORDS
    assert result_set.summary["structurally_valid"] == _EXPECTED_RECORDS
    assert result_set.summary["admission_eligible"] == _EXPECTED_RECORDS
    assert result_set.summary["canonical_records"] == _EXPECTED_RECORDS
    assert result_set.summary["claims"]["supported"] == _EXPECTED_SUPPORTED_CLAIMS
    assert result_set.summary["claims"]["contradicted"] == 0
    assert result_set.summary["claims"]["unverifiable"] == 0

    assert result_set.ai_used is False
    assert result_set.network_required is False


def test_all_admitted_lidl_records_preserve_verified_store_locality() -> None:
    """Pinned Lidl evidence must retain current store-scoped locality semantics."""
    result_set = _lidl_result_set()

    for record in result_set.canonical_records:
        locality = record["locality"]

        assert locality["scope"] == "store"
        assert isinstance(locality["stores"], list)
        assert locality["stores"]
        assert all(
            isinstance(store_id, str) and store_id for store_id in locality["stores"]
        )


def test_canonical_road_test_never_reads_legacy_neutral_export(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The historical retailer-neutral Lidl export is not canonical authority."""
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text

    def guarded_read_bytes(path: Path) -> bytes:
        if path.resolve() == _LEGACY_NEUTRAL_EXPORT.resolve():
            raise AssertionError("legacy Lidl neutral export must not be read")
        return original_read_bytes(path)

    def guarded_read_text(path: Path, *args: object, **kwargs: object) -> str:
        if path.resolve() == _LEGACY_NEUTRAL_EXPORT.resolve():
            raise AssertionError("legacy Lidl neutral export must not be read")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    result = run_road_test()

    assert result["pass"] is True
    assert result["corpus"]["canonical_records"] == 64
    assert result["corpus"]["represented_retailers"] == [
        "carrefour",
        "despar",
        "lidl",
    ]

    by_retailer = {item["retailer"]: item for item in result["retailers"]}
    assert by_retailer["lidl"]["fixture"] == (
        "lidl/data/output/lidl-lucca-current.json"
    )
