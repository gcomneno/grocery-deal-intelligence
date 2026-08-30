import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent

SCHEMA = ROOT / "schema/grocery-offer-v0.1.schema.json"

DATASETS = {
    "lidl": (ROOT / "lidl/data/output/lidl-lucca-current-retailer-neutral.json"),
    "esselunga": (
        ROOT / "esselunga/data/output/esselunga-porcari-current-retailer-neutral.json"
    ),
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_cross_retailer_contract():
    schema = load_json(SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)

    records = []

    for retailer, path in DATASETS.items():
        dataset = load_json(path)

        assert dataset, f"{retailer}: empty dataset"

        for index, record in enumerate(dataset):
            errors = list(validator.iter_errors(record))

            assert not errors, (
                f"{retailer} record {index} violates "
                f"grocery-offer-v0.1: "
                f"{errors[0].message}"
            )

            assert record["retailer"] == retailer

        records.extend(dataset)

    retailers = {record["retailer"] for record in records}

    assert retailers == {"lidl", "esselunga"}
