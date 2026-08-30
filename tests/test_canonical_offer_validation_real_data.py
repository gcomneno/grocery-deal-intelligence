import copy
import json
from pathlib import Path

from grocery_deal_intelligence.validation import validate_offers

ROOT = Path(__file__).resolve().parent.parent

DATASETS = {
    "lidl": ROOT / "lidl/data/output/lidl-lucca-current-retailer-neutral.json",
    "esselunga": (
        ROOT / "esselunga/data/output/esselunga-porcari-current-retailer-neutral.json"
    ),
}


def load_dataset(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_lidl_dataset_is_canonically_valid():
    dataset = load_dataset(DATASETS["lidl"])

    result = validate_offers(dataset)

    assert result["valid"] is True
    assert result["total_records"] == len(dataset)
    assert result["valid_records"] == len(dataset)
    assert result["invalid_records"] == 0
    assert result["errors"] == []


def test_real_esselunga_dataset_is_canonically_valid():
    dataset = load_dataset(DATASETS["esselunga"])

    result = validate_offers(dataset)

    assert result["valid"] is True
    assert result["total_records"] == len(dataset)
    assert result["valid_records"] == len(dataset)
    assert result["invalid_records"] == 0
    assert result["errors"] == []


def test_real_retailer_datasets_share_the_same_validation_interface():
    datasets = {retailer: load_dataset(path) for retailer, path in DATASETS.items()}

    results = {
        retailer: validate_offers(dataset) for retailer, dataset in datasets.items()
    }

    assert all(result["valid"] for result in results.values())
    assert all(result["invalid_records"] == 0 for result in results.values())
    assert all(result["errors"] == [] for result in results.values())


def test_real_lidl_validation_does_not_mutate_dataset():
    dataset = load_dataset(DATASETS["lidl"])
    original = copy.deepcopy(dataset)

    validate_offers(dataset)

    assert dataset == original


def test_real_esselunga_validation_does_not_mutate_dataset():
    dataset = load_dataset(DATASETS["esselunga"])
    original = copy.deepcopy(dataset)

    validate_offers(dataset)

    assert dataset == original


def test_real_dataset_validation_is_deterministic():
    datasets = {retailer: load_dataset(path) for retailer, path in DATASETS.items()}

    for dataset in datasets.values():
        assert validate_offers(dataset) == validate_offers(dataset)
