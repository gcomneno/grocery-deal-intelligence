import copy

import pytest

from grocery_deal_intelligence.ingestion import ingest_offer


class StubAI:
    def __init__(self, candidate):
        self.candidate = candidate

    def propose(self, source_record):
        return copy.deepcopy(self.candidate)


def source_record():
    return {
        "product_name": "Latte Fresco",
        "price": 1.49,
        "currency": "EUR",
        "valid_from": "2026-08-27T00:00:00Z",
        "valid_to": "2026-08-31T23:59:59Z",
    }


def candidate():
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
            "from": "2026-08-27T00:00:00Z",
            "to": "2026-08-31T23:59:59Z",
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
            "observed_at": "2026-08-27T00:00:00Z",
        },
    }


def test_legacy_validate_true_behavior_remains_structural_only():
    result = ingest_offer(source_record(), ai=StubAI(candidate()), validate=True)

    assert result["validated"] is True
    assert result["canonical"] == candidate()
    assert "admission" not in result
    assert "claim_verification" not in result


def test_admission_requires_explicit_structural_validation():
    with pytest.raises(ValueError, match="admission requires validate=True"):
        ingest_offer(source_record(), admission=True, retailer="lidl")


def test_admission_requires_retailer_context():
    with pytest.raises(ValueError, match="admission requires a non-empty retailer"):
        ingest_offer(source_record(), validate=True, admission=True)


def test_structurally_invalid_candidate_is_ineligible_and_noncanonical():
    bad = candidate()
    bad["price"] = "not-a-number"

    result = ingest_offer(
        source_record(),
        ai=StubAI(bad),
        validate=True,
        admission=True,
        retailer="lidl",
    )

    assert result["validated"] is False
    assert result["structural_validation"]["valid"] is False
    assert result["admission"]["eligible"] is False
    assert {reason["code"] for reason in result["admission"]["reasons"]} >= {
        "structural_invalid"
    }
    assert result["canonical"] is None


def test_structurally_valid_candidate_with_contradicted_claim_is_noncanonical():
    bad = candidate()
    bad["price"] = 2.49

    result = ingest_offer(
        source_record(),
        ai=StubAI(bad),
        validate=True,
        admission=True,
        retailer="lidl",
    )

    assert result["validated"] is True
    assert result["structural_validation"]["valid"] is True
    assert result["admission"]["eligible"] is False
    assert {
        (reason["code"], tuple(reason.get("path", [])))
        for reason in result["admission"]["reasons"]
    } >= {("contradicted_claim", ("price",))}
    assert result["canonical"] is None


def test_unsupported_critical_claim_blocks_canonical_admission():
    source = source_record()
    del source["product_name"]

    result = ingest_offer(
        source,
        ai=StubAI(candidate()),
        validate=True,
        admission=True,
        retailer="lidl",
    )

    assert result["validated"] is True
    assert result["admission"]["eligible"] is False
    assert {
        (reason["code"], tuple(reason.get("path", [])))
        for reason in result["admission"]["reasons"]
    } >= {("critical_claim_unsupported", ("product_name",))}
    assert result["canonical"] is None


def test_fully_admissible_candidate_becomes_canonical_with_noncritical_unknowns():
    result = ingest_offer(
        source_record(),
        ai=StubAI(candidate()),
        validate=True,
        admission=True,
        retailer="lidl",
    )

    assert result["validated"] is True
    assert result["structural_validation"]["valid"] is True
    assert result["admission"]["eligible"] is True
    assert result["admission"]["reasons"] == []
    assert result["canonical"] == candidate()
    assert any(
        claim["status"] == "unverifiable"
        and claim["path"] == ["provenance", "source_type"]
        for claim in result["claim_verification"]
    )


def test_admission_result_keeps_all_deterministic_layers_visible():
    result = ingest_offer(
        source_record(),
        ai=StubAI(candidate()),
        validate=True,
        admission=True,
        retailer="lidl",
    )

    assert result["candidate"] == candidate()
    assert isinstance(result["structural_validation"], dict)
    assert isinstance(result["source_evidence"], dict)
    assert isinstance(result["claim_verification"], list)
    assert isinstance(result["admission"], dict)
    assert result["source_evidence"]["retailer"] == "lidl"


def test_admission_composition_does_not_mutate_source_or_ai_candidate():
    source = source_record()
    proposed = candidate()
    before_source = copy.deepcopy(source)
    before_candidate = copy.deepcopy(proposed)

    result = ingest_offer(
        source,
        ai=StubAI(proposed),
        validate=True,
        admission=True,
        retailer="lidl",
    )

    assert source == before_source
    assert proposed == before_candidate
    assert result["candidate"] == before_candidate
