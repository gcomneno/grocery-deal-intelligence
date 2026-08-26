import copy

import pytest

from giadaware_ai.extension import CapabilityFamily, ProposeCapability

from grocery_deal_intelligence.giadaware_ai_adapter import GiadaWareAIAdapter
from grocery_deal_intelligence.ingestion import ingest_offer
from grocery_deal_intelligence.offer_proposal import ProposeOfferCandidateCapability
from grocery_deal_intelligence.validation import _load_schema


class FakeBackend:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate_json(self, *, system_prompt, user_prompt, response_schema=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": copy.deepcopy(response_schema),
            }
        )
        return copy.deepcopy(self.result)


class MutatingSchemaBackend(FakeBackend):
    def generate_json(self, *, system_prompt, user_prompt, response_schema=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": copy.deepcopy(response_schema),
            }
        )
        response_schema["title"] = "mutated by backend"
        return copy.deepcopy(self.result)


class FailingBackend:
    def generate_json(self, *, system_prompt, user_prompt, response_schema=None):
        raise RuntimeError("backend unavailable")


class NonMappingBackend:
    def generate_json(self, *, system_prompt, user_prompt, response_schema=None):
        return ["not", "a", "mapping"]


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
            "scope": "unknown",
            "stores": [],
        },
        "verification": {
            "locality_status": "unknown",
            "evidence_status": "unverified",
        },
        "provenance": {
            "source_type": "test",
            "source_url": "https://example.test/offer",
            "observed_at": "2026-08-26T00:00:00Z",
        },
    }


def test_capability_is_giadaware_ai_propose_family():
    capability = ProposeOfferCandidateCapability(FakeBackend(make_candidate()))

    assert isinstance(capability, ProposeCapability)
    assert capability.family is CapabilityFamily.PROPOSE


def test_capability_invokes_backend_once_with_candidate_only_contract():
    backend = FakeBackend(make_candidate())
    capability = ProposeOfferCandidateCapability(backend)

    result = capability.execute(make_source_record())

    assert result == make_candidate()
    assert len(backend.calls) == 1
    call = backend.calls[0]
    assert "candidate" in call["system_prompt"].lower()
    assert "canonicality" in call["system_prompt"].lower()
    assert '"currency":"EUR"' in call["user_prompt"]
    assert '"name":"Latte Fresco"' in call["user_prompt"]


def test_capability_passes_grocery_owned_canonical_schema_to_backend():
    backend = FakeBackend(make_candidate())
    capability = ProposeOfferCandidateCapability(backend)

    capability.execute(make_source_record())

    assert backend.calls[0]["response_schema"] == _load_schema()
    assert backend.calls[0]["response_schema"]["$id"] == "grocery-offer-v0.1.schema.json"


def test_backend_schema_mutation_does_not_mutate_grocery_schema_source():
    expected_schema = _load_schema()
    backend = MutatingSchemaBackend(make_candidate())
    capability = ProposeOfferCandidateCapability(backend)

    capability.execute(make_source_record())

    assert _load_schema() == expected_schema


def test_capability_does_not_mutate_source_record():
    source = make_source_record()
    before = copy.deepcopy(source)
    capability = ProposeOfferCandidateCapability(FakeBackend(make_candidate()))

    capability.execute(source)

    assert source == before


def test_capability_returns_detached_candidate_mapping():
    candidate = make_candidate()
    backend = FakeBackend(candidate)
    capability = ProposeOfferCandidateCapability(backend)

    result = capability.execute(make_source_record())
    result["promotion"]["type"] = "changed"

    assert candidate["promotion"]["type"] == "test"


def test_capability_rejects_non_mapping_input():
    capability = ProposeOfferCandidateCapability(FakeBackend(make_candidate()))

    with pytest.raises(TypeError, match="source_record must be a mapping"):
        capability.execute("not-a-record")


def test_capability_rejects_non_mapping_backend_output():
    capability = ProposeOfferCandidateCapability(NonMappingBackend())

    with pytest.raises(TypeError, match="backend must return mapping data"):
        capability.execute(make_source_record())


def test_capability_propagates_backend_failure():
    capability = ProposeOfferCandidateCapability(FailingBackend())

    with pytest.raises(RuntimeError, match="backend unavailable"):
        capability.execute(make_source_record())


@pytest.mark.parametrize("authority_field", ["canonical", "validated", "valid"])
def test_capability_rejects_authority_fields(authority_field):
    candidate = make_candidate()
    candidate[authority_field] = True
    capability = ProposeOfferCandidateCapability(FakeBackend(candidate))

    with pytest.raises(ValueError, match="must not include authority fields"):
        capability.execute(make_source_record())


def test_end_to_end_candidate_is_not_canonical_without_deterministic_validation():
    capability = ProposeOfferCandidateCapability(FakeBackend(make_candidate()))
    adapter = GiadaWareAIAdapter(capability)

    result = ingest_offer(make_source_record(), ai=adapter)

    assert result["candidate"] == make_candidate()
    assert result["validated"] is False
    assert result["canonical"] is None


def test_end_to_end_candidate_becomes_canonical_only_after_validation():
    capability = ProposeOfferCandidateCapability(FakeBackend(make_candidate()))
    adapter = GiadaWareAIAdapter(capability)

    result = ingest_offer(make_source_record(), ai=adapter, validate=True)

    assert result["validated"] is True
    assert result["canonical"] == make_candidate()


def test_plausible_but_invalid_ai_candidate_is_rejected_downstream():
    candidate = make_candidate()
    candidate["price"] = "1.49"
    capability = ProposeOfferCandidateCapability(FakeBackend(candidate))
    adapter = GiadaWareAIAdapter(capability)

    result = ingest_offer(make_source_record(), ai=adapter, validate=True)

    assert result["candidate"] == candidate
    assert result["validated"] is False
    assert result["canonical"] is None
