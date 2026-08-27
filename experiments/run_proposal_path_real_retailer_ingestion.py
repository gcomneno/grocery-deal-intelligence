from __future__ import annotations

import copy
import json
import os
from collections import Counter
from collections.abc import Mapping
from typing import Any

from giadaware_ai.backends.ollama import OllamaBackend

from experiments.run_multi_retailer_ai_ingestion import FIXTURES, load_fixture_record
from grocery_deal_intelligence.ingestion import ingest_offer_proposal_path
from grocery_deal_intelligence.proposal_adapter import GiadaWareAIProposalAdapter
from grocery_deal_intelligence.proposal_ai import ProposeOfferProposalCapability
from grocery_deal_intelligence.source_evidence import (
    CONTRADICTED,
    SUPPORTED,
    UNVERIFIABLE,
    summarize_claim_verification,
)


RUN_ENV = "GROCERY_DEAL_INTELLIGENCE_RUN_PROPOSAL_PATH_EXPERIMENT"
BASE_URL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_BASE_URL"
MODEL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_MODEL"
TIMEOUT_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_TIMEOUT"

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:1.5b-instruct"
DEFAULT_TIMEOUT = 120.0

DIRECT_CANONICAL_BASELINE = {
    "total_records": 4,
    "structurally_valid_records": 4,
    "admission_eligible_records": 4,
    "canonical_records": 4,
    "total_claims": 71,
    "supported_claims": 42,
    "contradicted_claims": 0,
    "unverifiable_claims": 29,
}


def _leaf_count(value: Any) -> int:
    if isinstance(value, Mapping):
        return sum(_leaf_count(value[key]) for key in sorted(value))
    return 1


