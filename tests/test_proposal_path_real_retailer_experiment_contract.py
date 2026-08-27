import pytest

from experiments import run_proposal_path_real_retailer_ingestion as experiment


def test_leaf_count_counts_only_emitted_proposal_claims():
    proposal = {
        "product_name": "Latte",
        "validity": {"from": "2026-08-27", "to": "2026-08-30"},
    }

    assert experiment._leaf_count(proposal) == 3
    assert experiment._leaf_count({}) == 0


def test_summary_distinguishes_proposal_projection_and_canonical_authority():
    results = [
        {
            "proposal_validation": {"valid": True},
            "proposal_leaf_claims": 2,
            "proposal_semantic_summary": {
                "supported": 1,
                "contradicted": 0,
                "unverifiable": 1,
            },
            "projection": {
                "projectable": False,
                "missing_required_claims": [["provenance", "observed_at"]],
                "rejected_claims": [
                    {"path": ["packaging_text"], "status": "unverifiable"}
                ],
            },
            "canonical_validation": None,
            "canonical_semantic_summary": None,
            "admission": None,
            "canonical": None,
        },
        {
            "proposal_validation": {"valid": True},
            "proposal_leaf_claims": 3,
            "proposal_semantic_summary": {
                "supported": 3,
                "contradicted": 0,
                "unverifiable": 0,
            },
            "projection": {
                "projectable": True,
                "missing_required_claims": [],
                "rejected_claims": [],
            },
            "canonical_validation": {"valid": True},
            "canonical_semantic_summary": {
                "supported": 10,
                "contradicted": 0,
                "unverifiable": 2,
            },
            "admission": {"eligible": True},
            "canonical": {"retailer": "lidl"},
        },
    ]

    summary = experiment.summarize_results(results)

    assert summary["total_records"] == 2
    assert summary["proposal_valid_records"] == 2
    assert summary["proposal_total_claims"] == 5
    assert summary["proposal_supported_claims"] == 4
    assert summary["proposal_unverifiable_claims"] == 1
    assert summary["projectable_records"] == 1
    assert summary["not_projectable_records"] == 1
    assert summary["structurally_valid_projected_records"] == 1
    assert summary["admission_eligible_records"] == 1
    assert summary["canonical_records"] == 1
    assert summary["missing_required_claim_counts"] == {
        "provenance.observed_at": 1
    }
    assert summary["rejected_proposal_status_counts"] == {"unverifiable": 1}


def test_experiment_is_explicitly_opt_in(monkeypatch):
    monkeypatch.delenv(experiment.RUN_ENV, raising=False)

    with pytest.raises(RuntimeError, match="opt-in"):
        experiment.run_experiment()


def test_direct_canonical_baseline_is_pinned_to_measured_issue_42_evidence():
    assert experiment.DIRECT_CANONICAL_BASELINE == {
        "total_records": 4,
        "structurally_valid_records": 4,
        "admission_eligible_records": 4,
        "canonical_records": 4,
        "total_claims": 71,
        "supported_claims": 42,
        "contradicted_claims": 0,
        "unverifiable_claims": 29,
    }
