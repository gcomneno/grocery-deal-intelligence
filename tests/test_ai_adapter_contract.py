import copy

import pytest

from grocery_deal_intelligence.ai_adapter import OfferCandidateAdapter


def make_source_record():
    return {
        "retailer": "lidl",
        "name": "Latte Fresco",
        "price": "1.49",
        "currency": "EUR",
    }


class FakeOfferCandidateAdapter(OfferCandidateAdapter):
    def __init__(self, candidate):
        self.candidate = copy.deepcopy(candidate)
        self.calls = []

    def propose(self, source_record):
        self.calls.append(copy.deepcopy(source_record))
        return copy.deepcopy(self.candidate)


def make_candidate():
    return {
        "retailer": "lidl",
        "product_name": "Latte Fresco",
        "price": 1.49,
        "currency": "EUR",
    }


def test_adapter_contract_exposes_propose():
    adapter = FakeOfferCandidateAdapter(make_candidate())

    assert hasattr(adapter, "propose")
    assert callable(adapter.propose)


def test_adapter_produces_candidate_data():
    source = make_source_record()
    candidate = make_candidate()

    adapter = FakeOfferCandidateAdapter(candidate)

    result = adapter.propose(source)

    assert result == candidate


def test_adapter_does_not_mutate_source_record():
    source = make_source_record()
    before = copy.deepcopy(source)

    adapter = FakeOfferCandidateAdapter(make_candidate())

    adapter.propose(source)

    assert source == before


def test_adapter_receives_a_copy_safe_for_read_only_processing():
    source = make_source_record()

    adapter = FakeOfferCandidateAdapter(make_candidate())

    adapter.propose(source)

    assert adapter.calls == [source]


def test_adapter_contract_does_not_define_canonicality():
    adapter = FakeOfferCandidateAdapter(make_candidate())

    result = adapter.propose(make_source_record())

    assert "canonical" not in result
    assert "validated" not in result
    assert "valid" not in result


def test_contract_is_independent_of_giadaware_ai_runtime():
    assert "giadaware_ai" not in OfferCandidateAdapter.__module__


def test_base_contract_cannot_be_used_as_concrete_adapter():
    with pytest.raises(TypeError):
        OfferCandidateAdapter()
