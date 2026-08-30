from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from grocery_deal_intelligence.ingestion_result_set import IngestionResultSet


@dataclass(frozen=True)
class CorpusRejectedEntry:
    """Rejected ingestion outcome with corpus-level retailer identity."""

    retailer: str
    record_index: int
    outcome: Mapping[str, Any]


@dataclass(frozen=True)
class CorpusSnapshot:
    """Read-only corpus assembled from existing deterministic result sets.

    The snapshot performs no ingestion, verification, validation, admission,
    repair, deduplication, ranking, or normalization.

    Canonical mappings are the same top-level read-only mappings exposed by the
    input ``IngestionResultSet`` values. Nested values are not recursively
    frozen.
    """

    canonical_records: tuple[Mapping[str, Any], ...]
    rejected: tuple[CorpusRejectedEntry, ...]
    result_set_retailers: tuple[str, ...]
    summary: Mapping[str, int]
    ai_used: bool
    network_required: bool


def assemble_corpus(
    result_sets: Iterable[IngestionResultSet],
) -> CorpusSnapshot:
    """Assemble already-authorized deterministic result sets into one corpus."""
    materialized = _materialize_result_sets(result_sets)

    canonical_records: list[Mapping[str, Any]] = []
    rejected: list[CorpusRejectedEntry] = []
    result_set_retailers: list[str] = []
    total_outcomes = 0

    for result_set in materialized:
        result_set_retailers.append(result_set.retailer)
        total_outcomes += len(result_set.outcomes)
        canonical_records.extend(result_set.canonical_records)
        rejected.extend(
            CorpusRejectedEntry(
                retailer=result_set.retailer,
                record_index=entry.record_index,
                outcome=entry.outcome,
            )
            for entry in result_set.rejected
        )

    summary = {
        "result_set_count": len(materialized),
        "total_outcomes": total_outcomes,
        "canonical_records": len(canonical_records),
        "rejected": len(rejected),
    }

    if summary["canonical_records"] + summary["rejected"] != total_outcomes:
        raise RuntimeError("assembled corpus counts must match observed outcomes")

    return CorpusSnapshot(
        canonical_records=tuple(canonical_records),
        rejected=tuple(rejected),
        result_set_retailers=tuple(result_set_retailers),
        summary=MappingProxyType(summary),
        ai_used=any(result_set.ai_used for result_set in materialized),
        network_required=any(
            result_set.network_required for result_set in materialized
        ),
    )


def _materialize_result_sets(
    result_sets: Iterable[IngestionResultSet],
) -> tuple[IngestionResultSet, ...]:
    try:
        iterator = iter(result_sets)
    except TypeError as exc:
        raise TypeError(
            "result_sets must be an iterable of IngestionResultSet values"
        ) from exc

    materialized = []

    for index, result_set in enumerate(iterator):
        if not isinstance(result_set, IngestionResultSet):
            raise TypeError(f"result_sets[{index}] must be an IngestionResultSet")
        materialized.append(result_set)

    return tuple(materialized)