def evaluate_fixture(
    source: dict[str, Any],
    source_identity: dict[str, Any],
    *,
    adapter: GiadaWareAIProposalAdapter,
) -> dict[str, Any]:
    source_before = copy.deepcopy(source)
    result = ingest_offer_proposal_path(
        source,
        ai=adapter,
        retailer=source_identity["retailer"],
    )

    if source != source_before:
        raise AssertionError("Proposal-path experiment mutated a source record")

    proposal = result["proposal"]
    proposal_validation = result["proposal_validation"]
    claim_verification = result["claim_verification"]
    projection = result["projection"]
    canonical_validation = result["canonical_validation"]
    canonical_claim_verification = result.get("canonical_claim_verification")
    admission = result["admission"]
    canonical = result["canonical"]

    proposal_summary = (
        summarize_claim_verification(claim_verification)
        if claim_verification is not None
        else None
    )
    canonical_summary = (
        summarize_claim_verification(canonical_claim_verification)
        if canonical_claim_verification is not None
        else None
    )

    if projection is not None and not projection["projectable"]:
        if canonical_validation is not None or admission is not None or canonical is not None:
            raise AssertionError("not_projectable must not fabricate downstream authority")

    if admission is not None and (canonical is not None) != bool(admission["eligible"]):
        raise AssertionError("canonical presence must match admission eligibility")

    return {
        "source_identity": copy.deepcopy(source_identity),
        "source_record": source_before,
        "proposal": copy.deepcopy(proposal),
        "proposal_validation": copy.deepcopy(proposal_validation),
        "proposal_leaf_claims": _leaf_count(proposal),
        "source_evidence": copy.deepcopy(result["source_evidence"]),
        "claim_verification": copy.deepcopy(claim_verification),
        "proposal_semantic_summary": copy.deepcopy(proposal_summary),
        "projection": copy.deepcopy(projection),
        "canonical_validation": copy.deepcopy(canonical_validation),
        "canonical_claim_verification": copy.deepcopy(canonical_claim_verification),
        "canonical_semantic_summary": copy.deepcopy(canonical_summary),
        "admission": copy.deepcopy(admission),
        "canonical": copy.deepcopy(canonical),
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    proposal_counts: Counter[str] = Counter()
    canonical_counts: Counter[str] = Counter()
    missing_required_counts: Counter[str] = Counter()
    rejected_status_counts: Counter[str] = Counter()

    proposal_valid = 0
    projectable = 0
    structural_valid = 0
    admission_eligible = 0
    canonical_records = 0
    proposal_total_claims = 0

    for result in results:
        if result["proposal_validation"]["valid"]:
            proposal_valid += 1
        proposal_total_claims += result["proposal_leaf_claims"]

        proposal_summary = result["proposal_semantic_summary"]
        if proposal_summary is not None:
            for status in (SUPPORTED, CONTRADICTED, UNVERIFIABLE):
                proposal_counts[status] += proposal_summary[status]

        projection = result["projection"]
        if projection is not None:
            if projection["projectable"]:
                projectable += 1
            for path in projection["missing_required_claims"]:
                missing_required_counts[".".join(path)] += 1
            for rejected in projection["rejected_claims"]:
                rejected_status_counts[rejected["status"]] += 1

        canonical_validation = result["canonical_validation"]
        if canonical_validation is not None and canonical_validation["valid"]:
            structural_valid += 1

        canonical_summary = result["canonical_semantic_summary"]
        if canonical_summary is not None:
            for status in (SUPPORTED, CONTRADICTED, UNVERIFIABLE):
                canonical_counts[status] += canonical_summary[status]

        admission = result["admission"]
        if admission is not None and admission["eligible"]:
            admission_eligible += 1
        if result["canonical"] is not None:
            canonical_records += 1

    return {
        "total_records": len(results),
        "proposal_valid_records": proposal_valid,
        "proposal_invalid_records": len(results) - proposal_valid,
        "proposal_total_claims": proposal_total_claims,
        "proposal_supported_claims": proposal_counts[SUPPORTED],
        "proposal_contradicted_claims": proposal_counts[CONTRADICTED],
        "proposal_unverifiable_claims": proposal_counts[UNVERIFIABLE],
        "projectable_records": projectable,
        "not_projectable_records": len(results) - projectable,
        "structurally_valid_projected_records": structural_valid,
        "admission_eligible_records": admission_eligible,
        "canonical_records": canonical_records,
        "canonical_supported_claims": canonical_counts[SUPPORTED],
        "canonical_contradicted_claims": canonical_counts[CONTRADICTED],
        "canonical_unverifiable_claims": canonical_counts[UNVERIFIABLE],
        "missing_required_claim_counts": dict(sorted(missing_required_counts.items())),
        "rejected_proposal_status_counts": dict(sorted(rejected_status_counts.items())),
    }


def run_experiment() -> dict[str, Any]:
    if os.environ.get(RUN_ENV) != "1":
        raise RuntimeError(f"Proposal-path real-retailer experiment is opt-in; set {RUN_ENV}=1")

    base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)
    model = os.environ.get(MODEL_ENV, DEFAULT_MODEL)
    timeout = float(os.environ.get(TIMEOUT_ENV, DEFAULT_TIMEOUT))

    backend = OllamaBackend(model=model, base_url=base_url, timeout=timeout)
    capability = ProposeOfferProposalCapability(backend)
    adapter = GiadaWareAIProposalAdapter(capability)

    results = []
    for spec in FIXTURES:
        source, identity = load_fixture_record(spec)
        results.append(evaluate_fixture(source, identity, adapter=adapter))

    return {
        "experiment": {
            "name": "fixed-real-retailer-proposal-v0.1-ingestion",
            "fixture_count": len(FIXTURES),
            "fixture_order": [
                {
                    "retailer": spec["retailer"],
                    "path": spec["path"],
                    "selector": copy.deepcopy(spec["selector"]),
                }
                for spec in FIXTURES
            ],
        },
        "fixtures": results,
        "summary": summarize_results(results),
        "comparison_baseline": copy.deepcopy(DIRECT_CANONICAL_BASELINE),
        "runtime_metadata": {
            "backend": "giadaware_ai.backends.ollama.OllamaBackend",
            "base_url": base_url,
            "model": model,
            "timeout": timeout,
        },
    }


def main() -> int:
    evidence = run_experiment()
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
