"""Pinned deterministic Lidl fixture loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from string import hexdigits
from typing import Any

LIDL_LUCCA_CURRENT_FIXTURE_SHA256 = (
    "a74d6ffa880b46513f90cbe22b1dccd3a99a21ed80f84680808ea4cb363500df"
)

_SHA256_HEX_LENGTH = 64


def load_lidl_fixture(
    path: str | Path,
    *,
    expected_sha256: str,
) -> list[dict[str, Any]]:
    """Load source-shaped Lidl records after verifying full-file identity."""
    if not isinstance(path, (str, Path)):
        raise TypeError("path must be a string or Path")

    if (
        not isinstance(expected_sha256, str)
        or len(expected_sha256) != _SHA256_HEX_LENGTH
        or any(character not in hexdigits for character in expected_sha256)
    ):
        raise ValueError("expected_sha256 must be a 64-character SHA-256 hex digest")

    payload = Path(path).read_bytes()
    actual_sha256 = hashlib.sha256(payload).hexdigest()

    if actual_sha256 != expected_sha256.lower():
        raise ValueError("Lidl fixture SHA-256 mismatch")

    parsed = json.loads(payload.decode("utf-8"))

    if not isinstance(parsed, list):
        raise ValueError("Lidl fixture must contain a top-level JSON list")

    for index, record in enumerate(parsed):
        if not isinstance(record, dict):
            raise ValueError(
                f"Lidl fixture record at index {index} must be a JSON object"
            )

    return parsed
