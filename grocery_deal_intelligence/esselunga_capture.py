"""Evidence-preserving Esselunga capture contract.

A capture manifest records acquisition facts that were preserved at capture
time. Verification checks those recorded facts against the exact captured bytes.

This module does not reconstruct historical provenance and does not authorize
canonical admission.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

_CAPTURE_VERSION = 1
_SOURCE_TYPE = "retailer_api"
_SHA256_HEX_LENGTH = 64

_DIGITAL_GRID_CONTEXT_PATTERN = re.compile(
    r"\.abbrev:(?P<store>[A-Za-z0-9_-]+)"
    r"\.page:[0-9]+"
    r"\.rows:[0-9]+"
    r"\.codPromo:(?P<campaign>[A-Za-z0-9_-]+)"
    r"\.json$"
)

_REQUIRED_MANIFEST_FIELDS = {
    "version",
    "request_url",
    "source_type",
    "observed_at",
    "response_body_sha256",
    "response_headers_sha256",
    "store_code",
    "campaign_id",
}


@dataclass(frozen=True)
class EsselungaCaptureEvidence:
    """Deterministically verified facts from one preserved acquisition capture."""

    manifest_sha256: str
    request_url: str
    source_type: str
    observed_at: str
    response_body_sha256: str
    response_headers_sha256: str | None
    store_code: str
    campaign_id: str
    request_context_verified: bool


def verify_esselunga_capture(
    *,
    manifest_capture: bytes,
    response_body: bytes,
    response_headers: bytes | None = None,
) -> EsselungaCaptureEvidence:
    """Verify one Esselunga capture manifest against exact captured bytes."""
    if not isinstance(manifest_capture, bytes):
        raise TypeError("manifest_capture must be bytes")
    if not isinstance(response_body, bytes):
        raise TypeError("response_body must be bytes")
    if response_headers is not None and not isinstance(response_headers, bytes):
        raise TypeError("response_headers must be bytes or None")

    manifest = _load_manifest(manifest_capture)

    version = manifest["version"]
    request_url = manifest["request_url"]
    source_type = manifest["source_type"]
    observed_at = manifest["observed_at"]
    expected_body_sha256 = manifest["response_body_sha256"]
    expected_headers_sha256 = manifest["response_headers_sha256"]
    store_code = manifest["store_code"]
    campaign_id = manifest["campaign_id"]

    if version != _CAPTURE_VERSION:
        raise ValueError(f"unsupported capture manifest version: {version!r}")

    request_url = _require_nonempty_string(request_url, field="request_url")
    source_type = _require_nonempty_string(source_type, field="source_type")
    observed_at = _require_nonempty_string(observed_at, field="observed_at")
    expected_body_sha256 = _require_sha256(
        expected_body_sha256,
        field="response_body_sha256",
    )
    store_code = _require_nonempty_string(store_code, field="store_code").upper()
    campaign_id = _require_nonempty_string(campaign_id, field="campaign_id")

    if source_type != _SOURCE_TYPE:
        raise ValueError(f"unsupported source_type: {source_type!r}")

    _validate_observed_at(observed_at)

    if expected_headers_sha256 is not None:
        expected_headers_sha256 = _require_sha256(
            expected_headers_sha256,
            field="response_headers_sha256",
        )

    actual_body_sha256 = _sha256(response_body)
    if actual_body_sha256 != expected_body_sha256:
        raise ValueError("response body SHA-256 mismatch")

    actual_headers_sha256: str | None = None
    if expected_headers_sha256 is None:
        if response_headers is not None:
            raise ValueError(
                "response headers were supplied but manifest does not bind them"
            )
    else:
        if response_headers is None:
            raise ValueError("manifest requires response headers")
        actual_headers_sha256 = _sha256(response_headers)
        if actual_headers_sha256 != expected_headers_sha256:
            raise ValueError("response headers SHA-256 mismatch")

    request_store, request_campaign = _parse_request_context(request_url)

    request_context_verified = (
        request_store == store_code and request_campaign == campaign_id
    )
    if not request_context_verified:
        raise ValueError("manifest store/campaign does not match preserved request URL")

    return EsselungaCaptureEvidence(
        manifest_sha256=_sha256(manifest_capture),
        request_url=request_url,
        source_type=source_type,
        observed_at=observed_at,
        response_body_sha256=actual_body_sha256,
        response_headers_sha256=actual_headers_sha256,
        store_code=store_code,
        campaign_id=campaign_id,
        request_context_verified=True,
    )


def _load_manifest(raw: bytes) -> Mapping[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("capture manifest must be valid UTF-8 JSON") from error

    if not isinstance(value, Mapping):
        raise ValueError("capture manifest must contain a JSON object")

    keys = set(value)
    missing = _REQUIRED_MANIFEST_FIELDS - keys
    extra = keys - _REQUIRED_MANIFEST_FIELDS

    if missing:
        raise ValueError(f"capture manifest missing fields: {sorted(missing)!r}")
    if extra:
        raise ValueError(f"capture manifest has unsupported fields: {sorted(extra)!r}")

    return value


def _parse_request_context(request_url: str) -> tuple[str, str]:
    parsed = urlsplit(request_url)

    if parsed.scheme != "https":
        raise ValueError("request_url must use https")
    if parsed.hostname != "www.esselunga.it":
        raise ValueError("request_url must target www.esselunga.it")
    if parsed.query or parsed.fragment:
        raise ValueError(
            "request_url must preserve the digital-grid URL without extras"
        )
    if not parsed.path.startswith(
        "/services/istituzionale35/digital-grid.condition:nav_menu"
    ):
        raise ValueError("request_url is not an Esselunga digital-grid endpoint")

    match = _DIGITAL_GRID_CONTEXT_PATTERN.search(parsed.path)
    if match is None:
        raise ValueError(
            "request_url does not expose store/campaign acquisition context"
        )

    return match.group("store").upper(), match.group("campaign")


def _validate_observed_at(value: str) -> None:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as error:
        raise ValueError(
            "observed_at must be an explicit UTC RFC3339 timestamp"
        ) from error

    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ValueError("observed_at must be an explicit UTC RFC3339 timestamp")


def _require_nonempty_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field} must not contain surrounding whitespace")
    return value


def _require_sha256(value: Any, *, field: str) -> str:
    value = _require_nonempty_string(value, field=field)

    if len(value) != _SHA256_HEX_LENGTH:
        raise ValueError(f"{field} must be a lowercase SHA-256 hex digest")

    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lowercase SHA-256 hex digest")

    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
