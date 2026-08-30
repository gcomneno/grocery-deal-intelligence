import json
from pathlib import Path

from grocery_deal_intelligence.filtering import filter_offers

ROOT = Path(__file__).resolve().parent.parent

DATASETS = {
    "lidl": ROOT / "lidl/data/output/lidl-lucca-current-retailer-neutral.json",
    "esselunga": (
        ROOT / "esselunga/data/output/esselunga-porcari-current-retailer-neutral.json"
    ),
}


def load_dataset(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_lidl_dataset_supports_canonical_filters():
    dataset = load_dataset(DATASETS["lidl"])

    results = filter_offers(
        dataset,
        retailer="lidl",
        locality_status="verified",
    )

    assert results
    assert all(record["retailer"] == "lidl" for record in results)
    assert all(
        record["verification"]["locality_status"] == "verified" for record in results
    )


def test_real_esselunga_dataset_supports_canonical_filters():
    dataset = load_dataset(DATASETS["esselunga"])

    results = filter_offers(
        dataset,
        retailer="esselunga",
        evidence_status="verified",
    )

    assert results
    assert all(record["retailer"] == "esselunga" for record in results)
    assert all(
        record["verification"]["evidence_status"] == "verified" for record in results
    )


def test_real_datasets_share_the_same_filter_interface():
    datasets = {retailer: load_dataset(path) for retailer, path in DATASETS.items()}

    for retailer, dataset in datasets.items():
        results = filter_offers(dataset, retailer=retailer)

        assert results
        assert all(record["retailer"] == retailer for record in results)


def test_real_filtering_does_not_mutate_dataset():
    for path in DATASETS.values():
        dataset = load_dataset(path)
        original = json.loads(json.dumps(dataset))

        filter_offers(
            dataset,
            locality_status="verified",
        )

        assert dataset == original


def test_real_filtering_is_independent_of_source_order():
    for path in DATASETS.values():
        dataset = load_dataset(path)

        forward = filter_offers(
            dataset,
            locality_status="verified",
        )
        reverse = filter_offers(
            list(reversed(dataset)),
            locality_status="verified",
        )

        assert forward == reverse


def test_real_filtering_can_select_loyalty_offers():
    for path in DATASETS.values():
        dataset = load_dataset(path)

        results = filter_offers(
            dataset,
            requires_loyalty=True,
        )

        assert all(
            record["promotion"]["requires_loyalty"] is True for record in results
        )


def test_real_filtering_supports_conjunctive_selection():
    for path in DATASETS.values():
        dataset = load_dataset(path)

        results = filter_offers(
            dataset,
            locality_status="verified",
            evidence_status="verified",
            requires_loyalty=True,
        )

        assert all(
            record["verification"]["locality_status"] == "verified"
            and record["verification"]["evidence_status"] == "verified"
            and record["promotion"]["requires_loyalty"] is True
            for record in results
        )
