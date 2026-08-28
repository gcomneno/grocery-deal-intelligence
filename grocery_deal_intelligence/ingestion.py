from collections import Counter
from copy import deepcopy

from grocery_deal_intelligence.admission import evaluate_canonical_admission
from grocery_deal_intelligence.proposal_projection import project_proposal_to_canonical
from grocery_deal_intelligence.proposal_validation import validate_proposal
from grocery_deal_intelligence.source_evidence import (
    CONTRADICTED,
    SUPPORTED,
    UNVERIFIABLE,
    project_source_evidence,
    summarize_claim_verification,
    verify_candidate_claims,
)
from grocery_deal_intelligence.validation import validate_offers


_DETERMINISTIC_CANDIDATE_FIELDS = (
    "retailer",
    "product_name",
    "price",
    "currency",
    "reference_price",
    "packaging_text",
    "base_price_text",
    "promotion",
    "validity",
    "locality",
    "verification",
    "provenance",
)


def _candidate_from_source_evidence(source_evidence):
    candidate = {}
    for key in _DETERMINISTIC_CANDIDATE_FIELDS:
        if key in source_evidence:
            candidate[key] = deepcopy(source_evidence[key])
    return candidate


def ingest_deterministic_source_record(source_record, *, retailer):
    """Ingest one deterministic retailer source record through canonical admission.

    This path is AI-free. It projects deterministic source evidence, constructs a
    candidate only from evidence fields, verifies every candidate claim, runs
    canonical structural validation, and applies canonical admission without
    collapsing the intermediate authority layers.
    """
    if not isinstance(retailer, str) or not retailer.strip():
        raise ValueError("deterministic source ingestion requires a non-empty retailer")

    source = deepcopy(source_record)
    source_evidence = project_source_evidence(source, retailer=retailer)
    candidate = _candidate_from_source_evidence(source_evidence)

    claim_verification = verify_candidate_claims(candidate, source_evidence)
    structural_validation = validate_offers([candidate])
    structurally_valid = bool(structural_validation["valid"])
    admission_decision = evaluate_canonical_admission(
        structurally_valid=structurally_valid,
        claim_verification=claim_verification,
    )

    return {
        "candidate": deepcopy(candidate),
        "ai_used": False,
        "validated": structurally_valid,
        "structural_validation": deepcopy(structural_validation),
        "source_evidence": deepcopy(source_evidence),
        "claim_verification": deepcopy(claim_verification),
        "admission": deepcopy(admission_decision),
        "canonical": deepcopy(candidate) if admission_decision["eligible"] else None,
    }


def ingest_deterministic_source_records(source_records, *, retailer):
    """Ingest deterministic retailer source records without adding authority.

    The batch layer preserves order and delegates every record to
    ``ingest_deterministic_source_record``. It aggregates observable outcomes but
    never repairs, completes, drops, or cross-pollinates record evidence.
    """
    if not isinstance(retailer, str) or not retailer.strip():
        raise ValueError("deterministic source ingestion requires a non-empty retailer")

    results = []
    claim_totals = Counter({SUPPORTED: 0, CONTRADICTED: 0, UNVERIFIABLE: 0})
    rejection_reasons = Counter()
    structurally_valid = 0
    admission_eligible = 0
    canonical_records = 0

    for source_record in source_records:
        result = ingest_deterministic_source_record(
            source_record,
            retailer=retailer,
        )
        results.append(deepcopy(result))

        structurally_valid += int(result["validated"] is True)
        admission_eligible += int(result["admission"]["eligible"] is True)
        canonical_records += int(result["canonical"] is not None)
        claim_totals.update(
            summarize_claim_verification(result["claim_verification"])
        )
        rejection_reasons.update(
            reason["code"] for reason in result["admission"]["reasons"]
        )

    total_records = len(results)
    return {
        "retailer": retailer,
        "records": results,
        "summary": {
            "total_records": total_records,
            "structurally_valid": structurally_valid,
            "structurally_invalid": total_records - structurally_valid,
            "admission_eligible": admission_eligible,
            "admission_ineligible": total_records - admission_eligible,
            "canonical_records": canonical_records,
            "claims": {
                SUPPORTED: claim_totals[SUPPORTED],
                CONTRADICTED: claim_totals[CONTRADICTED],
                UNVERIFIABLE: claim_totals[UNVERIFIABLE],
            },
            "rejection_reasons": dict(sorted(rejection_reasons.items())),
        },
        "ai_used": False,
        "network_required": False,
    }


