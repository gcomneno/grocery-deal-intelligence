import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent.parent
PROPOSAL_SCHEMA_PATH = ROOT / "schema/grocery-offer-proposal-v0.1.schema.json"


def _load_proposal_schema():
    return json.loads(PROPOSAL_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_proposal(proposal):
    """Validate Proposal v0.1 shape without mutating input or granting authority."""
    proposal_copy = deepcopy(proposal)
    validator = Draft202012Validator(_load_proposal_schema())
    errors = sorted(
        validator.iter_errors(proposal_copy),
        key=lambda error: (
            list(error.absolute_path),
            error.validator,
            error.message,
        ),
    )

    return {
        "valid": not errors,
        "errors": [
            {
                "path": list(error.absolute_path),
                "message": error.message,
            }
            for error in errors
        ],
    }
