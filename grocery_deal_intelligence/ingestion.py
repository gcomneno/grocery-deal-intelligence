from copy import deepcopy

from grocery_deal_intelligence.admission import evaluate_canonical_admission
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

    if ai is None:
        candidate = source
        ai_used = False
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

    source_evidence = project_source_evidence(source, retailer=retailer)
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
