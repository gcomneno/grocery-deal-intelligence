"""Evidence-backed Esselunga acquisition context.

Acquisition context is evidence-bearing input to retailer-specific source-evidence
projection. Caller arguments identify what should be verified; they are never
authority by themselves.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

_CAMPAIGN_STORE_PATTERN = re.compile(r'data-store="([^"]+)"')
_CAMPAIGN_ID_PATTERN = re.compile(r'data-cod-promo="([^"]+)"')


@dataclass(frozen=True)
class EsselungaAcquisitionContext:
    """Observed and verified authority from committed acquisition evidence."""

    expected_store_code: str
    expected_campaign_id: str | None
    store_detail_sha256: str
    store_listing_sha256: str
    campaign_artifact_sha256: str | None
    observed_store_code: str | None
    observed_store_name: str | None
    observed_store_locality: str | None
    observed_store_province: str | None
    campaign_store_codes: tuple[str, ...]
    campaign_ids: tuple[str, ...]
    store_verified: bool
    campaign_store_verified: bool


def verify_esselunga_acquisition_context(
    *,
    store_detail_capture: bytes,
    store_listing_capture: bytes,
    expected_store_code: str,
    expected_campaign_id: str | None = None,
    campaign_capture: bytes | None = None,
) -> EsselungaAcquisitionContext:
    """Verify Esselunga acquisition facts from captured evidence bytes.

    Expected values select the relationship to verify. They do not become
    evidence merely because the caller supplied them.
    """
    if not isinstance(store_detail_capture, bytes):
        raise TypeError("store_detail_capture must be bytes")
    if not isinstance(store_listing_capture, bytes):
        raise TypeError("store_listing_capture must be bytes")
    if not isinstance(expected_store_code, str) or not expected_store_code.strip():
        raise ValueError("expected_store_code must be a non-empty string")
    if expected_campaign_id is not None and (
        not isinstance(expected_campaign_id, str) or not expected_campaign_id.strip()
    ):
        raise ValueError("expected_campaign_id must be None or a non-empty string")
    if campaign_capture is not None and not isinstance(campaign_capture, bytes):
        raise TypeError("campaign_capture must be bytes or None")

    normalized_store = expected_store_code.strip().upper()
    normalized_campaign = (
        expected_campaign_id.strip() if expected_campaign_id is not None else None
    )

    store_detail = _load_mapping(store_detail_capture, label="store detail")
    store_listing = _load_sequence(store_listing_capture, label="store listing")

    detail_code = store_detail.get("abbrev")
    detail_name = store_detail.get("descBreveClienti")
    detail_province = store_detail.get("province")

    town = store_detail.get("town")
    detail_locality = town.get("name") if isinstance(town, Mapping) else None

    listing_matches = [
        item
        for item in store_listing
        if isinstance(item, Mapping)
        and isinstance(item.get("code"), str)
        and item["code"].upper() == normalized_store
    ]

    detail_matches_expected = (
        isinstance(detail_code, str) and detail_code.upper() == normalized_store
    )
    listing_matches_expected = len(listing_matches) == 1

    store_verified = detail_matches_expected and listing_matches_expected

    campaign_store_codes: tuple[str, ...] = ()
    campaign_ids: tuple[str, ...] = ()
    campaign_sha256: str | None = None
    campaign_store_verified = False

    if campaign_capture is not None:
        campaign_sha256 = _sha256(campaign_capture)
        campaign_text = campaign_capture.decode("utf-8", errors="replace")

        campaign_store_codes = tuple(
            sorted(
                {
                    match.upper()
                    for match in _CAMPAIGN_STORE_PATTERN.findall(campaign_text)
                    if match
                }
            )
        )
        campaign_ids = tuple(
            sorted(
                {
                    match
                    for match in _CAMPAIGN_ID_PATTERN.findall(campaign_text)
                    if match
                }
            )
        )

        campaign_store_verified = (
            store_verified
            and normalized_campaign is not None
            and campaign_store_codes == (normalized_store,)
            and normalized_campaign in campaign_ids
        )

    return EsselungaAcquisitionContext(
        expected_store_code=normalized_store,
        expected_campaign_id=normalized_campaign,
        store_detail_sha256=_sha256(store_detail_capture),
        store_listing_sha256=_sha256(store_listing_capture),
        campaign_artifact_sha256=campaign_sha256,
        observed_store_code=detail_code if isinstance(detail_code, str) else None,
        observed_store_name=detail_name if isinstance(detail_name, str) else None,
        observed_store_locality=(
            detail_locality if isinstance(detail_locality, str) else None
        ),
        observed_store_province=(
            detail_province if isinstance(detail_province, str) else None
        ),
        campaign_store_codes=campaign_store_codes,
        campaign_ids=campaign_ids,
        store_verified=store_verified,
        campaign_store_verified=campaign_store_verified,
    )


def _load_mapping(raw: bytes, *, label: str) -> Mapping[str, Any]:
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} capture must contain a JSON object")
    return value


def _load_sequence(raw: bytes, *, label: str) -> Sequence[Any]:
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"{label} capture must contain a JSON array")
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
