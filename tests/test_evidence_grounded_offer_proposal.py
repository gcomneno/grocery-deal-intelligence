import copy
import json

from grocery_deal_intelligence.ai_adapter import OfferCandidateAdapter
from grocery_deal_intelligence.giadaware_ai_adapter import GiadaWareAIAdapter
from grocery_deal_intelligence.ingestion import ingest_offer
from grocery_deal_intelligence.offer_proposal import ProposeOfferCandidateCapability


class RecordingBackend:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_json(self, *, system_prompt, user_prompt, response_schema=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": copy.deepcopy(response_schema),
            }
        )
        return copy.deepcopy(self.response)


def _candidate():
    return {
        "retailer": "lidl",
        "product_name": "Example",
        "price": 1.99,
        "currency": "EUR",
        "promotion": {"type": "standard", "requires_loyalty": False},
        "validity": {"from": "2026-08-01", "to": "2026-08-31"},
        "locality": {"scope": "national", "stores": []},
        "verification": {
            "locality_status": "unknown",
            "evidence_status": "unverified",
        },
        "provenance": {
            "source_type": "fixture",
            "source_url": "https://example.invalid/source",
            "observed_at": "2026-08-27T00:00:00Z",
        },
    }


def test_grounded_capability_keeps_raw_source_and_evidence_separate():
    backend = RecordingBackend(_candidate())
    capability = ProposeOfferCandidateCapability(backend)
    source = {"title": "Example", "raw_price": "1,99"}
    evidence = {"retailer": "lidl", "product_name": "Example", "price": 1.99}
    source_before = copy.deepcopy(source)
    evidence_before = copy.deepcopy(evidence)

    capability.execute_grounded(source, source_evidence=evidence)

    assert source == source_before
    assert evidence == evidence_before
    prompt = backend.calls[0]["user_prompt"]
    assert "DETERMINISTIC SOURCE EVIDENCE:" in prompt
    assert "RAW SOURCE RECORD:" in prompt
    assert json.dumps(evidence, sort_keys=True, separators=(",", ":")) in prompt
    assert json.dumps(source, sort_keys=True, separators=(",", ":")) in prompt
    assert backend.calls[0]["response_schema"] is not None


def test_legacy_capability_execution_remains_source_only():
    backend = RecordingBackend(_candidate())
    capability = ProposeOfferCandidateCapability(backend)

    capability.execute({"title": "Example"})

    prompt = backend.calls[0]["user_prompt"]
    assert "RAW SOURCE RECORD:" in prompt
    assert "DETERMINISTIC SOURCE EVIDENCE:" not in prompt


def test_giadaware_adapter_passes_detached_grounding_to_capability():
    class RecordingCapability:
        def __init__(self):
            self.source = None
            self.evidence = None

        def execute(self, value):
            return _candidate()

        def execute_grounded(self, value, *, source_evidence):
            self.source = value
            self.evidence = source_evidence
            value["mutated_by_capability"] = True
            source_evidence["mutated_by_capability"] = True
            return _candidate()

    capability = RecordingCapability()
    adapter = GiadaWareAIAdapter(capability)
    source = {"title": "Example"}
    evidence = {"retailer": "lidl"}
    source_before = copy.deepcopy(source)
    evidence_before = copy.deepcopy(evidence)

    result = adapter.propose_grounded(source, source_evidence=evidence)

    assert result == _candidate()
    assert source == source_before
    assert evidence == evidence_before
    assert capability.source["mutated_by_capability"] is True
    assert capability.evidence["mutated_by_capability"] is True


def test_default_adapter_grounding_hook_preserves_legacy_adapters():
    class LegacyAdapter(OfferCandidateAdapter):
        def propose(self, source_record):
            return {"seen": copy.deepcopy(source_record)}

    adapter = LegacyAdapter()
    source = {"x": 1}

    assert adapter.propose_grounded(source, source_evidence={"retailer": "lidl"}) == {
        "seen": source
    }


def test_admission_path_projects_evidence_before_grounded_ai_proposal():
    source = {
        "retailer": "lidl",
        "product_name": "Example",
        "price": 1.99,
        "currency": "EUR",
        "promotion_type": "standard",
        "requires_loyalty": False,
        "valid_from": "2026-08-01",
        "valid_to": "2026-08-31",
        "locality": {"stores": []},
        "provenance": {
            "source_type": "official_web",
            "campaign_url": "https://example.invalid/source",
            "observed_at": "2026-08-27T00:00:00Z",
        },
        "verification": {"locality": "verified"},
    }

    class GroundedAI:
        def __init__(self):
            self.evidence = None

        def propose_grounded(self, source_record, *, source_evidence):
            self.evidence = copy.deepcopy(source_evidence)
            return _candidate()

    ai = GroundedAI()
    ingest_offer(source, ai=ai, validate=True, admission=True, retailer="lidl")

    assert ai.evidence["retailer"] == "lidl"
    assert ai.evidence["product_name"] == "Example"
    assert ai.evidence["price"] == 1.99
    assert ai.evidence["validity"] == {
        "from": "2026-08-01",
        "to": "2026-08-31",
    }
