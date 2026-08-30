import copy

from grocery_deal_intelligence.ingestion import ingest_offer


def make_source_record():
    return {
        "retailer": "lidl",
        "name": "Latte Fresco",
        "price": "1.49",
        "currency": "EUR",
    }


class StubAI:
    def __init__(self, candidate):
        self.candidate = candidate
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


def test_ingestion_can_produce_candidate_without_ai():
    source = make_source_record()

    result = ingest_offer(source)

    assert result["candidate"] is not None
    assert result["ai_used"] is False
    assert result["validated"] is False


def test_ai_is_optional_and_read_only():
    source = make_source_record()
    candidate = make_candidate()
    ai = StubAI(candidate)

    before = copy.deepcopy(source)

    result = ingest_offer(source, ai=ai)

    assert result["candidate"] == candidate
    assert result["ai_used"] is True
    assert result["validated"] is False
    assert source == before
    assert ai.calls == [before]


def test_ai_output_is_not_canonical_without_validation():
    source = make_source_record()

    invalid_candidate = make_candidate()
    invalid_candidate["price"] = "not-a-number"

    ai = StubAI(invalid_candidate)

    result = ingest_offer(source, ai=ai)

    assert result["candidate"] == invalid_candidate
    assert result["validated"] is False
    assert result["canonical"] is None


def test_ai_output_is_never_authoritative():
    source = make_source_record()
    candidate = make_candidate()

    class LyingAI:
        def propose(self, source_record):
            return copy.deepcopy(candidate)

    result = ingest_offer(source, ai=LyingAI())

    assert result["candidate"] == candidate
    assert result["validated"] is False
    assert result["canonical"] is None


def test_valid_candidate_becomes_canonical_only_after_validation():
    source = make_source_record()
    candidate = make_candidate()
    ai = StubAI(candidate)

    result = ingest_offer(source, ai=ai, validate=True)

    assert result["candidate"] == candidate
    assert result["ai_used"] is True
    assert result["validated"] is True
    assert result["canonical"] == candidate


def test_invalid_candidate_is_rejected_by_validation_gate():
    source = make_source_record()

    invalid_candidate = make_candidate()
    invalid_candidate["price"] = "not-a-number"

    ai = StubAI(invalid_candidate)

    result = ingest_offer(source, ai=ai, validate=True)

    assert result["candidate"] == invalid_candidate
    assert result["validated"] is False
    assert result["canonical"] is None


def test_validation_is_performed_by_deterministic_validator():
    source = make_source_record()
    candidate = make_candidate()
    ai = StubAI(candidate)

    result = ingest_offer(source, ai=ai, validate=True)

    assert result["validated"] is True
    assert result["canonical"] is not None


def test_validation_does_not_mutate_candidate():
    source = make_source_record()
    candidate = make_candidate()
    ai = StubAI(candidate)

    before = copy.deepcopy(candidate)

    result = ingest_offer(source, ai=ai, validate=True)

    assert candidate == before
    assert result["candidate"] == before
    assert result["canonical"] == before


def test_source_remains_unchanged_through_validated_ingestion():
    source = make_source_record()
    before = copy.deepcopy(source)

    result = ingest_offer(
        source,
        ai=StubAI(make_candidate()),
        validate=True,
    )

    assert source == before
    assert result["validated"] is True


def test_validation_is_opt_in_but_canonical_promotion_is_not():
    source = make_source_record()
    candidate = make_candidate()

    result = ingest_offer(source, ai=StubAI(candidate))

    assert result["candidate"] == candidate
    assert result["validated"] is False
    assert result["canonical"] is None
