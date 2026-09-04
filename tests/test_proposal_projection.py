import copy

from grocery_deal_intelligence.proposal_projection import project_proposal_to_canonical
from grocery_deal_intelligence.source_evidence import (
    CONTRADICTED,
    SUPPORTED,
    UNVERIFIABLE,
)
from grocery_deal_intelligence.validation import validate_offers


def complete_evidence():
    return {
        "retailer": "lidl",
        "product_name": "Latte Fresco",
        "price": 1.49,
        "currency": "EUR",
        "promotion": {
            "type": "offer",
            "requires_loyalty": False,
        },
        "validity": {
            "from": "2026-08-27",
            "to": "2026-08-30",
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
            "source_type": "retailer",
            "source_url": "https://example.test/offer",
            "observed_at": "2026-08-27T08:00:00Z",
        },
    }


def verification(path, status, candidate_value, evidence_value=None):
    item = {
        "path": path,
        "status": status,
        "candidate_value": candidate_value,
    }
    if evidence_value is not None:
        item["evidence_value"] = evidence_value
    return item


def test_complete_evidence_with_supported_proposal_is_projectable():
    proposal = {"product_name": "Latte Fresco", "price": 1.49}
    checks = [
        verification(["price"], SUPPORTED, 1.49, 1.49),
        verification(["product_name"], SUPPORTED, "Latte Fresco", "Latte Fresco"),
    ]

    result = project_proposal_to_canonical(proposal, checks, complete_evidence())

    assert result["projectable"] is True
    assert result["candidate"] == complete_evidence()
    assert result["missing_required_claims"] == []
    assert result["rejected_claims"] == []


def test_absent_proposal_claim_can_be_supplied_by_deterministic_evidence():
    result = project_proposal_to_canonical({}, [], complete_evidence())

    assert result["projectable"] is True
    assert result["candidate"]["retailer"] == "lidl"
    assert (
        result["candidate"]["provenance"]["source_url"] == "https://example.test/offer"
    )


def test_projection_supplies_domain_eur_without_evidence_or_proposal_currency():
    evidence = complete_evidence()
    del evidence["currency"]

    result = project_proposal_to_canonical({}, [], evidence)

    assert result["projectable"] is True
    assert result["candidate"]["currency"] == "EUR"
    assert "currency" not in evidence


def test_contradicted_proposal_claim_is_rejected_and_does_not_override_evidence():
    proposal = {"price": 99.0}
    checks = [verification(["price"], CONTRADICTED, 99.0, 1.49)]

    result = project_proposal_to_canonical(proposal, checks, complete_evidence())

    assert result["projectable"] is True
    assert result["candidate"]["price"] == 1.49
    assert result["rejected_claims"] == [
        {"path": ["price"], "status": CONTRADICTED, "candidate_value": 99.0}
    ]


def test_unverifiable_proposal_claim_is_rejected_and_unusable():
    evidence = complete_evidence()
    evidence.pop("packaging_text", None)
    proposal = {"packaging_text": "1 l"}
    checks = [verification(["packaging_text"], UNVERIFIABLE, "1 l")]

    result = project_proposal_to_canonical(proposal, checks, evidence)

    assert result["projectable"] is True
    assert "packaging_text" not in result["candidate"]
    assert result["rejected_claims"] == [
        {"path": ["packaging_text"], "status": UNVERIFIABLE, "candidate_value": "1 l"}
    ]


def test_missing_required_canonical_fact_returns_not_projectable_and_null_candidate():
    evidence = complete_evidence()
    del evidence["provenance"]["observed_at"]

    result = project_proposal_to_canonical({}, [], evidence)

    assert result["projectable"] is False
    assert result["candidate"] is None
    assert ["provenance", "observed_at"] in result["missing_required_claims"]


def test_missing_required_nested_object_reports_required_leaf_paths_deterministically():
    evidence = complete_evidence()
    del evidence["validity"]

    result = project_proposal_to_canonical({}, [], evidence)

    assert result["projectable"] is False
    assert result["missing_required_claims"] == [
        ["validity", "from"],
        ["validity", "to"],
    ]


def test_missing_optional_canonical_fields_do_not_block_projection():
    evidence = complete_evidence()

    result = project_proposal_to_canonical({}, [], evidence)

    assert result["projectable"] is True
    assert "reference_price" not in result["candidate"]
    assert "packaging_text" not in result["candidate"]
    assert "base_price_text" not in result["candidate"]


def test_projection_is_read_only_and_result_is_detached():
    proposal = {"product_name": "Latte Fresco"}
    checks = [verification(["product_name"], SUPPORTED, "Latte Fresco", "Latte Fresco")]
    evidence = complete_evidence()
    proposal_before = copy.deepcopy(proposal)
    checks_before = copy.deepcopy(checks)
    evidence_before = copy.deepcopy(evidence)

    result = project_proposal_to_canonical(proposal, checks, evidence)
    result["candidate"]["promotion"]["type"] = "changed"

    assert proposal == proposal_before
    assert checks == checks_before
    assert evidence == evidence_before


def test_rejected_claims_are_sorted_by_path():
    proposal = {"product_name": "Wrong", "price": 99.0}
    checks = [
        verification(["product_name"], UNVERIFIABLE, "Wrong"),
        verification(["price"], CONTRADICTED, 99.0, 1.49),
    ]

    result = project_proposal_to_canonical(proposal, checks, complete_evidence())

    assert [item["path"] for item in result["rejected_claims"]] == [
        ["price"],
        ["product_name"],
    ]


def test_explicit_non_eur_evidence_remains_noncanonical():
    evidence = complete_evidence()
    evidence["currency"] = "USD"

    result = project_proposal_to_canonical({}, [], evidence)

    assert result["projectable"] is True
    validation = validate_offers([result["candidate"]])
    assert validation["valid"] is False


def test_explicit_non_eur_proposal_is_preserved_for_canonical_validation():
    evidence = complete_evidence()
    del evidence["currency"]
    proposal = {"currency": "USD"}
    checks = [verification(["currency"], UNVERIFIABLE, "USD")]

    result = project_proposal_to_canonical(proposal, checks, evidence)

    assert result["projectable"] is True
    assert result["candidate"]["currency"] == "USD"
    validation = validate_offers([result["candidate"]])
    assert validation["valid"] is False


def test_unknown_top_level_evidence_path_is_not_copied_into_candidate():
    evidence = complete_evidence()
    evidence["internal_debug"] = "do not project"

    result = project_proposal_to_canonical({}, [], evidence)

    assert result["projectable"] is True
    assert "internal_debug" not in result["candidate"]


def test_explicit_eur_proposal_does_not_become_currency_authority():
    evidence = complete_evidence()
    del evidence["currency"]
    proposal = {"currency": "EUR"}
    checks = [verification(["currency"], UNVERIFIABLE, "EUR")]

    result = project_proposal_to_canonical(proposal, checks, evidence)

    assert result["projectable"] is True
    assert result["candidate"]["currency"] == "EUR"
    assert "currency" not in evidence
