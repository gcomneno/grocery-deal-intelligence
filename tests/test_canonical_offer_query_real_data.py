import json
from pathlib import Path

from grocery_deal_intelligence.query import search_offers

ROOT = Path(__file__).resolve().parent.parent

DATASETS = {
    "lidl": ROOT / "lidl/data/output/lidl-lucca-current-retailer-neutral.json",
    "esselunga": (
        ROOT / "esselunga/data/output/esselunga-porcari-current-retailer-neutral.json"
    ),
}


def load_dataset(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_lidl_dataset_can_be_queried():
    dataset = load_dataset(DATASETS["lidl"])

    results = search_offers(dataset, "pollo", retailer="lidl")

    assert results
    assert all(record["retailer"] == "lidl" for record in results)
    assert all("pollo" in record["product_name"].casefold() for record in results)


def test_real_esselunga_dataset_can_be_queried():
    dataset = load_dataset(DATASETS["esselunga"])

    results = search_offers(dataset, "ananas", retailer="esselunga")

    assert results
    assert all(record["retailer"] == "esselunga" for record in results)
    assert all("ananas" in record["product_name"].casefold() for record in results)


def test_real_datasets_share_the_same_query_interface():
    datasets = {retailer: load_dataset(path) for retailer, path in DATASETS.items()}

    for retailer, dataset in datasets.items():
        results = search_offers(
            dataset,
            "latte",
            retailer=retailer,
        )

        assert all(record["retailer"] == retailer for record in results)


def test_real_query_does_not_mutate_dataset():
    dataset = load_dataset(DATASETS["lidl"])
    original = json.loads(json.dumps(dataset))

    search_offers(dataset, "pollo")

    assert dataset == original


def test_real_result_order_is_independent_of_source_order():
    dataset = load_dataset(DATASETS["esselunga"])

    forward = search_offers(dataset, "ananas")
    reverse = search_offers(list(reversed(dataset)), "ananas")

    assert forward == reverse
