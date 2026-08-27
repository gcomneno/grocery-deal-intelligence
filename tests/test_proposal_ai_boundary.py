import copy

import pytest

from giadaware_ai.extension import CapabilityFamily, ProposeCapability

from grocery_deal_intelligence.proposal_adapter import GiadaWareAIProposalAdapter
from grocery_deal_intelligence.proposal_ai import ProposeOfferProposalCapability
from grocery_deal_intelligence.proposal_validation import _load_proposal_schema


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


def make_source():
    return {"name": "Latte Fresco", "price": "1.49", "currency": "EUR"}


def test_capability_is_giadaware_propose_family():
    capability = ProposeOfferProposalCapability(FakeBackend({}))

    assert isinstance(capability, ProposeCapability)
    assert capability.family is CapabilityFamily.PROPOSE


def test_capability_uses_proposal_v01_response_schema():
    backend = FakeBackend({"product_name": "Latte Fresco"})
    capability = ProposeOfferProposalCapability(backend)

    capability.execute(make_source())

    assert backend.calls[0]["response_schema"] == _load_proposal_schema()
    assert backend.calls[0]["response_schema"]["$id"] == "grocery-offer-proposal-v0.1.schema.json"


def test_partial_proposal_is_returned_detached():
    proposal = {"product_name": "Latte Fresco", "validity": {"from": "2026-08-27"}}
    capability = ProposeOfferProposalCapability(FakeBackend(proposal))

    result = capability.execute(make_source())
    result["validity"]["from"] = "changed"

    assert proposal["validity"]["from"] == "2026-08-27"


def test_empty_proposal_is_valid_output():
    capability = ProposeOfferProposalCapability(FakeBackend({}))

    assert capability.execute(make_source()) == {}


def test_invalid_proposal_shape_is_rejected_deterministically():
    capability = ProposeOfferProposalCapability(FakeBackend({"validity": {}}))

    with pytest.raises(ValueError, match="invalid Proposal v0.1 output"):
        capability.execute(make_source())


def test_grounded_capability_preserves_input_and_includes_evidence():
    source = make_source()
    evidence = {"retailer": "esselunga", "price": 1.49}
    source_before = copy.deepcopy(source)
    evidence_before = copy.deepcopy(evidence)
    backend = FakeBackend({"retailer": "esselunga", "price": 1.49})
    capability = ProposeOfferProposalCapability(backend)

    capability.execute_grounded(source, source_evidence=evidence)

    assert source == source_before
    assert evidence == evidence_before
    prompt = backend.calls[0]["user_prompt"]
    assert "DETERMINISTIC SOURCE EVIDENCE" in prompt
    assert '"retailer":"esselunga"' in prompt


def test_adapter_returns_detached_partial_proposal():
    proposal = {"price": 1.49}
    adapter = GiadaWareAIProposalAdapter(ProposeOfferProposalCapability(FakeBackend(proposal)))

    result = adapter.propose(make_source())
    result["price"] = 99

    assert proposal["price"] == 1.49


def test_adapter_grounded_path_does_not_mutate_inputs():
    source = make_source()
    evidence = {"retailer": "esselunga"}
    before_source = copy.deepcopy(source)
    before_evidence = copy.deepcopy(evidence)
    adapter = GiadaWareAIProposalAdapter(
        ProposeOfferProposalCapability(FakeBackend({"retailer": "esselunga"}))
    )

    result = adapter.propose_grounded(source, source_evidence=evidence)

    assert result == {"retailer": "esselunga"}
    assert source == before_source
    assert evidence == before_evidence
