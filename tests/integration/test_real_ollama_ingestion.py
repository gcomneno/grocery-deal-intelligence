import copy
import os

import pytest

_RUN_ENV = "GROCERY_DEAL_INTELLIGENCE_RUN_OLLAMA_INTEGRATION"
_BASE_URL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_BASE_URL"
_MODEL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_MODEL"

pytestmark = pytest.mark.skipif(
    os.environ.get(_RUN_ENV) != "1",
    reason=f"set {_RUN_ENV}=1 to run the real Ollama integration",
)


def make_source_record():
    return {
        "retailer": "lidl",
        "product_name": "Latte Fresco Intero",
        "price": 1.49,
        "currency": "EUR",
        "reference_price": None,
        "packaging_text": "1 L",
        "base_price_text": "1.49 EUR/L",
        "promotion": {
            "type": "standard",
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
            "source_type": "integration-fixture",
            "source_url": "https://example.test/lidl/latte-fresco-intero",
            "observed_at": "2026-08-26T00:00:00Z",
        },
    }


def test_real_ollama_candidate_remains_subject_to_deterministic_validation():
    from giadaware_ai.backends.ollama import OllamaBackend

    from grocery_deal_intelligence.giadaware_ai_adapter import GiadaWareAIAdapter
    from grocery_deal_intelligence.ingestion import ingest_offer
    from grocery_deal_intelligence.offer_proposal import ProposeOfferCandidateCapability

    source = make_source_record()
    before = copy.deepcopy(source)

    backend = OllamaBackend(
        model=os.environ.get(_MODEL_ENV, "qwen2.5:1.5b-instruct"),
        base_url=os.environ.get(_BASE_URL_ENV, "http://127.0.0.1:11434"),
    )
    capability = ProposeOfferCandidateCapability(backend)
    adapter = GiadaWareAIAdapter(capability)

    result = ingest_offer(source, ai=adapter, validate=True)

    assert source == before
    assert result["ai_used"] is True
    assert isinstance(result["candidate"], dict)
    assert not {"canonical", "validated", "valid"}.intersection(result["candidate"])

    if result["validated"]:
        assert result["canonical"] == result["candidate"]
    else:
        assert result["canonical"] is None
