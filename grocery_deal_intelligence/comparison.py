from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .source_evidence import CONTRADICTED, SUPPORTED, UNVERIFIABLE


ROOT = Path(__file__).resolve().parent.parent
COMPARISON_PROPOSAL_SCHEMA_PATH = (
    ROOT / "schema/product-comparison-proposal-v0.1.schema.json"
)

SAME_PRODUCT = "same_product"
COMPARABLE = "comparable"
UNKNOWN = "unknown"

_RELATIONSHIPS = frozenset({SAME_PRODUCT, COMPARABLE, UNKNOWN})

INVALID_PROPOSAL = "invalid_proposal"
NO_COMPARISON_CLAIMS = "no_comparison_claims"
COMPARISON_CLAIM_UNSUPPORTED = "comparison_claim_unsupported"
RELATIONSHIP_POLICY_UNAVAILABLE = "relationship_evidence_policy_unavailable"
VERIFICATION_PROPOSAL_MISMATCH = "verification_proposal_mismatch"


def _load_comparison_proposal_schema() -> dict[str, Any]:
    return json.loads(COMPARISON_PROPOSAL_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_comparison_proposal(proposal: Mapping[str, Any]) -> dict[str, Any]:
    """Validate advisory comparison shape without granting comparison authority."""
    if not isinstance(proposal, Mapping):
        raise TypeError("proposal must be a mapping")

    proposal_copy = deepcopy(dict(proposal))
    validator = Draft202012Validator(_load_comparison_proposal_schema())
    errors = sorted(
        validator.iter_errors(proposal_copy),
        key=lambda error: (
            list(error.absolute_path),
            error.validator,
            error.message,
        ),
    )

    return {
        "valid": not errors,
        "errors": [
            {
                "path": list(error.absolute_path),
                "message": error.message,
            }
            for error in errors
        ],
    }


def verify_comparison_claims(
    proposal: Mapping[str, Any],
    left_offer: Mapping[str, Any],
    right_offer: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Verify proposed facts independently against the two canonical inputs.

    A supported result means only that the proposal represented an observed
    canonical fact correctly. It does not prove that the fact is sufficient to
    authorize the proposed product relationship.
    """
    if not isinstance(proposal, Mapping):
        raise TypeError("proposal must be a mapping")
    if not isinstance(left_offer, Mapping):
        raise TypeError("left_offer must be a mapping")
    if not isinstance(right_offer, Mapping):
        raise TypeError("right_offer must be a mapping")

    proposal_copy = deepcopy(dict(proposal))
    left_copy = deepcopy(dict(left_offer))
    right_copy = deepcopy(dict(right_offer))

    claims = proposal_copy.get("claims")
    if not isinstance(claims, list):
        raise ValueError("proposal.claims must be a list")

    results: list[dict[str, Any]] = []
    seen_paths: set[tuple[str, ...]] = set()

    for index, claim in enumerate(claims):
        if not isinstance(claim, Mapping):
            raise ValueError(f"proposal.claims[{index}] must be a mapping")

        raw_path = claim.get("path")
        if (
            not isinstance(raw_path, list)
            or not raw_path
            or not all(isinstance(part, str) and part for part in raw_path)
        ):
            raise ValueError(
                f"proposal.claims[{index}].path must be a non-empty list of strings"
            )

        if "left_value" not in claim or "right_value" not in claim:
            raise ValueError(
                f"proposal.claims[{index}] must contain left_value and right_value"
            )

        path = tuple(raw_path)
        if path in seen_paths:
            raise ValueError(f"duplicate comparison claim path: {list(path)!r}")
        seen_paths.add(path)

        left_found, left_evidence = _get_path(left_copy, path)
        right_found, right_evidence = _get_path(right_copy, path)

        results.append(
            {
                "path": list(path),
                "left": _verify_side(
                    proposed=claim["left_value"],
                    found=left_found,
                    evidence=left_evidence,
                ),
                "right": _verify_side(
                    proposed=claim["right_value"],
                    found=right_found,
                    evidence=right_evidence,
                ),
            }
        )

    return sorted(results, key=lambda item: tuple(item["path"]))


def evaluate_comparison_admission(
    proposal: Mapping[str, Any],
    verification: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate downstream relationship authority conservatively.

    Bilateral claim support proves that the proposal copied observed facts
    correctly. It does not prove that those facts are semantically sufficient
    for `same_product` or `comparable`.

    Until a deterministic relationship-evidence policy exists, stronger
    relationships therefore fail closed to `unknown`.
    """
    if not isinstance(proposal, Mapping):
        raise TypeError("proposal must be a mapping")
    if not isinstance(verification, list):
        raise TypeError("verification must be a list")

    proposal_copy = deepcopy(dict(proposal))
    verification_copy = deepcopy(verification)

    validation = validate_comparison_proposal(proposal_copy)
    if not validation["valid"]:
        return {
            "relationship": UNKNOWN,
            "eligible": False,
            "reasons": [
                {
                    "code": INVALID_PROPOSAL,
                    "errors": validation["errors"],
                }
            ],
        }

    proposed_relationship = proposal_copy["relationship"]

    if proposed_relationship not in _RELATIONSHIPS:
        return {
            "relationship": UNKNOWN,
            "eligible": False,
            "reasons": [{"code": INVALID_PROPOSAL}],
        }

    proposal_paths = _proposal_claim_paths(proposal_copy)
    verification_paths = _verification_claim_paths(verification_copy)

    if proposal_paths != verification_paths:
        return {
            "relationship": UNKNOWN,
            "eligible": False,
            "reasons": [
                {
                    "code": VERIFICATION_PROPOSAL_MISMATCH,
                    "missing_paths": [
                        list(path)
                        for path in sorted(proposal_paths - verification_paths)
                    ],
                    "extra_paths": [
                        list(path)
                        for path in sorted(verification_paths - proposal_paths)
                    ],
                }
            ],
        }

    if proposed_relationship == UNKNOWN:
        return {
            "relationship": UNKNOWN,
            "eligible": True,
            "reasons": [],
        }

    if not verification_copy:
        return {
            "relationship": UNKNOWN,
            "eligible": False,
            "reasons": [{"code": NO_COMPARISON_CLAIMS}],
        }

    reasons: list[dict[str, Any]] = []

    for item in verification_copy:
        if not isinstance(item, Mapping):
            raise TypeError("verification entries must be mappings")

        raw_path = item.get("path")
        if (
            not isinstance(raw_path, list)
            or not raw_path
            or not all(isinstance(part, str) and part for part in raw_path)
        ):
            raise ValueError(
                "verification path must be a non-empty list of strings"
            )

        left = item.get("left")
        right = item.get("right")
        if not isinstance(left, Mapping) or not isinstance(right, Mapping):
            raise ValueError(
                "verification entries must contain left and right mappings"
            )

        left_status = left.get("status")
        right_status = right.get("status")

        for status in (left_status, right_status):
            if status not in {SUPPORTED, CONTRADICTED, UNVERIFIABLE}:
                raise ValueError(f"unknown verification status: {status!r}")

        if left_status == SUPPORTED and right_status == SUPPORTED:
            continue

        reasons.append(
            {
                "code": COMPARISON_CLAIM_UNSUPPORTED,
                "path": list(raw_path),
                "left_status": left_status,
                "right_status": right_status,
            }
        )

    if reasons:
        reasons.sort(
            key=lambda reason: (
                tuple(reason.get("path", [])),
                reason["code"],
            )
        )
        return {
            "relationship": UNKNOWN,
            "eligible": False,
            "reasons": reasons,
        }

    return {
        "relationship": UNKNOWN,
        "eligible": False,
        "reasons": [
            {
                "code": RELATIONSHIP_POLICY_UNAVAILABLE,
                "proposed_relationship": proposed_relationship,
            }
        ],
    }


def compare_admitted_offers(
    left_offer: Mapping[str, Any],
    right_offer: Mapping[str, Any],
    proposal: Mapping[str, Any],
) -> dict[str, Any]:
    """Compose comparison verification and admission for canonical inputs.

    The caller supplies already-admitted canonical offers. Canonical admission
    remains owned by the existing ingestion boundary and is neither re-run nor
    duplicated here.
    """
    if not isinstance(left_offer, Mapping):
        raise TypeError("left_offer must be a mapping")
    if not isinstance(right_offer, Mapping):
        raise TypeError("right_offer must be a mapping")
    if not isinstance(proposal, Mapping):
        raise TypeError("proposal must be a mapping")

    left_copy = deepcopy(dict(left_offer))
    right_copy = deepcopy(dict(right_offer))
    proposal_copy = deepcopy(dict(proposal))

    validation = validate_comparison_proposal(proposal_copy)
    if not validation["valid"]:
        return {
            "proposal": proposal_copy,
            "verification": [],
            "admission": {
                "relationship": UNKNOWN,
                "eligible": False,
                "reasons": [
                    {
                        "code": INVALID_PROPOSAL,
                        "errors": validation["errors"],
                    }
                ],
            },
        }

    verification = verify_comparison_claims(
        proposal_copy,
        left_copy,
        right_copy,
    )
    admission = evaluate_comparison_admission(proposal_copy, verification)

    return {
        "proposal": proposal_copy,
        "verification": verification,
        "admission": admission,
    }


def _proposal_claim_paths(
    proposal: Mapping[str, Any],
) -> set[tuple[str, ...]]:
    claims = proposal.get("claims")
    if not isinstance(claims, list):
        raise ValueError("proposal.claims must be a list")

    paths: set[tuple[str, ...]] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, Mapping):
            raise ValueError(f"proposal.claims[{index}] must be a mapping")

        raw_path = claim.get("path")
        if (
            not isinstance(raw_path, list)
            or not raw_path
            or not all(isinstance(part, str) and part for part in raw_path)
        ):
            raise ValueError(
                f"proposal.claims[{index}].path must be a non-empty list of strings"
            )

        path = tuple(raw_path)
        if path in paths:
            raise ValueError(f"duplicate comparison claim path: {list(path)!r}")
        paths.add(path)

    return paths


def _verification_claim_paths(
    verification: list[Mapping[str, Any]],
) -> set[tuple[str, ...]]:
    paths: set[tuple[str, ...]] = set()

    for index, item in enumerate(verification):
        if not isinstance(item, Mapping):
            raise TypeError("verification entries must be mappings")

        raw_path = item.get("path")
        if (
            not isinstance(raw_path, list)
            or not raw_path
            or not all(isinstance(part, str) and part for part in raw_path)
        ):
            raise ValueError(
                f"verification[{index}].path must be a non-empty list of strings"
            )

        path = tuple(raw_path)
        if path in paths:
            raise ValueError(f"duplicate verification claim path: {list(path)!r}")
        paths.add(path)

    return paths


def _verify_side(*, proposed: Any, found: bool, evidence: Any) -> dict[str, Any]:
    result = {"proposed_value": deepcopy(proposed)}

    if not found:
        result["status"] = UNVERIFIABLE
        return result

    result["evidence_value"] = deepcopy(evidence)
    result["status"] = SUPPORTED if proposed == evidence else CONTRADICTED
    return result


def _get_path(
    value: Mapping[str, Any],
    path: tuple[str, ...],
) -> tuple[bool, Any]:
    current: Any = value

    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]

    return True, deepcopy(current)