def ingest_offer(
    source_record,
    *,
    ai=None,
    validate=False,
    admission=False,
    retailer=None,
):
    """
    Produce candidate canonical data from one source record.

    AI assistance is optional and advisory only.

    When validation is requested, the candidate must pass the deterministic
    canonical validation layer before it can become canonical data under the
    legacy structural-only path.

    Canonical admission is a separate explicit opt-in path. It composes
    structural validation, deterministic source-evidence verification, and the
    canonical admission policy while keeping all three results visible.
    """
    if admission and not validate:
        raise ValueError("admission requires validate=True")
    if admission and (not isinstance(retailer, str) or not retailer.strip()):
        raise ValueError("admission requires a non-empty retailer")

    source = deepcopy(source_record)
    source_evidence = (
        project_source_evidence(source, retailer=retailer)
        if admission
        else None
    )

    if ai is None:
        candidate = source
        ai_used = False
    else:
        if admission and hasattr(ai, "propose_grounded"):
            candidate = ai.propose_grounded(
                deepcopy(source),
                source_evidence=deepcopy(source_evidence),
            )
        else:
            candidate = ai.propose(deepcopy(source))
        ai_used = True

    candidate = deepcopy(candidate)

    if not validate:
        return {
            "candidate": candidate,
            "ai_used": ai_used,
            "validated": False,
            "canonical": None,
        }

    validation = validate_offers([candidate])
    structurally_valid = bool(validation["valid"])

    if not admission:
        if structurally_valid:
            return {
                "candidate": candidate,
                "ai_used": ai_used,
                "validated": True,
                "canonical": deepcopy(candidate),
            }

        return {
            "candidate": candidate,
            "ai_used": ai_used,
            "validated": False,
            "canonical": None,
        }

    claim_verification = verify_candidate_claims(candidate, source_evidence)
    admission_decision = evaluate_canonical_admission(
        structurally_valid=structurally_valid,
        claim_verification=claim_verification,
    )

    return {
        "candidate": candidate,
        "ai_used": ai_used,
        "validated": structurally_valid,
        "structural_validation": deepcopy(validation),
        "source_evidence": deepcopy(source_evidence),
        "claim_verification": deepcopy(claim_verification),
        "admission": deepcopy(admission_decision),
        "canonical": deepcopy(candidate) if admission_decision["eligible"] else None,
    }


def ingest_offer_proposal_path(
    source_record,
    *,
    ai,
    retailer,
):
    """Run the explicit Proposal v0.1 ingestion path without collapsing authority layers.

    The Proposal path is opt-in and independent from ``ingest_offer``. It keeps
    proposal shape, source support, projection completeness, canonical structural
    validation, and canonical admission as separate deterministic results.
    """
    if ai is None:
        raise ValueError("proposal path requires an AI proposal adapter")
    if not isinstance(retailer, str) or not retailer.strip():
        raise ValueError("proposal path requires a non-empty retailer")

    source = deepcopy(source_record)
    source_evidence = project_source_evidence(source, retailer=retailer)

    if hasattr(ai, "propose_grounded"):
        proposal = ai.propose_grounded(
            deepcopy(source),
            source_evidence=deepcopy(source_evidence),
        )
    else:
        proposal = ai.propose(deepcopy(source))
    proposal = deepcopy(proposal)

    proposal_validation = validate_proposal(proposal)
    result = {
        "proposal": deepcopy(proposal),
        "proposal_validation": deepcopy(proposal_validation),
        "source_evidence": deepcopy(source_evidence),
        "claim_verification": None,
        "projection": None,
        "canonical_validation": None,
        "canonical_claim_verification": None,
        "admission": None,
        "canonical": None,
    }

    if not proposal_validation["valid"]:
        return result

    claim_verification = verify_candidate_claims(proposal, source_evidence)
    result["claim_verification"] = deepcopy(claim_verification)

    projection = project_proposal_to_canonical(
        proposal,
        claim_verification,
        source_evidence,
    )
    result["projection"] = deepcopy(projection)

    if not projection["projectable"]:
        return result

    candidate = deepcopy(projection["candidate"])
    canonical_validation = validate_offers([candidate])
    result["canonical_validation"] = deepcopy(canonical_validation)

    canonical_claim_verification = verify_candidate_claims(
        candidate,
        source_evidence,
    )
    result["canonical_claim_verification"] = deepcopy(canonical_claim_verification)

    admission_decision = evaluate_canonical_admission(
        structurally_valid=bool(canonical_validation["valid"]),
        claim_verification=canonical_claim_verification,
    )
    result["admission"] = deepcopy(admission_decision)

    if canonical_validation["valid"] and admission_decision["eligible"]:
        result["canonical"] = deepcopy(candidate)

    return result
