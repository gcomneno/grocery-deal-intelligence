import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema/grocery-offer-v0.1.schema.json"


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _error_path(error: ValidationError):
    return list(error.absolute_path)


def validate_offers(records: Sequence[object]) -> dict[str, Any]:
    validator = Draft202012Validator(_load_schema())

    errors = []
    valid_records = 0

    for record_index, record in enumerate(records):
        record_errors = sorted(
            validator.iter_errors(record),
            key=lambda error: (
                list(error.absolute_path),
                error.validator,
                error.message,
            ),
        )

        if record_errors:
            errors.extend(
                {
                    "record_index": record_index,
                    "path": _error_path(error),
                    "message": error.message,
                }
                for error in record_errors
            )
        else:
            valid_records += 1

    invalid_records = len(records) - valid_records

    return {
        "valid": invalid_records == 0,
        "total_records": len(records),
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "errors": errors,
    }
