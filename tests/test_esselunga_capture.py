from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError

import pytest

from grocery_deal_intelligence.esselunga_capture import verify_esselunga_capture

_REQUEST_URL = (
    "https://www.esselunga.it/services/istituzionale35/"
    "digital-grid.condition:nav_menu"
    ".abbrev:ARI.page:0.rows:1000.codPromo:8400.json"
)
_OBSERVED_AT = "2026-08-31T14:30:00Z"
_BODY = b'{"status":"OK","items":[]}'
_HEADERS = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _manifest(
    *,
    request_url: str = _REQUEST_URL,
    body: bytes = _BODY,
    headers: bytes | None = _HEADERS,
    store_code: str = "ARI",
    campaign_id: str = "8400",
    observed_at: str = _OBSERVED_AT,
    extra: dict | None = None,
) -> bytes:
    value = {
        "version": 1,
        "request_url": request_url,
        "source_type": "retailer_api",
        "observed_at": observed_at,
        "response_body_sha256": _sha256(body),
        "response_headers_sha256": _sha256(headers) if headers is not None else None,
        "store_code": store_code,
        "campaign_id": campaign_id,
    }

    if extra is not None:
        value.update(extra)

    return (json.dumps(value, sort_keys=True) + "\n").encode()


def test_exact_capture_relationship_is_verified():
    manifest = _manifest()

    capture = verify_esselunga_capture(
        manifest_capture=manifest,
        response_body=_BODY,
        response_headers=_HEADERS,
    )

    assert capture.manifest_sha256 == _sha256(manifest)
    assert capture.request_url == _REQUEST_URL
    assert capture.source_type == "retailer_api"
    assert capture.observed_at == _OBSERVED_AT
    assert capture.response_body_sha256 == _sha256(_BODY)
    assert capture.response_headers_sha256 == _sha256(_HEADERS)
    assert capture.store_code == "ARI"
    assert capture.campaign_id == "8400"
    assert capture.request_context_verified is True


def test_body_identity_mismatch_fails_closed():
    with pytest.raises(ValueError, match="body SHA-256 mismatch"):
        verify_esselunga_capture(
            manifest_capture=_manifest(),
            response_body=b'{"status":"OK","items":[1]}',
            response_headers=_HEADERS,
        )


def test_header_identity_mismatch_fails_closed():
    with pytest.raises(ValueError, match="headers SHA-256 mismatch"):
        verify_esselunga_capture(
            manifest_capture=_manifest(),
            response_body=_BODY,
            response_headers=b"HTTP/1.1 500 Internal Server Error\r\n",
        )


def test_bound_headers_cannot_be_omitted():
    with pytest.raises(ValueError, match="requires response headers"):
        verify_esselunga_capture(
            manifest_capture=_manifest(),
            response_body=_BODY,
        )


def test_unbound_headers_cannot_be_attached_after_capture():
    with pytest.raises(ValueError, match="does not bind them"):
        verify_esselunga_capture(
            manifest_capture=_manifest(headers=None),
            response_body=_BODY,
            response_headers=_HEADERS,
        )


def test_manifest_store_cannot_override_preserved_request_url():
    with pytest.raises(ValueError, match="store/campaign"):
        verify_esselunga_capture(
            manifest_capture=_manifest(store_code="SCO"),
            response_body=_BODY,
            response_headers=_HEADERS,
        )


def test_manifest_campaign_cannot_override_preserved_request_url():
    with pytest.raises(ValueError, match="store/campaign"):
        verify_esselunga_capture(
            manifest_capture=_manifest(campaign_id="8260"),
            response_body=_BODY,
            response_headers=_HEADERS,
        )


def test_reconstructed_or_different_url_is_not_equivalent_evidence():
    different_url = (
        "https://www.esselunga.it/services/istituzionale35/"
        "digital-grid.condition:nav_menu"
        ".abbrev:SCO.page:0.rows:1000.codPromo:8400.json"
    )

    with pytest.raises(ValueError, match="store/campaign"):
        verify_esselunga_capture(
            manifest_capture=_manifest(request_url=different_url),
            response_body=_BODY,
            response_headers=_HEADERS,
        )


@pytest.mark.parametrize(
    "observed_at",
    [
        "",
        "2026-08-31",
        "2026-08-31T14:30:00",
        "2026-08-31T14:30:00+00:00",
    ],
)
def test_observed_at_requires_explicit_preserved_utc_timestamp(observed_at):
    with pytest.raises(ValueError, match="observed_at"):
        verify_esselunga_capture(
            manifest_capture=_manifest(observed_at=observed_at),
            response_body=_BODY,
            response_headers=_HEADERS,
        )


def test_currency_cannot_be_smuggled_in_as_manifest_authority():
    with pytest.raises(ValueError, match="unsupported fields"):
        verify_esselunga_capture(
            manifest_capture=_manifest(extra={"currency": "EUR"}),
            response_body=_BODY,
            response_headers=_HEADERS,
        )


def test_evidence_status_cannot_be_hard_coded_in_manifest():
    with pytest.raises(ValueError, match="unsupported fields"):
        verify_esselunga_capture(
            manifest_capture=_manifest(
                extra={"evidence_status": "verified"},
            ),
            response_body=_BODY,
            response_headers=_HEADERS,
        )


def test_bare_historical_body_is_not_self_authorizing():
    with pytest.raises(TypeError, match="manifest_capture"):
        verify_esselunga_capture(
            manifest_capture=None,
            response_body=_BODY,
            response_headers=_HEADERS,
        )


def test_verified_capture_is_immutable():
    capture = verify_esselunga_capture(
        manifest_capture=_manifest(),
        response_body=_BODY,
        response_headers=_HEADERS,
    )

    with pytest.raises(FrozenInstanceError):
        capture.store_code = "SCO"


def test_no_canonical_verification_status_is_created():
    capture = verify_esselunga_capture(
        manifest_capture=_manifest(),
        response_body=_BODY,
        response_headers=_HEADERS,
    )

    assert not hasattr(capture, "evidence_status")
    assert not hasattr(capture, "currency")
