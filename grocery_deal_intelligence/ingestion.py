from copy import deepcopy

from grocery_deal_intelligence.admission import evaluate_canonical_admission
from grocery_deal_intelligence.proposal_projection import project_proposal_to_canonical
from grocery_deal_intelligence.proposal_validation import validate_proposal
from grocery_deal_intelligence.source_evidence import (
    project_source_evidence,
    verify_candidate_claims,
)
from grocery_deal_intelligence.validation import validate_offers


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
