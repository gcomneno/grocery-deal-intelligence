from copy import deepcopy

from grocery_deal_intelligence.validation import validate_offers


def ingest_offer(source_record, *, ai=None, validate=False):
    """
    Produce candidate canonical data from one source record.

    AI assistance is optional and advisory only.

    When validation is requested, the candidate must pass the deterministic
    canonical validation layer before it can become canonical data.
    """
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

    if validation["valid"]:
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
