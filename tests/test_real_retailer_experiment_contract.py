import copy

import pytest

from experiments import run_real_retailer_ai_ingestion as experiment


def test_selected_real_retailer_record_has_stable_identity():
    record = experiment.load_selected_source_record()

    assert record["id"] == experiment.SOURCE_RECORD_ID
    assert record["code"] == experiment.SOURCE_RECORD_CODE
    assert experiment.SOURCE_RELATIVE_PATH.as_posix() == "esselunga/all-8400.json"


def test_experiment_is_opt_in(monkeypatch):
    monkeypatch.delenv(experiment.RUN_ENV, raising=False)

    with pytest.raises(RuntimeError, match="opt-in"):
        experiment.run_experiment()


def test_experiment_records_source_candidate_and_deterministic_decision(monkeypatch):
    source = experiment.load_selected_source_record()
    source_before = copy.deepcopy(source)

    candidate = {
        "retailer": "esselunga",
        "product_name": source["title"],
        "price": source["promozioni_prezzoPromo"][0],
        "currency": "EUR",
        "reference_price": source["prezzo"],
        "packaging_text": None,
        "base_price_text": None,
        "promotion": {"type": "price_reduction", "requires_loyalty": False},
        "validity": {
            "from": source["promozioni_dataInizioPromoArticolo"][0],
            "to": source["promozioni_dataFinePromoArticolo"][0],
        },
        "locality": {"scope": "unknown", "stores": []},
        "verification": {
            "locality_status": "unknown",
            "evidence_status": "unverified",
        },
        "provenance": {
            "source_type": "repository_fixture",
            "source_url": "esselunga/all-8400.json",
            "observed_at": source["promozioni_dataInizioPromoArticolo"][0],
        },
    }

    class FakeBackend:
        def __init__(self, *, model, base_url, timeout):
            self.model = model
            self.base_url = base_url
            self.timeout = timeout

        def generate_json(self, *, system_prompt, user_prompt):
            return copy.deepcopy(candidate)

    monkeypatch.setattr(experiment, "OllamaBackend", FakeBackend)
    monkeypatch.setenv(experiment.RUN_ENV, "1")

    evidence = experiment.run_experiment()

    assert evidence["source_record"] == source_before
    assert evidence["candidate"] == candidate
    assert evidence["validated"] is True
    assert evidence["canonical"] == candidate
    assert evidence["runtime_metadata"]["model"] == experiment.DEFAULT_MODEL
    assert evidence["source_identity"]["record_id"] == experiment.SOURCE_RECORD_ID
    assert len(evidence["source_identity"]["file_sha256"]) == 64


def test_invalid_ai_candidate_cannot_become_canonical(monkeypatch):
    class FakeBackend:
        def __init__(self, *, model, base_url, timeout):
            pass

        def generate_json(self, *, system_prompt, user_prompt):
            return {
                "product_name": "candidate without required canonical evidence",
                "price": "1.83",
            }

    monkeypatch.setattr(experiment, "OllamaBackend", FakeBackend)
    monkeypatch.setenv(experiment.RUN_ENV, "1")

    evidence = experiment.run_experiment()

    assert evidence["validated"] is False
    assert evidence["canonical"] is None
