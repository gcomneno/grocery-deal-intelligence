from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class IndexedIngestionOutcome:
    record_index: int
    outcome: Mapping


@dataclass(frozen=True, init=False)
class IngestionResultSet:
    """Read-only projection over an existing deterministic batch result.

    The result set deep-copies the incoming batch result once, then exposes
    tuple-backed collections and read-only top-level mapping boundaries. Nested
    diagnostics, evidence, provenance, and canonical fields are not recursively
    frozen, so recursive immutability is not guaranteed.

    Construction observes only the copied batch snapshot. It does not ingest,
    validate, admit, project evidence, call retailer adapters, invoke AI, use
    the network, rebuild canonical data, or otherwise re-authorize records.
    """

    retailer: str
    outcomes: tuple
    admitted: tuple
    canonical_records: tuple
    rejected: tuple
    summary: Mapping
    ai_used: bool
    network_required: bool

    def __init__(self, batch_result: object) -> None:
        snapshot = deepcopy(batch_result)
        projection = _build_projection(snapshot)

        object.__setattr__(self, "retailer", projection["retailer"])
        object.__setattr__(self, "outcomes", projection["outcomes"])
        object.__setattr__(self, "admitted", projection["admitted"])
        object.__setattr__(
            self,
            "canonical_records",
            projection["canonical_records"],
        )
        object.__setattr__(self, "rejected", projection["rejected"])
        object.__setattr__(self, "summary", projection["summary"])
        object.__setattr__(self, "ai_used", projection["ai_used"])
        object.__setattr__(
            self,
            "network_required",
            projection["network_required"],
        )


def _build_projection(snapshot: object):
    if not isinstance(snapshot, Mapping):
        raise ValueError("batch result must be a mapping")

    retailer = snapshot.get("retailer")
    if not isinstance(retailer, str) or not retailer.strip():
        raise ValueError("batch result retailer must be a non-empty string")

    if "records" not in snapshot or not isinstance(snapshot["records"], list):
        raise ValueError("batch result records must be the ordered batch list")

    records = snapshot["records"]

    summary = snapshot.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("batch result summary must be a mapping")

    outcomes = []
    admitted = []
    rejected = []
    canonical_records = []

    for record_index, outcome in enumerate(records):
        _validate_outcome(outcome, record_index)

        canonical_proxy = None
        if outcome["admission"]["eligible"] is True:
            canonical_proxy = MappingProxyType(outcome["canonical"])
            outcome["canonical"] = canonical_proxy

        outcome_proxy = MappingProxyType(outcome)
        entry = IndexedIngestionOutcome(
            record_index=record_index,
            outcome=outcome_proxy,
        )

        outcomes.append(outcome_proxy)
        if canonical_proxy is not None:
            admitted.append(entry)
            canonical_records.append(canonical_proxy)
        else:
            rejected.append(entry)

    _validate_summary(
        summary=summary,
        total_outcomes=len(outcomes),
        admitted_count=len(admitted),
        rejected_count=len(rejected),
        canonical_count=len(canonical_records),
    )
    ai_used = _required_bool(snapshot, "ai_used")
    network_required = _required_bool(snapshot, "network_required")

    return {
        "retailer": retailer,
        "outcomes": tuple(outcomes),
        "admitted": tuple(admitted),
        "canonical_records": tuple(canonical_records),
        "rejected": tuple(rejected),
        "summary": MappingProxyType(summary),
        "ai_used": ai_used,
        "network_required": network_required,
    }


def _validate_outcome(outcome: object, record_index: int):
    if not isinstance(outcome, Mapping):
        raise ValueError(
            f"batch outcome at record_index {record_index} must be a mapping"
        )

    admission = outcome.get("admission")
    if not isinstance(admission, Mapping):
        raise ValueError(
            f"batch outcome at record_index {record_index} admission must be a mapping"
        )

    if "eligible" not in admission:
        raise ValueError(
            f"batch outcome at record_index {record_index} admission.eligible is required"
        )

    eligible = admission["eligible"]
    if eligible is not True and eligible is not False:
        raise ValueError(
            f"batch outcome at record_index {record_index} admission.eligible must be an actual boolean"
        )

    canonical = outcome.get("canonical")
    if eligible is True:
        if not isinstance(canonical, Mapping):
            raise ValueError(
                f"eligible outcome at record_index {record_index} requires a non-null canonical mapping"
            )
    elif canonical is not None:
        raise ValueError(
            f"ineligible outcome at record_index {record_index} requires canonical to be None"
        )


def _validate_summary(
    *,
    summary: Mapping[str, Any],
    total_outcomes: int,
    admitted_count: int,
    rejected_count: int,
    canonical_count: int,
):
    _require_summary_count(summary, "total_records", total_outcomes)
    _require_summary_count(summary, "admission_eligible", admitted_count)
    _require_summary_count(summary, "admission_ineligible", rejected_count)
    _require_summary_count(summary, "canonical_records", canonical_count)

    if "structurally_valid" in summary or "structurally_invalid" in summary:
        if "structurally_valid" not in summary:
            raise ValueError("summary.structurally_valid is required")
        if "structurally_invalid" not in summary:
            raise ValueError("summary.structurally_invalid is required")

        structurally_valid = _summary_int(summary, "structurally_valid")
        structurally_invalid = _summary_int(summary, "structurally_invalid")
        if structurally_valid + structurally_invalid != total_outcomes:
            raise ValueError("summary structural counts must match observed outcomes")


def _require_summary_count(summary: Mapping[str, Any], key: str, expected: int):
    actual = _summary_int(summary, key)
    if actual != expected:
        raise ValueError(f"summary.{key} does not match observed outcomes")


def _summary_int(summary: Mapping[str, Any], key: str):
    if key not in summary:
        raise ValueError(f"summary.{key} is required")

    value = summary[key]
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"summary.{key} must be a non-negative integer count")

    return value


def _required_bool(snapshot: Mapping[str, Any], key: str):
    if key not in snapshot:
        raise ValueError(f"batch result {key} is required")

    value = snapshot[key]
    if value is not True and value is not False:
        raise ValueError(f"batch result {key} must be an actual boolean")

    return value
