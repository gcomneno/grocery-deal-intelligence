import copy

import pytest

from grocery_deal_intelligence.ai_adapter import OfferCandidateAdapter
from grocery_deal_intelligence.giadaware_ai_adapter import GiadaWareAIAdapter
from grocery_deal_intelligence.ingestion import ingest_offer


def make_source_record():
    return {
        "retailer": "lidl",
        "name": "Latte Fresco",
        "price": "1.49",
        "currency": "EUR",
    }


def make_candidate():
    return {
        "retailer": "lidl",
        "product_name": "Latte Fresco",
        "price": 1.49,
        "currency": "EUR",
        "reference_price": None,
        "packaging_text": None,
        "base_price_text": None,
        "promotion": {
            "type": "test",
            "requires_loyalty": False,
        },
        "validity": {
            "from": None,
            "to": None,
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
            "source_type": "test",
            "source_url": "https://example.test/offer",
            "observed_at": "2026-08-26T00:00:00Z",
        },
    }


class StubProposeCapability:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def execute(self, value):
        self.calls.append(copy.deepcopy(value))
        return copy.deepcopy(self.result)


class MutatingCapability:
    def __init__(self, result):
        self.result = result

    def execute(self, value):
        value["mutated_by_capability"] = True
        return self.result


class FailingCapability:
    def execute(self, value):
        raise RuntimeError("AI backend unavailable")


def test_giadaware_adapter_implements_offer_candidate_contract():
    adapter = GiadaWareAIAdapter(StubProposeCapability(make_candidate()))

    assert isinstance(adapter, OfferCandidateAdapter)


def test_adapter_invokes_injected_propose_capability_exactly_once():
    source = make_source_record()
    capability = StubProposeCapability(make_candidate())
    adapter = GiadaWareAIAdapter(capability)

    adapter.propose(source)

    assert capability.calls == [source]


def test_adapter_does_not_mutate_source_when_capability_mutates_input():
    source = make_source_record()
    before = copy.deepcopy(source)
    adapter = GiadaWareAIAdapter(MutatingCapability(make_candidate()))

    adapter.propose(source)

    assert source == before


def test_adapter_returns_detached_candidate_mapping():
    source = make_source_record()
    candidate = make_candidate()
    capability = StubProposeCapability(candidate)
    adapter = GiadaWareAIAdapter(capability)

    result = adapter.propose(source)

    assert result == candidate
    assert result is not candidate


def test_adapter_rejects_non_mapping_capability_result():
    adapter = GiadaWareAIAdapter(StubProposeCapability(["not", "candidate", "data"]))

    with pytest.raises(TypeError, match="must return mapping data"):
        adapter.propose(make_source_record())


def test_capability_failure_propagates_without_fallback_candidate():
    adapter = GiadaWareAIAdapter(FailingCapability())

    with pytest.raises(RuntimeError, match="AI backend unavailable"):
        adapter.propose(make_source_record())


def test_adapter_output_has_no_canonicality_authority():
    adapter = GiadaWareAIAdapter(StubProposeCapability(make_candidate()))

    result = adapter.propose(make_source_record())

    assert "canonical" not in result
    assert "validated" not in result
    assert "valid" not in result


def test_deterministic_ingestion_remains_authoritative():
    invalid_candidate = make_candidate()
    invalid_candidate["price"] = "not-a-number"
    adapter = GiadaWareAIAdapter(StubProposeCapability(invalid_candidate))

    result = ingest_offer(make_source_record(), ai=adapter, validate=True)

    assert result["candidate"] == invalid_candidate
    assert result["validated"] is False
    assert result["canonical"] is None
