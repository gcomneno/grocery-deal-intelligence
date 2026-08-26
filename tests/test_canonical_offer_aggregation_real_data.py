import copy
import json
from pathlib import Path

import pytest

from grocery_deal_intelligence.aggregation import aggregate_offers


ROOT = Path(__file__).resolve().parent.parent

DATASETS = {
    "lidl": ROOT / "lidl/data/output/lidl-lucca-current-retailer-neutral.json",
    "esselunga": (
        ROOT
        / "esselunga/data/output/"
        "esselunga-porcari-current-retailer-neutral.json"
    ),
}

DIMENSIONS = (
    "retailer",
    "currency",
    "promotion.type",
    "promotion.requires_loyalty",
    "locality.scope",
    "verification.locality_status",
    "verification.evidence_status",
    "reference_price",
    "base_price_text",
)


def load_dataset(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("retailer", DATASETS)
@pytest.mark.parametrize("dimension", DIMENSIONS)
def test_real_dataset_aggregation_preserves_record_count(retailer, dimension):
    dataset = load_dataset(DATASETS[retailer])

    result = aggregate_offers(dataset, dimension=dimension)

    assert result["dimension"] == dimension
    assert sum(result["groups"].values()) == len(dataset)


@pytest.mark.parametrize("retailer", DATASETS)
@pytest.mark.parametrize("dimension", DIMENSIONS)
def test_real_dataset_aggregation_is_deterministic(retailer, dimension):
    dataset = load_dataset(DATASETS[retailer])

    first = aggregate_offers(dataset, dimension=dimension)
    second = aggregate_offers(dataset, dimension=dimension)

    assert first == second


@pytest.mark.parametrize("retailer", DATASETS)
@pytest.mark.parametrize("dimension", DIMENSIONS)
def test_real_dataset_source_order_does_not_affect_aggregation(
    retailer,
    dimension,
):
    dataset = load_dataset(DATASETS[retailer])

    forward = aggregate_offers(dataset, dimension=dimension)
    reverse = aggregate_offers(
        list(reversed(dataset)),
        dimension=dimension,
    )

    assert forward == reverse


@pytest.mark.parametrize("retailer", DATASETS)
@pytest.mark.parametrize("dimension", DIMENSIONS)
def test_real_dataset_aggregation_does_not_mutate_source(
    retailer,
    dimension,
):
    dataset = load_dataset(DATASETS[retailer])
    original = copy.deepcopy(dataset)

    aggregate_offers(dataset, dimension=dimension)

    assert dataset == original


@pytest.mark.parametrize("retailer", DATASETS)
def test_real_dataset_uses_same_aggregation_interface(retailer):
    dataset = load_dataset(DATASETS[retailer])

    results = {
        dimension: aggregate_offers(dataset, dimension=dimension)
        for dimension in DIMENSIONS
    }

    assert set(results) == set(DIMENSIONS)
    assert all(
        result["dimension"] == dimension
        for dimension, result in results.items()
    )
    assert all(
        sum(result["groups"].values()) == len(dataset)
        for result in results.values()
    )


@pytest.mark.parametrize("retailer", DATASETS)
def test_real_dataset_retailer_aggregation_matches_dataset_identity(retailer):
    dataset = load_dataset(DATASETS[retailer])

    result = aggregate_offers(dataset, dimension="retailer")

    assert result["groups"] == {retailer: len(dataset)}
