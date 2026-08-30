from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from .source_evidence import CONTRADICTED, SUPPORTED, UNVERIFIABLE
from .validation import _load_schema

_USABLE_STATUS = SUPPORTED
_REJECTED_STATUSES = frozenset({CONTRADICTED, UNVERIFIABLE})


def project_proposal_to_canonical(
    proposal: Mapping[str, Any],
    claim_verification: Sequence[Mapping[str, Any]],
    source_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Compose a canonical candidate only from supported proposal claims and evidence.

    Projection is deterministic composition plus completeness checking. It does not
    perform canonical structural validation and never fabricates missing facts.
    """
    if not isinstance(proposal, Mapping):
        raise TypeError("proposal must be a mapping")
    if not isinstance(source_evidence, Mapping):
        raise TypeError("source_evidence must be a mapping")
    if not isinstance(claim_verification, Sequence) or isinstance(
        claim_verification, (str, bytes, bytearray)
    ):
        raise TypeError("claim_verification must be a sequence")

    proposal_copy = deepcopy(dict(proposal))
    evidence_copy = deepcopy(dict(source_evidence))
    verification_copy = deepcopy(list(claim_verification))
    schema = _load_schema()

    verification_by_path: dict[tuple[str, ...], Mapping[str, Any]] = {}
    rejected_claims: list[dict[str, Any]] = []

    for item in verification_copy:
        if not isinstance(item, Mapping):
            raise TypeError("claim verification entries must be mappings")
        raw_path = item.get("path")
        if not isinstance(raw_path, list) or not all(
            isinstance(part, str) for part in raw_path
        ):
            raise ValueError("claim verification path must be a list of strings")
        path = tuple(raw_path)
        status = item.get("status")
        if status not in {SUPPORTED, CONTRADICTED, UNVERIFIABLE}:
            raise ValueError(f"unknown claim verification status: {status!r}")
        verification_by_path[path] = item
        if status in _REJECTED_STATUSES:
            rejected_claims.append(
                {
                    "path": list(path),
                    "status": status,
                    "candidate_value": deepcopy(item.get("candidate_value")),
                }
            )

    candidate: dict[str, Any] = {}

    for path, value in sorted(_leaf_items(evidence_copy), key=lambda item: item[0]):
        if _path_allowed_by_schema(path, schema):
            _set_path(candidate, path, deepcopy(value))

    for path, value in sorted(_leaf_items(proposal_copy), key=lambda item: item[0]):
        verification = verification_by_path.get(path)
        if verification is None:
            continue
        if verification.get("status") != _USABLE_STATUS:
            continue
        if not _path_allowed_by_schema(path, schema):
            continue
        _set_path(candidate, path, deepcopy(value))

    missing_required_claims = _missing_required_paths(candidate, schema)
    projectable = not missing_required_claims

    return {
        "projectable": projectable,
        "candidate": deepcopy(candidate) if projectable else None,
        "missing_required_claims": [list(path) for path in missing_required_claims],
        "rejected_claims": sorted(
            rejected_claims,
            key=lambda item: (tuple(item["path"]), item["status"]),
        ),
    }


def _leaf_items(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, Mapping):
        for key in sorted(value):
            yield from _leaf_items(value[key], (*path, str(key)))
        return
    yield path, value


def _set_path(target: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    if not path:
        return
    current = target
    for part in path[:-1]:
        existing = current.get(part)
        if not isinstance(existing, dict):
            existing = {}
            current[part] = existing
        current = existing
    current[path[-1]] = value


def _path_allowed_by_schema(path: tuple[str, ...], schema: Mapping[str, Any]) -> bool:
    if not path:
        return False
    current_schema: Mapping[str, Any] = schema
    for part in path:
        properties = current_schema.get("properties")
        if isinstance(properties, Mapping) and part in properties:
            child = properties[part]
            if not isinstance(child, Mapping):
                return False
            current_schema = child
            continue
        additional = current_schema.get("additionalProperties", True)
        return additional is not False
    return True


def _missing_required_paths(
    candidate: Mapping[str, Any],
    schema: Mapping[str, Any],
    path: tuple[str, ...] = (),
) -> list[tuple[str, ...]]:
    missing: list[tuple[str, ...]] = []
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    if not isinstance(required, list) or not isinstance(properties, Mapping):
        return missing

    for key in sorted(required):
        required_path = (*path, str(key))
        child_schema = properties.get(key)

        if key not in candidate:
            if (
                isinstance(child_schema, Mapping)
                and child_schema.get("type") == "object"
            ):
                nested_missing = _missing_required_paths(
                    {}, child_schema, path=required_path
                )
                missing.extend(nested_missing or [required_path])
            else:
                missing.append(required_path)
            continue

        child_value = candidate[key]
        if isinstance(child_schema, Mapping) and child_schema.get("type") == "object":
            if isinstance(child_value, Mapping):
                missing.extend(
                    _missing_required_paths(
                        child_value, child_schema, path=required_path
                    )
                )
            else:
                missing.append(required_path)

    return sorted(set(missing))
