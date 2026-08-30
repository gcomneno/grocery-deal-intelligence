import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent

SCHEMA = ROOT / "schema/grocery-offer-v0.1.schema.json"
DATASET = ROOT / "lidl/data/output/lidl-lucca-current-retailer-neutral.json"


def main() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    dataset = Path(sys.argv[1]) if len(sys.argv) > 1 else DATASET

    records = json.loads(dataset.read_text(encoding="utf-8"))

    validator = jsonschema.Draft202012Validator(schema)

    errors = []

    for index, record in enumerate(records):
        errors.extend((index, error) for error in validator.iter_errors(record))

    print("===== RETAILER-NEUTRAL VALIDATION =====")
    print("records:", len(records))
    print("errors:", len(errors))

    if errors:
        for index, error in errors[:20]:
            path = ".".join(str(part) for part in error.absolute_path) or "<root>"

            print(f"FAIL record={index} path={path}: {error.message}")

        sys.exit(1)

    print("validate_retailer_neutral: PASS")


if __name__ == "__main__":
    main()
