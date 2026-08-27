import copy

import grocery_deal_intelligence.ingestion as ingestion_module
from grocery_deal_intelligence.ingestion import (
    ingest_offer,
    ingest_offer_proposal_path,
)


class FakeProposalAdapter:
    def __init__(self, proposal):
        self.proposal = proposal
        self.calls = []

    def propose_grounded(self, source_record, *, source_evidence):
        self.calls.append(
            {
                "source_record": copy.deepcopy(source_record),
                "source_evidence": copy.deepcopy(source_evidence),
            }
        )
        return copy.deepcopy(self.proposal)


class FakeLegacyAdapter:
    def __init__(self, candidate):
        self.candidate = candidate

    def propose(self, source_record):
        return copy.deepcopy(self.candidate)


def complete_evidence():
    return {
        "retailer": "testmart",
        "product_name": "Latte Fresco",
        "price": 1.49,
        "currency": "EUR",
        "promotion": {
            "type": "standard",
            "requires_loyalty": False,
        },
        "validity": {
            "from": "2026-08-27T00:00:00Z",
            "to": "2026-08-30T23:59:59Z",
        },
        "locality": {
            "scope": "national",
            "stores": [],
        },
        "verification": {
            "locality_status": "verified",
            "evidence_status": "verified",
        },
        "provenance": {
            "source_type": "fixture",
            "source_url": "https://example.test/source",
            "observed_at": "2026-08-27T08:00:00Z",
        },
    }


def test_invalid_proposal_stops_before_claim_verification_and_projection(monkeypatch):
    monkeypatch.setattr(
        ingestion_module,
        "project_source_evidence",
        lambda source, *, retailer: complete_evidence(),
    )
    adapter = FakeProposalAdapter({"price": "not-a-number"})

    result = ingest_offer_proposal_path({}, ai=adapter, retailer="testmart")

    assert result["proposal_validation"]["valid"] is False
    assert result["claim_verification"] is None
    assert result["projection"] is None
    assert result["canonical_validation"] is None
    assert result["admission"] is None
    assert result["canonical"] is None


def test_valid_partial_proposal_can_be_not_projectable_without_fabrication():
    source = {"title": "FORST V.I.P. Pils"}
    adapter = FakeProposalAdapter({"product_name": "FORST V.I.P. Pils"})

    result = ingest_offer_proposal_path(
        source,
        ai=adapter,
        retailer="esselunga",
    )

    assert result["proposal_validation"]["valid"] is True
    assert result["projection"]["projectable"] is False
    assert result["projection"]["candidate"] is None
    assert result["projection"]["missing_required_claims"]
    assert result["canonical_validation"] is None
    assert result["admission"] is None
    assert result["canonical"] is None


def test_projectable_candidate_can_still_fail_canonical_validation(monkeypatch):
    evidence = complete_evidence()
    evidence["currency"] = "eur"
    monkeypatch.setattr(
        ingestion_module,
        "project_source_evidence",
        lambda source, *, retailer: copy.deepcopy(evidence),
    )
    adapter = FakeProposalAdapter({})

    result = ingest_offer_proposal_path({}, ai=adapter, retailer="testmart")

    assert result["projection"]["projectable"] is True
    assert result["canonical_validation"]["valid"] is False
    assert result["admission"]["eligible"] is False
    assert {reason["code"] for reason in result["admission"]["reasons"]} == {
        "structural_invalid"
    }
    assert result["canonical"] is None


def test_full_success_keeps_all_authority_layers_visible(monkeypatch):
    evidence = complete_evidence()
    monkeypatch.setattr(
        ingestion_module,
        "project_source_evidence",
        lambda source, *, retailer: copy.deepcopy(evidence),
    )
    proposal = {
        "product_name": "Latte Fresco",
        "price": 1.49,
    }
    adapter = FakeProposalAdapter(proposal)

    result = ingest_offer_proposal_path(
        {"raw": "source"},
        ai=adapter,
        retailer="testmart",
    )

    assert result["proposal"] == proposal
    assert result["proposal_validation"]["valid"] is True
    assert result["claim_verification"]
    assert result["projection"]["projectable"] is True
    assert result["canonical_validation"]["valid"] is True
    assert result["canonical_claim_verification"]
    assert result["admission"]["eligible"] is True
    assert result["canonical"] == evidence


def test_supported_proposal_claims_and_evidence_are_read_only(monkeypatch):
    evidence = complete_evidence()
    source = {"raw": {"nested": "value"}}
    source_before = copy.deepcopy(source)
    evidence_before = copy.deepcopy(evidence)
    proposal = {"price": 1.49}
    adapter = FakeProposalAdapter(proposal)

    monkeypatch.setattr(
        ingestion_module,
        "project_source_evidence",
        lambda source, *, retailer: copy.deepcopy(evidence),
    )

    result = ingest_offer_proposal_path(source, ai=adapter, retailer="testmart")
    result["source_evidence"]["price"] = 999
    result["proposal"]["price"] = 999

    assert source == source_before
    assert evidence == evidence_before
    assert proposal == {"price": 1.49}
    assert adapter.calls[0]["source_record"] == source_before
    assert adapter.calls[0]["source_evidence"] == evidence_before


def test_legacy_ingest_offer_path_remains_unchanged():
    candidate = complete_evidence()
    adapter = FakeLegacyAdapter(candidate)

    result = ingest_offer(
        {"legacy": True},
        ai=adapter,
        validate=True,
    )

    assert result == {
        "candidate": candidate,
        "ai_used": True,
        "validated": True,
        "canonical": candidate,
    }


def test_proposal_path_requires_adapter_and_retailer():
    try:
        ingest_offer_proposal_path({}, ai=None, retailer="testmart")
    except ValueError as exc:
        assert "AI proposal adapter" in str(exc)
    else:
        raise AssertionError("expected proposal path to require an adapter")

    adapter = FakeProposalAdapter({})
    try:
        ingest_offer_proposal_path({}, ai=adapter, retailer="")
    except ValueError as exc:
        assert "non-empty retailer" in str(exc)
    else:
        raise AssertionError("expected proposal path to require retailer context")
