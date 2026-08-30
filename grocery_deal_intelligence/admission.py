from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from grocery_deal_intelligence.source_evidence import (
    CONTRADICTED,
    SUPPORTED,
    UNVERIFIABLE,
)

STRUCTURAL_INVALID = "structural_invalid"
CONTRADICTED_CLAIM = "contradicted_claim"
CRITICAL_CLAIM_UNSUPPORTED = "critical_claim_unsupported"

CRITICAL_CLAIM_PATHS: tuple[tuple[str, ...], ...] = (
    ("price",),
    ("product_name",),
    ("retailer",),
    ("validity", "from"),
    ("validity", "to"),
)


def evaluate_canonical_admission(
    *,
    structurally_valid: bool,
    claim_verification: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate deterministic canonical admission from structural and source-support evidence."""
    if not isinstance(structurally_valid, bool):
        raise TypeError("structurally_valid must be a bool")
    if not isinstance(claim_verification, Sequence) or isinstance(
        claim_verification, (str, bytes, bytearray)
    ):
        raise TypeError("claim_verification must be a sequence of mappings")

    claims = deepcopy(list(claim_verification))
    by_path: dict[tuple[str, ...], Mapping[str, Any]] = {}

    for index, claim in enumerate(claims):
        if not isinstance(claim, Mapping):
            raise TypeError(f"claim_verification[{index}] must be a mapping")

        raw_path = claim.get("path")
        if not isinstance(raw_path, list) or not all(
            isinstance(part, str) for part in raw_path
        ):
            raise ValueError(
                f"claim_verification[{index}].path must be a list of strings"
            )
        path = tuple(raw_path)
        if path in by_path:
            raise ValueError(f"duplicate claim path: {list(path)!r}")

        status = claim.get("status")
        if status not in {SUPPORTED, CONTRADICTED, UNVERIFIABLE}:
            raise ValueError(f"unknown claim verification status: {status!r}")
        by_path[path] = claim

    reasons: list[dict[str, Any]] = []

    if not structurally_valid:
        reasons.append({"code": STRUCTURAL_INVALID})

    contradicted_paths = sorted(
        path for path, claim in by_path.items() if claim["status"] == CONTRADICTED
    )
    reasons.extend(
        {"code": CONTRADICTED_CLAIM, "path": list(path)} for path in contradicted_paths
    )

    critical_claims: list[dict[str, Any]] = []
    for path in CRITICAL_CLAIM_PATHS:
        claim = by_path.get(path)
        status = claim["status"] if claim is not None else UNVERIFIABLE
        critical_claims.append({"path": list(path), "status": status})

        if status == CONTRADICTED:
            continue
        if status != SUPPORTED:
            reasons.append({"code": CRITICAL_CLAIM_UNSUPPORTED, "path": list(path)})

    reasons.sort(key=_reason_sort_key)

    return {
        "eligible": not reasons,
        "reasons": reasons,
        "critical_claims": critical_claims,
    }


def _reason_sort_key(reason: Mapping[str, Any]) -> tuple[int, tuple[str, ...]]:
    order = {
        STRUCTURAL_INVALID: 0,
        CONTRADICTED_CLAIM: 1,
        CRITICAL_CLAIM_UNSUPPORTED: 2,
    }
    code = reason["code"]
    path = tuple(reason.get("path", []))
    return order[code], path
