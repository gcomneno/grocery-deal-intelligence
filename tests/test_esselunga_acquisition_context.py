from __future__ import annotations

from pathlib import Path

from grocery_deal_intelligence.esselunga_acquisition import (
    verify_esselunga_acquisition_context,
)
from grocery_deal_intelligence.source_evidence import project_source_evidence

_ROOT = Path(__file__).resolve().parent.parent
_STORE_DETAIL = _ROOT / "esselunga/ari-store.json"
_STORE_LISTING = _ROOT / "esselunga/porcari-stores.json"
_CAPTURED_CAMPAIGN = _ROOT / "esselunga/esselunga-sconti-50.html"


def _source() -> dict:
    return {
        "title": "FORST V.I.P. Pils CAN 3 x 0,33 l",
        "prezzo": 2.33,
        "promozioni_prezzoPromo": [1.83],
        "promozioni_dataInizioPromoArticolo": ["2026-08-24T00:00:00Z"],
        "promozioni_dataFinePromoArticolo": ["2026-09-20T00:00:00Z"],
        "promozioni_desMeccanica": ["Sc + Facile val"],
    }


def _real_context():
    return verify_esselunga_acquisition_context(
        store_detail_capture=_STORE_DETAIL.read_bytes(),
        store_listing_capture=_STORE_LISTING.read_bytes(),
        expected_store_code="ARI",
        expected_campaign_id="8400",
        campaign_capture=_CAPTURED_CAMPAIGN.read_bytes(),
    )


def test_real_store_capture_verifies_ari_identity():
    context = _real_context()

    assert context.store_verified is True
    assert context.expected_store_code == "ARI"
    assert context.observed_store_code == "ARI"
    assert context.observed_store_name == "Esselunga di Porcari"
    assert context.observed_store_locality == "Porcari"
    assert context.observed_store_province == "LU"
    assert len(context.store_detail_sha256) == 64
    assert len(context.store_listing_sha256) == 64


def test_current_campaign_capture_does_not_authorize_ari_binding():
    context = _real_context()

    assert context.campaign_store_codes == ("SCO",)
    assert "8400" in context.campaign_ids
    assert context.campaign_store_verified is False
    assert context.campaign_artifact_sha256 is not None


def test_matching_campaign_capture_can_verify_store_campaign_relationship():
    campaign = b'<main data-store="ARI" data-cod-promo="8400"></main>'

    context = verify_esselunga_acquisition_context(
        store_detail_capture=_STORE_DETAIL.read_bytes(),
        store_listing_capture=_STORE_LISTING.read_bytes(),
        expected_store_code="ARI",
        expected_campaign_id="8400",
        campaign_capture=campaign,
    )

    assert context.store_verified is True
    assert context.campaign_store_codes == ("ARI",)
    assert context.campaign_ids == ("8400",)
    assert context.campaign_store_verified is True


def test_caller_store_value_is_not_authority_when_captures_disagree():
    context = verify_esselunga_acquisition_context(
        store_detail_capture=_STORE_DETAIL.read_bytes(),
        store_listing_capture=_STORE_LISTING.read_bytes(),
        expected_store_code="SCO",
        expected_campaign_id="8400",
        campaign_capture=_CAPTURED_CAMPAIGN.read_bytes(),
    )

    assert context.store_verified is False
    assert context.campaign_store_verified is False


def test_real_unverified_campaign_context_adds_no_locality_authority():
    evidence = project_source_evidence(
        _source(),
        retailer="esselunga",
        esselunga_acquisition_context=_real_context(),
    )

    assert "locality" not in evidence
    assert "verification" not in evidence
    assert "currency" not in evidence
    assert "provenance" not in evidence


def test_verified_campaign_context_authorizes_only_store_locality():
    campaign = b'<main data-store="ARI" data-cod-promo="8400"></main>'
    context = verify_esselunga_acquisition_context(
        store_detail_capture=_STORE_DETAIL.read_bytes(),
        store_listing_capture=_STORE_LISTING.read_bytes(),
        expected_store_code="ARI",
        expected_campaign_id="8400",
        campaign_capture=campaign,
    )

    evidence = project_source_evidence(
        _source(),
        retailer="esselunga",
        esselunga_acquisition_context=context,
    )

    assert evidence["locality"] == {
        "scope": "store",
        "stores": ["ARI"],
    }
    assert evidence["verification"] == {
        "locality_status": "verified",
    }

    assert "currency" not in evidence
    assert "provenance" not in evidence
    assert "evidence_status" not in evidence["verification"]


def test_existing_esselunga_projection_without_context_is_unchanged():
    evidence = project_source_evidence(_source(), retailer="esselunga")

    assert evidence == {
        "retailer": "esselunga",
        "product_name": "FORST V.I.P. Pils CAN 3 x 0,33 l",
        "price": 1.83,
        "reference_price": 2.33,
        "promotion": {"discount_text": "Sc + Facile val"},
        "validity": {
            "from": "2026-08-24T00:00:00Z",
            "to": "2026-09-20T00:00:00Z",
        },
    }
